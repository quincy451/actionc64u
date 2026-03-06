from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HEADER_SIZE = 10
MAGIC = b"AVM1"
OPCODE_CALLN = 0x49
OPCODE_SETP16 = 0x61
INTR_PRINT = 0xFF00
INTR_PRINTE = 0xFF10
INTR_EXIT = 0xFF20


class TestCompileFeatures(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.compiler = self.root / "tools" / "actionc64u_compile.py"

    def compile_ok(self, source: Path, output_name: str) -> tuple[Path, bytes]:
        output = self.root / "build" / output_name
        result = subprocess.run(
            [sys.executable, str(self.compiler), str(source), "--output", str(output)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertTrue(output.is_file())
        blob = output.read_bytes()
        self.assertGreaterEqual(len(blob), HEADER_SIZE)
        self.assertEqual(blob[:4], MAGIC)
        self.assertEqual(blob[4], 1)
        payload_len = int.from_bytes(blob[5:7], "little")
        entry_offset = int.from_bytes(blob[7:9], "little")
        self.assertEqual(blob[9], 0)
        payload = blob[HEADER_SIZE : HEADER_SIZE + payload_len]
        self.assertEqual(len(payload), payload_len)
        self.assertLessEqual(entry_offset, payload_len)
        return output, payload

    def render_output(self, payload: bytes, entry_offset: int = 0) -> str:
        pc = entry_offset
        pointer = 0
        output: list[str] = []

        while pc < len(payload):
            opcode = payload[pc]
            pc += 1

            if opcode == OPCODE_SETP16:
                self.assertLessEqual(pc + 2, len(payload))
                pointer = int.from_bytes(payload[pc : pc + 2], "little")
                pc += 2
                continue

            if opcode == OPCODE_CALLN:
                self.assertLessEqual(pc + 2, len(payload))
                target = int.from_bytes(payload[pc : pc + 2], "little")
                pc += 2

                if target == INTR_EXIT:
                    break

                self.assertIn(target, {INTR_PRINT, INTR_PRINTE})
                self.assertLess(pointer, len(payload))
                end = payload.index(0, pointer)
                text = payload[pointer:end].decode("ascii")
                output.append(text)
                if target == INTR_PRINTE:
                    output.append("\n")
                continue

            self.fail(f"unsupported opcode in emitted payload: 0x{opcode:02x}")

        return "".join(output)

    def test_math_example_compiles(self) -> None:
        output, payload = self.compile_ok(self.root / "examples" / "math.act", "math.avm")
        self.assertTrue(output.is_file())
        self.assertEqual(self.render_output(payload), "20\n")

    def test_if_example_compiles(self) -> None:
        output, payload = self.compile_ok(self.root / "examples" / "if.act", "if.avm")
        self.assertTrue(output.is_file())
        self.assertEqual(self.render_output(payload), "ok\n")

    def test_type_error_is_actionable(self) -> None:
        bad_source = """PROC main()\nBYTE x\nx = 1000\nPrintIE(x)\nRETURN\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "bad.act"
            out = Path(tmpdir) / "bad.avm"
            src.write_text(bad_source, encoding="ascii")
            result = subprocess.run(
                [sys.executable, str(self.compiler), str(src), "--output", str(out)],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not fit in BYTE", result.stderr)


if __name__ == "__main__":
    unittest.main()
