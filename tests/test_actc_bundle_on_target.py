from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


def build_manifest_bundle(source_dir: Path) -> str:
    parts: list[str] = []
    for manifest in sorted(source_dir.glob("*.mod")):
        text = manifest.read_text(encoding="ascii").replace("\r\n", "\n").strip()
        parts.append(f"FILE {manifest.name.lower()}\n{text}\nEND\n")
    return "\n".join(parts)


class TestActcBundleOnTarget(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.build_actc = self.root / "tools" / "build_actc.sh"
        self.build_vm = self.root / "tools" / "build_vmrun.sh"
        self.runner = self.root / "tools" / "cpmemu_runner.py"
        self.libmods = self.root / "src" / "tools_cpm" / "libmods"

    def build_tool(self, script: Path) -> None:
        result = subprocess.run(
            [str(script)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            self.skipTest(f"required CP/M tool build unavailable: {output.strip()}")

    def run_cpm(self, cwd: Path, program: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(self.runner),
                "--cwd",
                str(cwd),
                program,
                *args,
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )

    def test_compile_and_run_with_packed_manifest_bundle(self) -> None:
        self.build_tool(self.build_actc)
        self.build_tool(self.build_vm)

        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            shutil.copy2(self.root / "build" / "actc.com", drive / "actc.com")
            shutil.copy2(self.root / "build" / "vm.com", drive / "vm.com")
            (drive / "libmods.dat").write_text(build_manifest_bundle(self.libmods), encoding="ascii")
            (drive / "main.act").write_text(
                'PROC main()\nPrintE("HELLO FROM BUNDLE")\nRETURN\n',
                encoding="ascii",
            )

            compile_result = self.run_cpm(drive, "actc.com")
            compile_output = compile_result.stdout + compile_result.stderr
            self.assertEqual(compile_result.returncode, 0, msg=compile_output)
            self.assertTrue((drive / "main.avm").is_file())

            run_result = self.run_cpm(drive, "vm.com", "main.avm")
            run_output = run_result.stdout + run_result.stderr
            self.assertEqual(run_result.returncode, 0, msg=run_output)
            self.assertIn("HELLO FROM BUNDLE", run_output)


if __name__ == "__main__":
    unittest.main()
