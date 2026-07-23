from pathlib import Path
import shutil
import subprocess
import sys
import unittest


class TestMathRuntime(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def require_host_harness(self) -> None:
        if shutil.which("cc") is None:
            self.skipTest("C compiler not found")
        if not (self.root / "third_party" / "lib6502" / "lib6502.c").is_file():
            self.skipTest("lib6502 source not found")

    def run_tool(self, name: str, *arguments: str) -> str:
        completed = subprocess.run(
            [sys.executable, str(self.root / "tools" / name), *arguments],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=True,
        )
        return completed.stdout

    def test_generated_math_objects_are_current(self) -> None:
        self.run_tool("generate_math_runtime.py", "--check")

    def test_ieee_add_sub_mul_compare_machine_code(self) -> None:
        self.require_host_harness()
        output = self.run_tool(
            "verify_f_ieee_runtime.py", "--random-cases", "64"
        )
        for operation in (
            "add",
            "sub",
            "mul",
            "cmp",
            "sign",
            "trunc",
            "floor",
            "ceil",
            "round",
            "frac",
            "mod",
            "hypot",
            "pow",
            "wrap_pi",
            "sin",
            "cos",
            "tan",
            "exp",
            "ln",
            "log2",
            "log10",
            "deg_to_rad",
            "rad_to_deg",
            "min",
            "max",
            "clamp",
        ):
            self.assertIn(f"rt_f_{operation}", output)
        self.assertIn("exact edge/random cases passed", output)

    def test_ieee_division_machine_code(self) -> None:
        self.require_host_harness()
        output = self.run_tool(
            "verify_f_div_runtime.py", "--random-cases", "64"
        )
        self.assertIn("exact edge/random cases passed", output)

    def test_ieee_square_root_machine_code(self) -> None:
        self.require_host_harness()
        output = self.run_tool(
            "verify_f_sqrt_runtime.py", "--random-cases", "64"
        )
        self.assertIn("exponent-boundary/edge/random cases passed", output)

    def test_ieee_print_machine_code(self) -> None:
        self.require_host_harness()
        output = self.run_tool(
            "verify_f_print_runtime.py", "--random-cases", "64"
        )
        self.assertIn("exact edge/random strings passed", output)


if __name__ == "__main__":
    unittest.main()
