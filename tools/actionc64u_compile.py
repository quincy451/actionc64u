#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
from typing import Iterable

from avo_format import AvoObject, AvoFormatError, OverlayObject, write_avo

OPCODE_CALLN = 0x49
OPCODE_SETP16 = 0x61
INTR_PRINT = 0xFF00
INTR_PRINTE = 0xFF10
INTR_EXIT = 0xFF20
RUNTIME_PRINT = "rt.print_str"
RUNTIME_PRINT_LINE = "rt.print_line"
RUNTIME_FORMAT_INT = "rt.format_int"

TYPE_BYTE = "BYTE"
TYPE_CARD = "CARD"
TYPE_INT = "INT"
TYPE_REAL = "REAL"
ASSIGNABLE_TYPES = {TYPE_BYTE, TYPE_CARD, TYPE_INT, TYPE_REAL}
RUNTIME_F_ADD = "rt.f_add"
RUNTIME_F_SUB = "rt.f_sub"
RUNTIME_F_MUL = "rt.f_mul"
RUNTIME_F_DIV = "rt.f_div"
RUNTIME_F_CMP = "rt.f_cmp"
RUNTIME_I_TO_F = "rt.i_to_f"
RUNTIME_F_TO_I = "rt.f_to_i"
RUNTIME_PRINT_F = "rt.print_f"
RUNTIME_REU_ALLOC = "rt.reu_alloc"
RUNTIME_REU_PEEK8 = "rt.reu_peek8"
RUNTIME_REU_PEEK16 = "rt.reu_peek16"
RUNTIME_REU_POKE8 = "rt.reu_poke8"
RUNTIME_REU_POKE16 = "rt.reu_poke16"
RUNTIME_OVL_LOAD = "rt.ovl_load"
RUNTIME_OVL_CALL = "rt.ovl_call"
TOKEN_RE = re.compile(
    r"\s*(?:(?P<hex>\$[0-9A-Fa-f]+)|"
    r"(?P<real>(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)|"
    r"(?P<number>\d+)|(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|"
    r"(?P<op><>|<=|>=|[(),+\-*/=<>]))"
)


class CompileError(Exception):
    pass


@dataclass(frozen=True)
class TypedValue:
    type_name: str
    value: int | float


@dataclass(frozen=True)
class PrintAction:
    text: str
    newline: bool
    requires_int_format: bool = False
    requires_real_format: bool = False


@dataclass(frozen=True)
class Decl:
    line: int
    type_name: str
    names: list[str]


@dataclass(frozen=True)
class ReuDecl:
    line: int
    element_type: str
    name: str
    length: int


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
class PrintRealStmt:
    line: int
    kind: str
    expr: "Expr"


@dataclass(frozen=True)
class ReuPokeStmt:
    line: int
    width: int
    name: str
    index_expr: "Expr"
    value_expr: "Expr"


@dataclass(frozen=True)
class OverlayCallStmt:
    line: int
    name: str


@dataclass(frozen=True)
class IfStmt:
    line: int
    condition: "Expr"
    body: list["Stmt"]


Stmt = AssignStmt | PrintStmt | PrintIntStmt | PrintRealStmt | ReuPokeStmt | OverlayCallStmt | IfStmt


@dataclass(frozen=True)
class NumberExpr:
    value: int | float
    type_name: str
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


@dataclass(frozen=True)
class CastExpr:
    target_type: str
    operand: "Expr"
    line: int


@dataclass(frozen=True)
class ReuPeekExpr:
    width: int
    name: str
    index_expr: "Expr"
    line: int


Expr = NumberExpr | VarExpr | UnaryExpr | BinaryExpr | CastExpr | ReuPeekExpr


@dataclass(frozen=True)
class OverlayBlock:
    line: int
    name: str
    statements: list[Stmt]


@dataclass(frozen=True)
class Program:
    module_name: str | None
    decls: list[Decl]
    reu_decls: list[ReuDecl]
    overlays: list[OverlayBlock]
    statements: list[Stmt]


@dataclass
class VarInfo:
    type_name: str
    value: int | float | None = None


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
            return NumberExpr(int(token[1:], 16), TYPE_CARD, self.line)
        if re.fullmatch(r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+", token):
            return NumberExpr(float(token), TYPE_REAL, self.line)
        if token.isdigit():
            return NumberExpr(int(token, 10), TYPE_CARD, self.line)
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
            if self.peek() == "(" and token.upper() in {"REUPEEK8", "REUPEEK16"}:
                self.take()
                name_token = self.take()
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name_token):
                    raise fail(self.line, "expected REU array name")
                if self.take() != ",":
                    raise fail(self.line, f"expected ',' in {token}(...)")
                index_expr = self.parse_comparison()
                if self.take() != ")":
                    raise fail(self.line, f"expected ')' after {token} arguments")
                width = 8 if token.upper() == "REUPEEK8" else 16
                return ReuPeekExpr(width, name_token, index_expr, self.line)
            if self.peek() == "(" and token.upper() in {TYPE_REAL, TYPE_INT}:
                self.take()
                operand = self.parse_comparison()
                if self.take() != ")":
                    raise fail(self.line, f"expected ')' after {token} conversion")
                return CastExpr(token.upper(), operand, self.line)
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


def parse_reu_decl(line_no: int, text: str) -> ReuDecl:
    match = re.fullmatch(r"REU\s+(BYTE)\s+ARRAY\s+([A-Za-z_][A-Za-z0-9_]*)\((\d+)\)", text, flags=re.IGNORECASE)
    if not match:
        raise fail(line_no, "expected REU declaration like 'REU BYTE ARRAY big(50000)'")
    element_type, name, length_text = match.groups()
    length = int(length_text, 10)
    if length <= 0:
        raise fail(line_no, "REU array length must be positive")
    return ReuDecl(line_no, element_type.upper(), name, length)


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


def parse_real_stmt(line_no: int, text: str, kind: str) -> PrintRealStmt:
    inner = text[text.find("(") + 1 : -1].strip()
    return PrintRealStmt(line_no, kind, parse_expression(inner, line_no))


def parse_name_and_args(line_no: int, text: str, kind: str, expected_args: int) -> tuple[str, list[str]]:
    inner = text[text.find("(") + 1 : -1].strip()
    parts = [part.strip() for part in inner.split(",")]
    if len(parts) != expected_args:
        raise fail(line_no, f"{kind} expects {expected_args} arguments")
    name = parts[0]
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise fail(line_no, f"invalid REU/overlay identifier: {name}")
    return name, parts[1:]


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
    if upper.startswith("PRINTR(") and text.endswith(")"):
        return parse_real_stmt(line_no, text, "PrintR"), index + 1
    if upper.startswith("PRINTRE(") and text.endswith(")"):
        return parse_real_stmt(line_no, text, "PrintRE"), index + 1
    if upper.startswith("REUPOKE8(") and text.endswith(")"):
        name, args = parse_name_and_args(line_no, text, "ReuPoke8", 3)
        return ReuPokeStmt(line_no, 8, name, parse_expression(args[0], line_no), parse_expression(args[1], line_no)), index + 1
    if upper.startswith("REUPOKE16(") and text.endswith(")"):
        name, args = parse_name_and_args(line_no, text, "ReuPoke16", 3)
        return ReuPokeStmt(line_no, 16, name, parse_expression(args[0], line_no), parse_expression(args[1], line_no)), index + 1
    if upper.startswith("OVERLAYCALL(") and text.endswith(")"):
        name, _args = parse_name_and_args(line_no, text, "OverlayCall", 1)
        return OverlayCallStmt(line_no, name), index + 1
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

    overlays: list[OverlayBlock] = []
    while index < len(lines) and lines[index][1].upper().startswith("OVERLAY "):
        line_no, text_line = lines[index]
        name = text_line.split(None, 1)[1].strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            raise fail(line_no, f"invalid overlay name: {name}")
        body, next_index = parse_block(lines, index + 1, {"ENDOVERLAY"})
        if next_index >= len(lines) or lines[next_index][1].upper() != "ENDOVERLAY":
            raise fail(line_no, "OVERLAY without matching ENDOVERLAY")
        overlays.append(OverlayBlock(line_no, name, body))
        index = next_index + 1

    if index >= len(lines) or lines[index][1].upper() != "PROC MAIN()":
        line_no = lines[index][0] if index < len(lines) else 1
        raise fail(line_no, "expected 'PROC main()'")
    index += 1

    decls: list[Decl] = []
    reu_decls: list[ReuDecl] = []
    while index < len(lines):
        line_no, text = lines[index]
        head = text.split(None, 1)[0].upper()
        if head in ASSIGNABLE_TYPES:
            decls.append(parse_decl(line_no, text))
            index += 1
            continue
        if head == "REU":
            reu_decls.append(parse_reu_decl(line_no, text))
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

    return Program(module_name, decls, reu_decls, overlays, statements)


def signed_compare(value: TypedValue) -> int:
    return value.value if value.type_name == TYPE_INT else value.value


def arithmetic_type(left: str, right: str) -> str:
    return TYPE_INT if TYPE_INT in {left, right} else TYPE_CARD


def ensure_unsigned(value: int, line: int, op: str) -> None:
    if value < 0:
        raise fail(line, f"unsigned result became negative during '{op}'")


def quantize_real(value: float, line: int) -> float:
    try:
        rounded = struct.unpack("<f", struct.pack("<f", float(value)))[0]
    except OverflowError as exc:
        raise fail(line, "REAL32 overflow") from exc
    if not math.isfinite(rounded):
        raise fail(line, "REAL32 overflow")
    return rounded


def to_real(value: TypedValue, line: int, used_runtime_imports: set[str]) -> TypedValue:
    if value.type_name == TYPE_REAL:
        return TypedValue(TYPE_REAL, quantize_real(float(value.value), line))
    used_runtime_imports.add(RUNTIME_I_TO_F)
    return TypedValue(TYPE_REAL, quantize_real(float(value.value), line))


def eval_expr(
    expr: Expr,
    symbols: dict[str, VarInfo],
    reu_arrays: dict[str, bytearray],
    line_hint: int,
    used_runtime_imports: set[str],
) -> TypedValue:
    if isinstance(expr, NumberExpr):
        if expr.type_name == TYPE_REAL:
            return TypedValue(TYPE_REAL, quantize_real(float(expr.value), line_hint))
        return TypedValue(expr.type_name, expr.value)
    if isinstance(expr, VarExpr):
        info = symbols.get(expr.name)
        if info is None:
            raise fail(line_hint, f"unknown variable '{expr.name}'")
        if info.value is None:
            raise fail(line_hint, f"variable '{expr.name}' used before assignment")
        return TypedValue(info.type_name, info.value)
    if isinstance(expr, ReuPeekExpr):
        index_value = eval_expr(expr.index_expr, symbols, reu_arrays, line_hint, used_runtime_imports)
        if index_value.type_name == TYPE_REAL:
            raise fail(line_hint, "REU indexes must be integer expressions")
        store = reu_arrays.get(expr.name)
        if store is None:
            raise fail(line_hint, f"unknown REU array '{expr.name}'")
        index = int(index_value.value)
        width_bytes = 1 if expr.width == 8 else 2
        if index < 0 or index + width_bytes > len(store):
            raise fail(line_hint, f"REU access out of bounds for '{expr.name}'")
        used_runtime_imports.add(RUNTIME_REU_PEEK8 if expr.width == 8 else RUNTIME_REU_PEEK16)
        if expr.width == 8:
            return TypedValue(TYPE_BYTE, store[index])
        return TypedValue(TYPE_CARD, store[index] | (store[index + 1] << 8))
    if isinstance(expr, CastExpr):
        operand = eval_expr(expr.operand, symbols, reu_arrays, line_hint, used_runtime_imports)
        if expr.target_type == TYPE_REAL:
            return to_real(operand, line_hint, used_runtime_imports)
        if expr.target_type == TYPE_INT:
            if operand.type_name == TYPE_REAL:
                used_runtime_imports.add(RUNTIME_F_TO_I)
                truncated = math.trunc(operand.value)
                if not -0x8000 <= truncated <= 0x7FFF:
                    raise fail(line_hint, f"value {truncated} does not fit in INT")
                return TypedValue(TYPE_INT, truncated)
            coerced = coerce_to_type(TYPE_INT, operand, line_hint, used_runtime_imports)
            return TypedValue(TYPE_INT, coerced)
        raise fail(line_hint, f"unsupported conversion {expr.target_type}(...)")
    if isinstance(expr, UnaryExpr):
        operand = eval_expr(expr.operand, symbols, reu_arrays, line_hint, used_runtime_imports)
        if operand.type_name == TYPE_REAL:
            used_runtime_imports.add(RUNTIME_F_SUB)
            return TypedValue(TYPE_REAL, quantize_real(-float(operand.value), line_hint))
        value = -int(operand.value)
        return TypedValue(TYPE_INT, value)
    if isinstance(expr, BinaryExpr):
        left = eval_expr(expr.left, symbols, reu_arrays, line_hint, used_runtime_imports)
        right = eval_expr(expr.right, symbols, reu_arrays, line_hint, used_runtime_imports)
        op = expr.op
        if TYPE_REAL in {left.type_name, right.type_name}:
            left_real = to_real(left, line_hint, used_runtime_imports)
            right_real = to_real(right, line_hint, used_runtime_imports)
            lhs = float(left_real.value)
            rhs = float(right_real.value)

            if op == "+":
                used_runtime_imports.add(RUNTIME_F_ADD)
                return TypedValue(TYPE_REAL, quantize_real(lhs + rhs, line_hint))
            if op == "-":
                used_runtime_imports.add(RUNTIME_F_SUB)
                return TypedValue(TYPE_REAL, quantize_real(lhs - rhs, line_hint))
            if op == "*":
                used_runtime_imports.add(RUNTIME_F_MUL)
                return TypedValue(TYPE_REAL, quantize_real(lhs * rhs, line_hint))
            if op == "/":
                if rhs == 0.0:
                    raise fail(line_hint, "division by zero")
                used_runtime_imports.add(RUNTIME_F_DIV)
                return TypedValue(TYPE_REAL, quantize_real(lhs / rhs, line_hint))

            used_runtime_imports.add(RUNTIME_F_CMP)
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

        if op in {"+", "-", "*", "/"}:
            if op == "+":
                value = int(left.value) + int(right.value)
            elif op == "-":
                value = int(left.value) - int(right.value)
            elif op == "*":
                value = int(left.value) * int(right.value)
            else:
                if int(right.value) == 0:
                    raise fail(line_hint, "division by zero")
                result_type = arithmetic_type(left.type_name, right.type_name)
                if result_type == TYPE_INT:
                    value = int(int(left.value) / int(right.value))
                else:
                    value = int(left.value) // int(right.value)
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


def coerce_to_type(target_type: str, value: TypedValue, line: int, used_runtime_imports: set[str]) -> int | float:
    raw = value.value
    if target_type == TYPE_REAL:
        return float(to_real(value, line, used_runtime_imports).value)
    if value.type_name == TYPE_REAL:
        raise fail(line, f"cannot assign REAL to {target_type} without explicit INT(...)")
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


def format_real(value: float) -> str:
    text = format(value, ".9g")
    if "e" not in text.lower() and "." not in text:
        text += ".0"
    return text


def build_overlay_payload(name: str) -> bytes:
    return f"overlay:{name}\0".encode("ascii")


def execute_program(program: Program) -> tuple[list[PrintAction], set[str], list[tuple[str, bytes]]]:
    symbols: dict[str, VarInfo] = {}
    for decl in program.decls:
        for name in decl.names:
            if name in symbols:
                raise fail(decl.line, f"duplicate declaration for '{name}'")
            symbols[name] = VarInfo(decl.type_name)

    reu_arrays: dict[str, bytearray] = {}
    for decl in program.reu_decls:
        if decl.name in symbols or decl.name in reu_arrays:
            raise fail(decl.line, f"duplicate declaration for '{decl.name}'")
        if decl.element_type != TYPE_BYTE:
            raise fail(decl.line, "only REU BYTE ARRAY is currently supported")
        reu_arrays[decl.name] = bytearray(decl.length)

    overlay_table: dict[str, OverlayBlock] = {}
    for overlay in program.overlays:
        if overlay.name in overlay_table:
            raise fail(overlay.line, f"duplicate overlay '{overlay.name}'")
        overlay_table[overlay.name] = overlay

    actions: list[PrintAction] = []
    used_runtime_imports: set[str] = set()
    used_overlay_payloads: list[tuple[str, bytes]] = []
    used_overlay_names: set[str] = set()

    if reu_arrays:
        used_runtime_imports.add(RUNTIME_REU_ALLOC)

    def exec_block(statements: list[Stmt]) -> None:
        for stmt in statements:
            if isinstance(stmt, AssignStmt):
                info = symbols.get(stmt.name)
                if info is None:
                    raise fail(stmt.line, f"unknown variable '{stmt.name}'")
                value = eval_expr(stmt.expr, symbols, reu_arrays, stmt.line, used_runtime_imports)
                info.value = coerce_to_type(info.type_name, value, stmt.line, used_runtime_imports)
                continue
            if isinstance(stmt, PrintStmt):
                actions.append(PrintAction(stmt.value, stmt.kind == "PrintE"))
                continue
            if isinstance(stmt, PrintIntStmt):
                value = eval_expr(stmt.expr, symbols, reu_arrays, stmt.line, used_runtime_imports)
                if value.type_name == TYPE_REAL:
                    raise fail(stmt.line, "PrintI requires an integer expression; use INT(...) explicitly")
                actions.append(
                    PrintAction(
                        format_integer(value),
                        stmt.kind == "PrintIE",
                        requires_int_format=True,
                    )
                )
                continue
            if isinstance(stmt, PrintRealStmt):
                value = eval_expr(stmt.expr, symbols, reu_arrays, stmt.line, used_runtime_imports)
                real_value = to_real(value, stmt.line, used_runtime_imports)
                actions.append(
                    PrintAction(
                        format_real(float(real_value.value)),
                        stmt.kind == "PrintRE",
                        requires_real_format=True,
                    )
                )
                continue
            if isinstance(stmt, ReuPokeStmt):
                store = reu_arrays.get(stmt.name)
                if store is None:
                    raise fail(stmt.line, f"unknown REU array '{stmt.name}'")
                index_value = eval_expr(stmt.index_expr, symbols, reu_arrays, stmt.line, used_runtime_imports)
                if index_value.type_name == TYPE_REAL:
                    raise fail(stmt.line, "REU indexes must be integer expressions")
                index = int(index_value.value)
                value = eval_expr(stmt.value_expr, symbols, reu_arrays, stmt.line, used_runtime_imports)
                width_bytes = 1 if stmt.width == 8 else 2
                if index < 0 or index + width_bytes > len(store):
                    raise fail(stmt.line, f"REU access out of bounds for '{stmt.name}'")
                if value.type_name == TYPE_REAL:
                    raise fail(stmt.line, "REU poke requires an integer value")
                if stmt.width == 8:
                    raw = coerce_to_type(TYPE_BYTE, value, stmt.line, used_runtime_imports)
                    store[index] = int(raw)
                    used_runtime_imports.add(RUNTIME_REU_POKE8)
                else:
                    raw = coerce_to_type(TYPE_CARD, value, stmt.line, used_runtime_imports)
                    store[index] = int(raw) & 0xFF
                    store[index + 1] = (int(raw) >> 8) & 0xFF
                    used_runtime_imports.add(RUNTIME_REU_POKE16)
                continue
            if isinstance(stmt, OverlayCallStmt):
                overlay = overlay_table.get(stmt.name)
                if overlay is None:
                    raise fail(stmt.line, f"unknown overlay '{stmt.name}'")
                used_runtime_imports.update({RUNTIME_OVL_LOAD, RUNTIME_OVL_CALL})
                if stmt.name not in used_overlay_names:
                    used_overlay_names.add(stmt.name)
                    used_overlay_payloads.append((stmt.name, build_overlay_payload(stmt.name)))
                exec_block(overlay.statements)
                continue
            if isinstance(stmt, IfStmt):
                cond = eval_expr(stmt.condition, symbols, reu_arrays, stmt.line, used_runtime_imports)
                if cond.value != 0:
                    exec_block(stmt.body)
                continue
            raise fail(stmt.line, "unsupported statement kind")

    exec_block(program.statements)
    return actions, used_runtime_imports, used_overlay_payloads


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
    parser = argparse.ArgumentParser(
        description="Compile a minimal Action-like source file into ActionC64U .avo or .avm"
    )
    parser.add_argument("input", help="input .act file")
    parser.add_argument("-o", "--output", help="output .avo or .avm file")
    parser.add_argument("--object-output", help="explicit .avo output path when --emit-avm is used")
    parser.add_argument("--emit-avm", action="store_true", help="run the linker after emitting the main .avo")
    parser.add_argument(
        "--runtime-dir",
        action="append",
        default=[],
        help="runtime module directory for linker resolution (default: src/runtime/modules)",
    )
    parser.add_argument("--entry-offset", type=int, default=0, help="entry offset for the generated main payload")
    return parser


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_runtime_dirs() -> list[Path]:
    return [repo_root() / "src" / "runtime" / "modules"]


def default_output_path(input_path: Path, emit_avm: bool) -> Path:
    suffix = ".avm" if emit_avm else ".avo"
    return repo_root() / "build" / f"{input_path.stem}{suffix}"


def module_name_for(program: Program, input_path: Path) -> str:
    return program.module_name or input_path.stem


def collect_imports(actions: Iterable[PrintAction], runtime_imports: set[str]) -> list[str]:
    imports: set[str] = set(runtime_imports)
    for action in actions:
        imports.add(RUNTIME_PRINT_LINE if action.newline else RUNTIME_PRINT)
        if action.requires_int_format:
            imports.add(RUNTIME_FORMAT_INT)
        if action.requires_real_format:
            imports.add(RUNTIME_PRINT_F)
    return sorted(imports)


def run_linker(main_object: Path, avm_output: Path, runtime_dirs: list[Path]) -> int:
    linker = Path(__file__).resolve().with_name("actionc64u_link.py")
    map_output = avm_output.with_suffix(".map.txt")
    command = [
        sys.executable,
        str(linker),
        str(main_object),
        "--output",
        str(avm_output),
        "--map-output",
        str(map_output),
    ]
    for runtime_dir in runtime_dirs:
        command.extend(["--runtime-dir", str(runtime_dir)])

    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode

    sys.stdout.write(result.stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.is_file():
        parser.error(f"input file not found: {input_path}")

    requested_output = Path(args.output) if args.output else None
    emit_avm = args.emit_avm or (requested_output is not None and requested_output.suffix.lower() == ".avm")
    output_path = requested_output or default_output_path(input_path, emit_avm)

    runtime_dirs = [Path(path) for path in args.runtime_dir] if args.runtime_dir else default_runtime_dirs()
    object_path = Path(args.object_output) if args.object_output else (
        output_path.with_suffix(".avo") if emit_avm else output_path
    )
    avm_output = output_path if emit_avm else None

    if emit_avm and output_path.suffix.lower() != ".avm":
        parser.error("--emit-avm requires an .avm --output path")

    object_path.parent.mkdir(parents=True, exist_ok=True)
    if avm_output is not None:
        avm_output.parent.mkdir(parents=True, exist_ok=True)

    try:
        source_text = input_path.read_text(encoding="ascii")
        program = parse_program(source_text)
        actions, runtime_imports, overlay_payloads = execute_program(program)
        payload = emit_payload(actions)
        imports = collect_imports(actions, runtime_imports)
        write_avo(
            object_path,
            AvoObject(
                module_name=module_name_for(program, input_path),
                entry_offset=args.entry_offset,
                exports=[("main", args.entry_offset)],
                imports=imports,
                payload=payload,
                overlays=[OverlayObject(name=name, imports=[], payload=overlay_payload) for name, overlay_payload in overlay_payloads],
            ),
        )
    except (CompileError, UnicodeDecodeError, UnicodeEncodeError, AvoFormatError) as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"wrote {object_path}")
    if avm_output is None:
        return 0

    return run_linker(object_path, avm_output, runtime_dirs)


if __name__ == "__main__":
    raise SystemExit(main())
