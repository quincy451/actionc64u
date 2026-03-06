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
            "docs/spec.md",
            "src/compiler",
            "src/vm",
            "src/runtime",
            "src/tools_cpm",
            "tools/env_check.sh",
            "tools/setup_wsl.sh",
            "tools/path_probe.py",
            "pytest/__main__.py",
            "tools",
            "examples",
            "tests",
        ]

        missing = [path for path in required if not (root / path).exists()]
        self.assertFalse(missing, f"Missing required project paths: {missing}")


if __name__ == "__main__":
    unittest.main()
