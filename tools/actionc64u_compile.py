#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Iterable

OPCODE_CALLN = 0x49
OPCODE_SETP16 = 0x61
INTR_PRINT = 0xFF00
INTR_PRINTE = 0xFF10
INTR_EXIT = 0xFF20

TYPE_BYTE = "BYTE"
TYPE_CARD = "CARD"
TYPE_INT = "INT"
ASSIGNABLE_TYPES = {TYPE_BYTE, TYPE_CARD, TYPE_INT}
TOKEN_RE = re.compile(
    r"\s*(?:(?P<hex>\$[0-9A-Fa-f]+)|(?P<number>\d+)|(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|"
    r"(?P<op><>|<=|>=|[()+\-*/=<>]))"
)


class CompileError(Exception):
    pass


@dataclass(frozen=True)
class TypedValue:
    type_name: str
    value: int


@dataclass(frozen=True)
class PrintAction:
    text: str
    newline: bool


@dataclass(frozen=True)
class Decl:
    line: int
    type_name: str
    names: list[str]


@dataclass(frozen=True)
class AssignStmt:
    line: int
    name: str
    expr: "Expr"


@dataclass(frozen=True)
class PrintStmt:
    line: int
    kind: str
    value: str


@dataclass(frozen=True)
class PrintIntStmt:
    line: int
    kind: str
    expr: "Expr"


@dataclass(frozen=True)
class IfStmt:
    line: int
    condition: "Expr"
    body: list["Stmt"]


Stmt = AssignStmt | PrintStmt | PrintIntStmt | IfStmt


@dataclass(frozen=True)
class NumberExpr:
    value: int
    line: int


@dataclass(frozen=True)
class VarExpr:
    name: str
    line: int


@dataclass(frozen=True)
class UnaryExpr:
    op: str
    operand: "Expr"
    line: int


@dataclass(frozen=True)
class BinaryExpr:
    op: str
    left: "Expr"
    right: "Expr"
    line: int


Expr = NumberExpr | VarExpr | UnaryExpr | BinaryExpr


@dataclass(frozen=True)
class Program:
    module_name: str | None
    decls: list[Decl]
    statements: list[Stmt]


@dataclass
class VarInfo:
    type_name: str
    value: int | None = None


def fail(line: int, message: str) -> CompileError:
    return CompileError(f"line {line}: {message}")


def preprocess(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if line:
            lines.append((lineno, line))
    return lines


class ExprParser:
    def __init__(self, text: str, line: int):
        self.line = line
        self.tokens = self.tokenize(text)
        self.index = 0

    def tokenize(self, text: str) -> list[str]:
        tokens: list[str] = []
        pos = 0
        while pos < len(text):
            match = TOKEN_RE.match(text, pos)
            if not match:
                raise fail(self.line, f"invalid token near: {text[pos:]}")
            token = match.group(match.lastgroup or 0)
            tokens.append(token)
            pos = match.end()
        return tokens

    def peek(self) -> str | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise fail(self.line, "unexpected end of expression")
        self.index += 1
        return token

    def parse(self) -> Expr:
        expr = self.parse_comparison()
        if self.peek() is not None:
            raise fail(self.line, f"unexpected token: {self.peek()}")
        return expr

    def parse_comparison(self) -> Expr:
        expr = self.parse_addsub()
        token = self.peek()
        if token in {"=", "<>", "<", "<=", ">", ">="}:
            self.take()
            rhs = self.parse_addsub()
            expr = BinaryExpr(token, expr, rhs, self.line)
        return expr

    def parse_addsub(self) -> Expr:
        expr = self.parse_muldiv()
        while self.peek() in {"+", "-"}:
            op = self.take()
            rhs = self.parse_muldiv()
            expr = BinaryExpr(op, expr, rhs, self.line)
        return expr

    def parse_muldiv(self) -> Expr:
        expr = self.parse_unary()
        while self.peek() in {"*", "/"}:
            op = self.take()
            rhs = self.parse_unary()
            expr = BinaryExpr(op, expr, rhs, self.line)
        return expr

    def parse_unary(self) -> Expr:
        token = self.peek()
        if token == "-":
            self.take()
            return UnaryExpr("-", self.parse_unary(), self.line)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        token = self.take()
        if token == "(":
            expr = self.parse_comparison()
            if self.take() != ")":
                raise fail(self.line, "expected ')' in expression")
            return expr
        if token.startswith("$"):
            return NumberExpr(int(token[1:], 16), self.line)
        if token.isdigit():
            return NumberExpr(int(token, 10), self.line)
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
            return VarExpr(token, self.line)
        raise fail(self.line, f"unexpected token in expression: {token}")


def parse_expression(text: str, line: int) -> Expr:
    return ExprParser(text, line).parse()


def parse_decl(line_no: int, text: str) -> Decl:
    type_name, rest = text.split(None, 1)
    names = [name.strip() for name in rest.split(",") if name.strip()]
    if not names:
        raise fail(line_no, f"expected variable names after {type_name}")
    for name in names:
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            raise fail(line_no, f"invalid identifier: {name}")
    return Decl(line_no, type_name.upper(), names)


def parse_string_stmt(line_no: int, text: str, kind: str) -> PrintStmt:
    inner = text[text.find("(") + 1 : -1].strip()
    try:
        value = ast.literal_eval(inner)
    except (SyntaxError, ValueError) as exc:
        raise fail(line_no, f"invalid string literal: {inner}") from exc
    if not isinstance(value, str):
        raise fail(line_no, f"expected string literal in {kind}")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise fail(line_no, f"{kind} only supports ASCII string literals") from exc
    return PrintStmt(line_no, kind, value)


def parse_int_stmt(line_no: int, text: str, kind: str) -> PrintIntStmt:
    inner = text[text.find("(") + 1 : -1].strip()
    return PrintIntStmt(line_no, kind, parse_expression(inner, line_no))


def parse_statement(line_no: int, text: str, lines: list[tuple[int, str]], index: int) -> tuple[Stmt, int]:
    upper = text.upper()
    if upper.startswith("PRINT(") and text.endswith(")"):
        return parse_string_stmt(line_no, text, "Print"), index + 1
    if upper.startswith("PRINTE(") and text.endswith(")"):
        return parse_string_stmt(line_no, text, "PrintE"), index + 1
    if upper.startswith("PRINTI(") and text.endswith(")"):
        return parse_int_stmt(line_no, text, "PrintI"), index + 1
    if upper.startswith("PRINTIE(") and text.endswith(")"):
        return parse_int_stmt(line_no, text, "PrintIE"), index + 1
    if upper.startswith("IF "):
        condition_text = text[3:].strip()
        if condition_text.upper().endswith(" THEN"):
            condition_text = condition_text[:-5].strip()
        body, next_index = parse_block(lines, index + 1, {"FI"})
        if next_index >= len(lines) or lines[next_index][1].upper() != "FI":
            raise fail(line_no, "IF without matching FI")
        return IfStmt(line_no, parse_expression(condition_text, line_no), body), next_index + 1
    if "=" in text:
        name, expr_text = text.split("=", 1)
        name = name.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            raise fail(line_no, f"invalid assignment target: {name}")
        return AssignStmt(line_no, name, parse_expression(expr_text.strip(), line_no)), index + 1
    raise fail(line_no, f"unsupported statement: {text}")


def parse_block(lines: list[tuple[int, str]], index: int, terminators: set[str]) -> tuple[list[Stmt], int]:
    statements: list[Stmt] = []
    while index < len(lines):
        line_no, text = lines[index]
        if text.upper() in terminators:
            break
        statement, index = parse_statement(line_no, text, lines, index)
        statements.append(statement)
    return statements, index


def parse_program(text: str) -> Program:
    lines = preprocess(text)
    index = 0
    module_name: str | None = None

    if index < len(lines) and lines[index][1].upper().startswith("MODULE "):
        module_name = lines[index][1].split(None, 1)[1].strip()
        index += 1

    if index >= len(lines) or lines[index][1].upper() != "PROC MAIN()":
        line_no = lines[index][0] if index < len(lines) else 1
        raise fail(line_no, "expected 'PROC main()'")
    index += 1

    decls: list[Decl] = []
    while index < len(lines):
        line_no, text = lines[index]
        head = text.split(None, 1)[0].upper()
        if head in ASSIGNABLE_TYPES:
            decls.append(parse_decl(line_no, text))
            index += 1
            continue
        break

    statements, index = parse_block(lines, index, {"RETURN"})
    if index >= len(lines) or lines[index][1].upper() != "RETURN":
        line_no = lines[index][0] if index < len(lines) else 1
        raise fail(line_no, "expected RETURN")
    index += 1
    if index != len(lines):
        raise fail(lines[index][0], f"unexpected trailing input: {lines[index][1]}")

    return Program(module_name, decls, statements)


def signed_compare(value: TypedValue) -> int:
    return value.value if value.type_name == TYPE_INT else value.value


def arithmetic_type(left: str, right: str) -> str:
    return TYPE_INT if TYPE_INT in {left, right} else TYPE_CARD


def ensure_unsigned(value: int, line: int, op: str) -> None:
    if value < 0:
        raise fail(line, f"unsigned result became negative during '{op}'")


def eval_expr(expr: Expr, symbols: dict[str, VarInfo], line_hint: int) -> TypedValue:
    if isinstance(expr, NumberExpr):
        return TypedValue(TYPE_CARD, expr.value)
    if isinstance(expr, VarExpr):
        info = symbols.get(expr.name)
        if info is None:
            raise fail(line_hint, f"unknown variable '{expr.name}'")
        if info.value is None:
            raise fail(line_hint, f"variable '{expr.name}' used before assignment")
        return TypedValue(info.type_name, info.value)
    if isinstance(expr, UnaryExpr):
        operand = eval_expr(expr.operand, symbols, line_hint)
        value = -operand.value
        result_type = TYPE_INT if operand.type_name == TYPE_INT else TYPE_INT
        return TypedValue(result_type, value)
    if isinstance(expr, BinaryExpr):
        left = eval_expr(expr.left, symbols, line_hint)
        right = eval_expr(expr.right, symbols, line_hint)
        op = expr.op
        if op in {"+", "-", "*", "/"}:
            if op == "+":
                value = left.value + right.value
            elif op == "-":
                value = left.value - right.value
            elif op == "*":
                value = left.value * right.value
            else:
                if right.value == 0:
                    raise fail(line_hint, "division by zero")
                result_type = arithmetic_type(left.type_name, right.type_name)
                if result_type == TYPE_INT:
                    value = int(left.value / right.value)
                else:
                    value = left.value // right.value
            if op == "-":
                result_type = TYPE_INT if TYPE_INT in {left.type_name, right.type_name} or value < 0 else TYPE_CARD
            else:
                result_type = arithmetic_type(left.type_name, right.type_name)
            if result_type != TYPE_INT:
                ensure_unsigned(value, line_hint, op)
            return TypedValue(result_type, value)

        signed = TYPE_INT in {left.type_name, right.type_name}
        lhs = signed_compare(left) if signed else left.value
        rhs = signed_compare(right) if signed else right.value
        if op == "=":
            result = lhs == rhs
        elif op == "<>":
            result = lhs != rhs
        elif op == "<":
            result = lhs < rhs
        elif op == "<=":
            result = lhs <= rhs
        elif op == ">":
            result = lhs > rhs
        elif op == ">=":
            result = lhs >= rhs
        else:
            raise fail(line_hint, f"unsupported operator '{op}'")
        return TypedValue(TYPE_CARD, 1 if result else 0)
    raise fail(line_hint, "unsupported expression")


def coerce_to_type(target_type: str, value: TypedValue, line: int) -> int:
    raw = value.value
    if target_type == TYPE_BYTE:
        if not 0 <= raw <= 0xFF:
            raise fail(line, f"value {raw} does not fit in BYTE")
        return raw
    if target_type == TYPE_CARD:
        if not 0 <= raw <= 0xFFFF:
            raise fail(line, f"value {raw} does not fit in CARD")
        return raw
    if target_type == TYPE_INT:
        if not -0x8000 <= raw <= 0x7FFF:
            raise fail(line, f"value {raw} does not fit in INT")
        return raw
    raise fail(line, f"unsupported target type {target_type}")


def format_integer(value: TypedValue) -> str:
    if value.type_name == TYPE_INT:
        return str(value.value)
    return str(value.value)


def execute_program(program: Program) -> list[PrintAction]:
    symbols: dict[str, VarInfo] = {}
    for decl in program.decls:
        for name in decl.names:
            if name in symbols:
                raise fail(decl.line, f"duplicate declaration for '{name}'")
            symbols[name] = VarInfo(decl.type_name)

    actions: list[PrintAction] = []

    def exec_block(statements: list[Stmt]) -> None:
        for stmt in statements:
            if isinstance(stmt, AssignStmt):
                info = symbols.get(stmt.name)
                if info is None:
                    raise fail(stmt.line, f"unknown variable '{stmt.name}'")
                value = eval_expr(stmt.expr, symbols, stmt.line)
                info.value = coerce_to_type(info.type_name, value, stmt.line)
                continue
            if isinstance(stmt, PrintStmt):
                actions.append(PrintAction(stmt.value, stmt.kind == "PrintE"))
                continue
            if isinstance(stmt, PrintIntStmt):
                value = eval_expr(stmt.expr, symbols, stmt.line)
                actions.append(PrintAction(format_integer(value), stmt.kind == "PrintIE"))
                continue
            if isinstance(stmt, IfStmt):
                cond = eval_expr(stmt.condition, symbols, stmt.line)
                if cond.value != 0:
                    exec_block(stmt.body)
                continue
            raise fail(stmt.line, "unsupported statement kind")

    exec_block(program.statements)
    return actions


def encode_u16(value: int) -> bytes:
    return bytes((value & 0xFF, (value >> 8) & 0xFF))


def emit_payload(actions: Iterable[PrintAction]) -> bytes:
    code = bytearray()
    strings = bytearray()
    pending_offsets: list[tuple[int, int]] = []

    for action in actions:
        code.append(OPCODE_SETP16)
        patch_index = len(code)
        code.extend(b"\x00\x00")
        pending_offsets.append((patch_index, len(strings)))

        code.append(OPCODE_CALLN)
        code.extend(encode_u16(INTR_PRINTE if action.newline else INTR_PRINT))

        strings.extend(action.text.encode("ascii"))
        strings.append(0)

    code.append(OPCODE_CALLN)
    code.extend(encode_u16(INTR_EXIT))

    string_base = len(code)
    for patch_index, string_offset in pending_offsets:
        code[patch_index : patch_index + 2] = encode_u16(string_base + string_offset)

    code.extend(strings)
    return bytes(code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile a minimal Action-like source file into ActionC64U .avm")
    parser.add_argument("input", help="input .act file")
    parser.add_argument("-o", "--output", required=True, help="output .avm file")
    parser.add_argument("--entry-offset", type=int, default=0, help="entry offset for the generated payload")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_file():
        parser.error(f"input file not found: {input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        source_text = input_path.read_text(encoding="ascii")
        program = parse_program(source_text)
        actions = execute_program(program)
        payload = emit_payload(actions)
    except (CompileError, UnicodeDecodeError, UnicodeEncodeError) as exc:
        print(exc, file=sys.stderr)
        return 1

    avm_pack = Path(__file__).resolve().with_name("avm_pack.py")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".payload",
        prefix=f"{output_path.stem}-",
        dir=output_path.parent,
        delete=False,
    ) as handle:
        handle.write(payload)
        payload_path = Path(handle.name)

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(avm_pack),
                str(payload_path),
                "--entry-offset",
                str(args.entry_offset),
                "--output",
                str(output_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        payload_path.unlink(missing_ok=True)

    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode

    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
