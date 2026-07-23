from pathlib import Path
import re
import shutil
import subprocess
import unittest


ALINK_CODE_START = 0x0900
UDOS_PRESERVED_TOOL_ABI_START = 0x9800
ALINK_WORKSPACE_START = 0xA000
ALINK_WORKSPACE_END = 0xC000


class TestAlinkCapacity(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.map_path = self.root / "build" / "udos_tools" / "alink.current.map"

    def test_production_layout_preserves_live_udos_tool_abi(self) -> None:
        for tool in ("ca65", "ld65"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} not found")

        result = subprocess.run(
            [str(self.root / "tools" / "build_alink_udos.sh")],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        map_text = self.map_path.read_text(encoding="ascii")
        code_start, code_end = self.segment_bounds(map_text, "CODE")
        bss_start, bss_end = self.segment_bounds(map_text, "BSS")

        self.assertEqual(code_start, ALINK_CODE_START, msg=map_text)
        self.assertLess(code_end, UDOS_PRESERVED_TOOL_ABI_START, msg=map_text)
        self.assertGreaterEqual(bss_start, ALINK_WORKSPACE_START, msg=map_text)
        self.assertLess(bss_end, ALINK_WORKSPACE_END, msg=map_text)

    def test_debug_sidecar_defers_file_output_until_after_object_scans(self) -> None:
        alink_text = (
            self.root / "src" / "tools_udos" / "alink" / "alink.asm"
        ).read_text(encoding="ascii")
        sidecar_text = (
            self.root / "src" / "tools_udos" / "alink" / "debug_sidecar.inc"
        ).read_text(encoding="ascii")

        self.assertIn("ALINK_DEBUG_REU_BASE_BANK = $01", alink_text)
        begin = sidecar_text.index("emit_debug_sidecar_or_fail:")
        done = sidecar_text.index("emit_debug_sidecar_done:", begin)
        record = sidecar_text.index("emit_debug_entry_record_or_fail:", done)
        scan_body = sidecar_text[begin:done]
        output_body = sidecar_text[done:record]

        self.assertIn("jsr reload_root_object_or_fail", scan_body)
        self.assertIn("jsr load_pending_object_or_library_or_fail", scan_body)
        self.assertNotIn("open_output_stream_to_target_or_fail", scan_body)

        required_calls = [
            "jsr flush_debug_reu_chunk_or_fail",
            "jsr build_debug_save_target_path",
            "jsr open_output_stream_to_target_or_fail",
            "jsr stream_debug_reu_to_output_or_fail",
            "jmp close_output_stream",
        ]
        positions = [output_body.index(call) for call in required_calls]
        self.assertEqual(positions, sorted(positions), msg=output_body)

        append_begin = sidecar_text.index("append_debug_char:")
        append_end = sidecar_text.index("append_debug_newline:", append_begin)
        append_body = sidecar_text[append_begin:append_end]
        self.assertIn("jsr flush_debug_reu_chunk_or_fail", append_body)
        self.assertNotIn("append_payload_byte", append_body)

    def test_relocation_capacity_uses_dedicated_reu_region_without_synthesis_queues(self) -> None:
        alink_text = (
            self.root / "src" / "tools_udos" / "alink" / "alink.asm"
        ).read_text(encoding="ascii")
        direct_text = (
            self.root / "src" / "tools_udos" / "alink" / "direct_prg.inc"
        ).read_text(encoding="ascii")

        def constant(name: str) -> int:
            match = re.search(rf"^{name}\s*=\s*([^\s]+)", alink_text, re.MULTILINE)
            self.assertIsNotNone(match, msg=name)
            assert match is not None
            return int(match.group(1).replace("$", "0x"), 0)

        reloc_base = (
            constant("ALINK_RELOC_REU_BASE_LO")
            | constant("ALINK_RELOC_REU_BASE_HI") << 8
            | constant("ALINK_RELOC_REU_BASE_BANK") << 16
        )
        body_base = (
            constant("ALINK_BODY_REU_BASE_LO")
            | constant("ALINK_BODY_REU_BASE_HI") << 8
            | constant("ALINK_BODY_REU_BASE_BANK") << 16
        )
        reloc_max = constant("RELOC_MAX")
        reloc_record_bytes = constant("RELOC_RECORD_BYTES")
        reloc_reu_bytes = constant("RELOC_REU_BYTES")
        root_export_base = (
            constant("ALINK_ROOT_EXPORT_REU_BASE_LO")
            | constant("ALINK_ROOT_EXPORT_REU_BASE_HI") << 8
            | constant("ALINK_ROOT_EXPORT_REU_BASE_BANK") << 16
        )

        self.assertEqual(reloc_base, 0x034400)
        self.assertEqual(body_base, 0x041000)
        self.assertNotEqual(reloc_base >> 16, body_base >> 16)
        self.assertEqual(reloc_record_bytes, 5)
        self.assertEqual(reloc_reu_bytes, 0x500)
        self.assertEqual(reloc_max, 255)
        self.assertLessEqual(reloc_max * reloc_record_bytes, reloc_reu_bytes)
        self.assertLessEqual(reloc_base + reloc_reu_bytes, root_export_base)
        self.assertNotIn("ALINK_RUNTIME_STORE_REU_BASE", alink_text)
        self.assertNotIn("ALINK_LINKED_LITERAL_REU_BASE", alink_text)

        load_begin = direct_text.index("load_reloc_records_current_object_or_fail:")
        load_end = direct_text.index(
            "append_named_relocs_current_export_to_queue_or_fail:", load_begin
        )
        load_body = direct_text[load_begin:load_end]
        self.assertIn("cpx #RELOC_MAX", load_body)
        self.assertNotIn("cpx #EXTERNAL_MAX", load_body)

        append_begin = direct_text.index(
            "append_machine_code_record_current_object_or_fail:"
        )
        append_end = direct_text.index(
            "skip_machine_code_bytes_to_export_offset_or_fail:", append_begin
        )
        append_body = direct_text[append_begin:append_end]
        self.assertIn("jsr prepare_linked_reloc_cursor_or_fail", append_body)

        patch_begin = direct_text.index("find_reloc_patch_byte_for_current_offset:")
        patch_end = direct_text.index(
            "parse_object_code_import_index_at_scan_ptr_or_fail:", patch_begin
        )
        patch_body = direct_text[patch_begin:patch_end]
        self.assertIn("linked_reloc_cursor_window", patch_body)
        self.assertNotIn("load_linked_reloc_record_window_from_x_or_fail", patch_body)

        production_build = (self.root / "tools" / "build_alink_udos.sh").read_text(
            encoding="ascii"
        )
        external_match = re.search(r"-D EXTERNAL_MAX=(\d+)", production_build)
        self.assertIsNotNone(external_match)
        assert external_match is not None
        external_max = int(external_match.group(1))
        self.assertEqual(external_max, 64)
        self.assertNotIn("PENDING_SYMBOL_MAX", production_build)
        self.assertNotIn("PENDING_SYMBOL_MAX", alink_text)
        self.assertNotIn("ALINK_PENDING_REU_BASE", alink_text)
        self.assertIn("EXTERNAL_MAX * EXTERNAL_NAME_BYTES", alink_text)
        self.assertIn("EXTERNAL_MAX * PENDING_META_BYTES", alink_text)

        print_object = (
            self.root / "src" / "runtime" / "udos_modules" / "rt_print_f.obj"
        ).read_text(encoding="ascii")
        print_relocs = sum(line.startswith("r ") for line in print_object.splitlines())
        self.assertGreater(print_relocs, 64)
        self.assertLessEqual(print_relocs, reloc_max)

        exp_object = (
            self.root / "src" / "runtime" / "udos_modules" / "rt_f_exp.obj"
        ).read_text(encoding="ascii")
        exp_relocs = sum(line.startswith("r ") for line in exp_object.splitlines())
        self.assertGreater(exp_relocs, 128)
        self.assertLessEqual(exp_relocs, reloc_max)

        ln_object = (
            self.root / "src" / "runtime" / "udos_modules" / "rt_f_ln.obj"
        ).read_text(encoding="ascii")
        ln_relocs = sum(line.startswith("r ") for line in ln_object.splitlines())
        self.assertGreater(ln_relocs, 128)
        self.assertLessEqual(ln_relocs, reloc_max)

    def segment_bounds(self, map_text: str, segment: str) -> tuple[int, int]:
        match = re.search(
            rf"^{segment}\s+([0-9A-Fa-f]{{6}})\s+([0-9A-Fa-f]{{6}})\s+",
            map_text,
            re.MULTILINE,
        )
        self.assertIsNotNone(match, msg=map_text)
        assert match is not None
        return int(match.group(1), 16), int(match.group(2), 16)


if __name__ == "__main__":
    unittest.main()
