from pathlib import Path
import subprocess
import sys
import unittest


class TestLinker(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.compiler = self.root / "tools" / "actionc64u_compile.py"
        self.linker = self.root / "tools" / "actionc64u_link.py"

    def compile_object(self, source_name: str, object_name: str) -> Path:
        source = self.root / "examples" / source_name
        output = self.root / "build" / object_name
        result = subprocess.run(
            [sys.executable, str(self.compiler), str(source), "--output", str(output)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertTrue(output.is_file())
        return output

    def link_object(self, object_path: Path, avm_name: str) -> tuple[Path, Path]:
        avm_output = self.root / "build" / avm_name
        map_output = avm_output.with_suffix(".map.txt")
        result = subprocess.run(
            [
                sys.executable,
                str(self.linker),
                str(object_path),
                "--output",
                str(avm_output),
                "--map-output",
                str(map_output),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertTrue(avm_output.is_file())
        self.assertTrue(map_output.is_file())
        return avm_output, map_output

    def test_print_only_program_skips_int_format_module(self) -> None:
        obj = self.compile_object("hello.act", "hello.avo")
        _avm, map_output = self.link_object(obj, "hello-linked.avm")
        map_text = map_output.read_text(encoding="ascii")
        self.assertIn("rt.print_line", map_text)
        self.assertIn("rt.print_str", map_text)
        self.assertNotIn("rt.format_int", map_text)
        self.assertNotIn("rt.f_add", map_text)
        self.assertNotIn("rt.f_cmp", map_text)
        self.assertNotIn("rt.i_to_f", map_text)
        self.assertNotIn("rt.print_f", map_text)
        self.assertNotIn("rt.reu_alloc", map_text)
        self.assertNotIn("rt.ovl_call", map_text)

    def test_integer_print_program_pulls_int_format_module(self) -> None:
        obj = self.compile_object("math.act", "math.avo")
        _avm, map_output = self.link_object(obj, "math-linked.avm")
        map_text = map_output.read_text(encoding="ascii")
        self.assertIn("rt.print_line", map_text)
        self.assertIn("rt.print_str", map_text)
        self.assertIn("rt.format_int", map_text)

    def test_linker_output_is_stable(self) -> None:
        obj = self.compile_object("hello.act", "hello-stable.avo")
        avm_one, map_one = self.link_object(obj, "hello-stable-1.avm")
        avm_two, map_two = self.link_object(obj, "hello-stable-2.avm")
        self.assertEqual(avm_one.read_bytes(), avm_two.read_bytes())
        self.assertEqual(map_one.read_text(encoding="ascii"), map_two.read_text(encoding="ascii"))


if __name__ == "__main__":
    unittest.main()
