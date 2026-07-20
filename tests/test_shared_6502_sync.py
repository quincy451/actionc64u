from __future__ import annotations

import importlib.util
import os
import shutil
import tempfile
import unittest
from pathlib import Path


class TestShared6502Sync(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        script = cls.root / "tools" / "shared_6502_sync.py"
        spec = importlib.util.spec_from_file_location("shared_6502_sync", script)
        assert spec is not None and spec.loader is not None
        cls.sync = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.sync)

    def peer_checkout(self) -> Path | None:
        configured = [
            os.environ.get("IDUN_ACTION_ROOT"),
            os.environ.get("ACTION_NATIVE_ROOT"),
        ]
        candidates = [
            *(Path(value).expanduser() for value in configured if value),
            self.root.parent / "actionc64u",
            self.root.parent / "action" / "actionc64u",
            self.root.parent / "idun_fork",
            self.root.parent.parent / "idun_fork",
        ]
        return next(
            (
                candidate.resolve()
                for candidate in candidates
                if candidate is not None
                and candidate.resolve() != self.root.resolve()
                and (candidate / self.sync.MANIFEST).is_file()
            ),
            None,
        )

    def test_checkout_matches_shared_6502_manifest(self) -> None:
        self.assertEqual([], self.sync.verify_manifest(self.root))

    def test_only_os_specific_dbf_adapters_are_excluded(self) -> None:
        self.assertEqual(
            (
                "rt_dbf_create.obj",
                "rt_dbf_file_open_write.obj",
            ),
            self.sync.EXCLUDED_MODULES,
        )

    def test_manifest_detects_changed_runtime_module(self) -> None:
        manifest = self.sync.load_manifest(self.root)
        files = manifest["files"]
        self.assertIsInstance(files, dict)
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary)
            for relative_text in files:
                relative = Path(relative_text)
                target = checkout / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.root / relative, target)
            target_manifest = checkout / self.sync.MANIFEST
            target_manifest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.root / self.sync.MANIFEST, target_manifest)
            module = next(
                checkout / relative
                for relative in map(Path, files)
                if relative.suffix == ".obj"
            )
            module.write_bytes(module.read_bytes() + b"\n")
            self.assertTrue(
                any("digest differs" in error for error in self.sync.verify_manifest(checkout))
            )

    def test_peer_checkout_matches_when_available(self) -> None:
        peer = self.peer_checkout()
        if peer is None:
            self.skipTest("peer checkout is not available")
        self.assertEqual([], self.sync.compare_roots(self.root, peer))

    def test_portable_parity_sources_match_peer_when_available(self) -> None:
        peer = self.peer_checkout()
        if peer is None:
            self.skipTest("peer checkout is not available")
        local_root = self.root / "tests" / "parity"
        peer_root = peer / "tests" / "parity"
        local = {path.name: path.read_bytes() for path in local_root.glob("*.act")}
        remote = {path.name: path.read_bytes() for path in peer_root.glob("*.act")}
        self.assertEqual(local, remote)


if __name__ == "__main__":
    unittest.main()
