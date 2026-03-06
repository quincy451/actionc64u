from pathlib import Path
import subprocess
import sys
import unittest

HEADER_SIZE = 10
MAGIC = b"AVM1"
OPCODE_CALLN = 0x49
OPCODE_SETP16 = 0x61
INTR_PRINT = 0xFF00
INTR_PRINTE = 0xFF10
INTR_EXIT = 0xFF20


class TestReuAndOverlays(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.compiler = self.root / "tools" / "actionc64u_compile.py"

    def compile_program(self, source_name: str, output_name: str) -> tuple[bytes, str]:
        source = self.root / "examples" / source_name
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
        self.assertTrue(output.with_suffix(".map.txt").is_file())
        blob = output.read_bytes()
        self.assertGreaterEqual(len(blob), HEADER_SIZE)
        self.assertEqual(blob[:4], MAGIC)
        payload_len = int.from_bytes(blob[5:7], "little")
        payload = blob[HEADER_SIZE : HEADER_SIZE + payload_len]
        map_text = output.with_suffix(".map.txt").read_text(encoding="ascii")
        return payload, map_text

    def render_output(self, payload: bytes) -> str:
        pc = 0
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

    def test_reu_demo_outputs_expected_text_and_modules(self) -> None:
        payload, map_text = self.compile_program("reu_demo.act", "reu_demo.avm")
        self.assertEqual(self.render_output(payload), "reu ok\n")
        self.assertIn("rt.reu_alloc", map_text)
        self.assertIn("rt.reu_poke8", map_text)
        self.assertIn("rt.reu_peek8", map_text)
        self.assertNotIn("rt.ovl_call", map_text)

    def test_overlay_demo_outputs_expected_text_and_overlay_map(self) -> None:
        payload, map_text = self.compile_program("ovl_demo.act", "ovl_demo.avm")
        self.assertEqual(self.render_output(payload), "42\n")
        self.assertIn("rt.ovl_call", map_text)
        self.assertIn("rt.ovl_load", map_text)
        self.assertIn("overlays:", map_text)
        self.assertIn("Math", map_text)
        self.assertNotIn("rt.reu_alloc", map_text)


if __name__ == "__main__":
    unittest.main()
