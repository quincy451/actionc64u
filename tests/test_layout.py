from pathlib import Path
import unittest


class TestRepoLayout(unittest.TestCase):
    def test_repo_layout_smoke(self) -> None:
        root = Path(__file__).resolve().parents[1]

        required = [
            "README.md",
            "LICENSE",
            ".gitignore",
            "AGENTS.md",
            "docs/inspiration/action.pdf",
            "docs/setup_wsl.md",
            "docs/roadmap.md",
            "docs/architecture.md",
            "docs/cpmemu.md",
            "docs/cpm65_abi.md",
            "docs/acheron.md",
            "docs/bytecode.md",
            "docs/cpm65_cmdline.md",
            "docs/blockers.md",
            "docs/spec.md",
            "docs/vm_abi.md",
            "docs/linker.md",
            "docs/real32.md",
            "src/compiler",
            "src/vm",
            "src/vm/vmhello/vmhello.asm",
            "src/vm/vmrun/vmrun.asm",
            "src/runtime",
            "src/runtime/modules",
            "src/runtime/modules/rt_f_add.avo",
            "src/runtime/modules/rt_f_sub.avo",
            "src/runtime/modules/rt_f_mul.avo",
            "src/runtime/modules/rt_f_div.avo",
            "src/runtime/modules/rt_f_cmp.avo",
            "src/runtime/modules/rt_i_to_f.avo",
            "src/runtime/modules/rt_f_to_i.avo",
            "src/runtime/modules/rt_print_f.avo",
            "src/runtime/modules/rt_print_str.avo",
            "src/runtime/modules/rt_print_line.avo",
            "src/runtime/modules/rt_format_int.avo",
            "src/tools_cpm",
            "src/tools_cpm/hello/hello.asm",
            "src/tools_cpm/hello/hello.c",
            "tools/actionc64u_compile.py",
            "tools/actionc64u_link.py",
            "tools/avo_format.py",
            "tools/avm_pack.py",
            "tools/env_check.sh",
            "tools/setup_wsl.sh",
            "tools/path_probe.py",
            "tools/cpmemu_runner.py",
            "tools/build_cpm65_notes.sh",
            "tools/build_hello.sh",
            "tools/build_vmhello.sh",
            "tools/build_vmrun.sh",
            "pytest/__main__.py",
            "tools",
            "examples",
            "examples/hello.act",
            "examples/if.act",
            "examples/math.act",
            "examples/real_math.act",
            "examples/real_cmp.act",
            "examples/hello.avm",
            "examples/hello.avm.txt",
            "tests",
            "tests/test_cpmemu_available.py",
            "tests/test_hello_com.py",
            "tests/test_vmhello.py",
            "tests/test_vmrun_file.py",
            "tests/test_compile_and_run.py",
            "tests/test_compile_features.py",
            "tests/test_linker.py",
            "tests/test_real.py",
        ]

        missing = [path for path in required if not (root / path).exists()]
        self.assertFalse(missing, f"Missing required project paths: {missing}")


if __name__ == "__main__":
    unittest.main()
