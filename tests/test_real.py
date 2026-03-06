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


class TestRealFeatures(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.compiler = self.root / "tools" / "actionc64u_compile.py"

    def compile_program(self, source: Path, output_name: str) -> tuple[Path, bytes, str]:
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
        self.assertTrue(output.with_suffix(".avo").is_file())
        map_output = output.with_suffix(".map.txt")
        self.assertTrue(map_output.is_file())
        blob = output.read_bytes()
        self.assertGreaterEqual(len(blob), HEADER_SIZE)
        self.assertEqual(blob[:4], MAGIC)
        self.assertEqual(blob[4], 1)
        payload_len = int.from_bytes(blob[5:7], "little")
        payload = blob[HEADER_SIZE : HEADER_SIZE + payload_len]
        return output, payload, map_output.read_text(encoding="ascii")

    def render_output(self, payload: bytes, entry_offset: int = 0) -> str:
        pc = entry_offset
        pointer = 0
        output: list[str] = []

        while pc < len(payload):
            opcode = payload[pc]
            pc += 1

            if opcode == OPCODE_SETP16:
                pointer = int.from_bytes(payload[pc : pc + 2], "little")
                pc += 2
                continue

            if opcode == OPCODE_CALLN:
                target = int.from_bytes(payload[pc : pc + 2], "little")
                pc += 2
                if target == INTR_EXIT:
                    break
                self.assertIn(target, {INTR_PRINT, INTR_PRINTE})
                end = payload.index(0, pointer)
                text = payload[pointer:end].decode("ascii")
                output.append(text)
                if target == INTR_PRINTE:
                    output.append("\n")
                continue

            self.fail(f"unsupported opcode in emitted payload: 0x{opcode:02x}")

        return "".join(output)

    def test_real_math_example_outputs_expected_text(self) -> None:
        _output, payload, map_text = self.compile_program(
            self.root / "examples" / "real_math.act",
            "real_math.avm",
        )
        self.assertEqual(self.render_output(payload), "7.5\n")
        self.assertIn("rt.f_add", map_text)
        self.assertIn("rt.f_mul", map_text)
        self.assertIn("rt.i_to_f", map_text)
        self.assertIn("rt.print_f", map_text)

    def test_real_compare_example_outputs_expected_text(self) -> None:
        _output, payload, map_text = self.compile_program(
            self.root / "examples" / "real_cmp.act",
            "real_cmp.avm",
        )
        self.assertEqual(self.render_output(payload), "ok\n")
        self.assertIn("rt.f_cmp", map_text)
        self.assertNotIn("rt.print_f", map_text)

    def test_real_to_int_conversion_truncates_toward_zero(self) -> None:
        source_text = "PROC main()\nREAL x\nx = 3.75\nPrintIE(INT(x))\nRETURN\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "real_to_int.act"
            src.write_text(source_text, encoding="ascii")
            _output, payload, map_text = self.compile_program(src, "real_to_int.avm")

        self.assertEqual(self.render_output(payload), "3\n")
        self.assertIn("rt.f_to_i", map_text)


if __name__ == "__main__":
    unittest.main()
