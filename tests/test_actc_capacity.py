from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
import unittest


ACTC_MIN_RESIDENT_HEADROOM = 80
ACTC_OVERLAY_SCRATCH_BASE = 0x8000


def count_body_ops(body: str) -> int:
    match = re.search(r"^b ([^\n]*)$", body, re.MULTILINE)
    if match is None:
        return 0
    stream = match.group(1)
    count = 0
    index = 0
    while index < len(stream):
        count += 1
        index += 1
        if index < len(stream) and stream[index] in "0123456789ABCDEF":
            index += 1
    return count


def assert_single_proc_object(test: unittest.TestCase, text: str, body: str, min_line: int = 2) -> None:
    match = re.match(r"^OBJ1\nf 0 src/main\.act\nq 0 0 (\d+) (\d+)\n((?:l 0 \d+ 0 \d+ \d+\n)*)", text)
    test.assertIsNotNone(match, msg=text)
    assert match is not None
    test.assertGreaterEqual(int(match.group(1)), min_line, msg=text)
    test.assertEqual(int(match.group(2)), 6, msg=text)
    debug_lines = [line for line in match.group(3).splitlines() if line]
    test.assertEqual(len(debug_lines), count_body_ops(body), msg=text)
    for index, line in enumerate(debug_lines):
        test.assertRegex(line, rf"^l 0 {index} 0 \d+ \d+$", msg=text)
    remainder = text[match.end() :]
    var_debug_prefix = re.match(
        r"^((?:V g [ibcr] \d+ 0 \d+ \d+\n|V [pl] [ibcr] \d+ \d+ 0 \d+ \d+\n)*)",
        remainder,
    )
    assert var_debug_prefix is not None
    test.assertEqual(remainder[var_debug_prefix.end() :], body, msg=text)


class TestActcCapacity(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.build_dir = self.root / "build" / "udos_tools"

    def require_toolchain(self) -> None:
        for tool in ("cc", "ca65", "ld65", "make"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} not found")

    def run_checked(self, args: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args,
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def assert_actc_stays_inside_tool_window(self) -> None:
        map_text = (self.build_dir / "actc.current.map").read_text(encoding="ascii")
        match = re.search(r"^BSS\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{6})\s+", map_text, re.MULTILINE)
        self.assertIsNotNone(match, msg=map_text)
        bss_end = int(match.group(2), 16)
        self.assertLess(
            bss_end,
            ACTC_OVERLAY_SCRATCH_BASE,
            msg=(
                f"ACTC BSS end ${bss_end:04X} overlaps overlay scratch at "
                f"${ACTC_OVERLAY_SCRATCH_BASE:04X}\n{map_text}"
            ),
        )
        resident_floor = self.find_resident_floor()
        self.assertLess(
            bss_end,
            resident_floor,
            msg=f"ACTC BSS end ${bss_end:04X} overlaps UDOS resident floor ${resident_floor:04X}\n{map_text}",
        )
        headroom = resident_floor - bss_end
        self.assertGreaterEqual(
            headroom,
            ACTC_MIN_RESIDENT_HEADROOM,
            msg=(
                f"ACTC has only {headroom} bytes below UDOS resident floor "
                f"${resident_floor:04X}; keep at least {ACTC_MIN_RESIDENT_HEADROOM} bytes for safe library growth\n"
                f"{map_text}"
            ),
        )

    def current_actc_labels(self) -> set[str]:
        return {
            fields[2].lstrip(".")
            for line in (self.build_dir / "actc.current.labels").read_text(
                encoding="ascii"
            ).splitlines()
            if len(fields := line.split()) >= 3
        }

    def find_resident_floor(self) -> int:
        udos_dir = self.root.parent / "udos"
        floor_symbols = ("tool_abi_preserved_start", "reu_transfer_chunk_loop")
        candidates = [
            udos_dir / "build" / "release" / "udos-resident.labels",
            udos_dir / "build" / "udos-resident.labels",
        ]
        for path in candidates:
            if not path.is_file():
                continue
            for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[2].lstrip(".") in floor_symbols:
                    return int(parts[1], 16)
        return 0x4AFE

    def test_production_actc_omits_disabled_fallback_scratch(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.assert_actc_stays_inside_tool_window()

        labels = self.current_actc_labels()
        fallback_only = {
            "payload_offset_hi",
            "expr_group_saved_saved_lo",
            "expr_group_saved_saved_hi",
            "expr_compare_hi",
            "expr_group_saved_compare_lo",
            "expr_group_saved_compare_hi",
            "expr_runtime_wrapped_data",
            "preallocate_condition_start_y_data",
            "preallocate_call_arg_scan_depth_data",
            "preallocate_bool_primary_start_y_data",
            "preallocate_print_start_y_data",
            "expr_print_op",
            "expr_digit_count",
            "param_bind_count_data",
            "param_bind_base_data",
            "real_rhs_index_data",
            "body_marker_visit_mask_data",
        }
        self.assertTrue(fallback_only.isdisjoint(labels), msg=sorted(fallback_only & labels))

    def test_resident_fallback_builds_retain_required_scratch(self) -> None:
        self.require_toolchain()
        build = str(self.root / "tools" / "build_actc_udos.sh")
        cases = (
            (
                "ACTC_KEEP_BODY_RESIDENT_FALLBACK=1",
                {
                    "expr_group_saved_saved_lo",
                    "expr_compare_hi",
                    "expr_group_saved_compare_hi",
                    "expr_runtime_wrapped_data",
                    "preallocate_condition_start_y_data",
                    "preallocate_call_arg_scan_depth_data",
                    "preallocate_bool_primary_start_y_data",
                    "preallocate_print_start_y_data",
                    "expr_print_op",
                    "param_bind_count_data",
                    "param_bind_base_data",
                    "real_rhs_index_data",
                },
            ),
            ("ACTC_USE_LAYOUT_OVERLAY=0", {"payload_offset_hi"}),
            (
                "ACTC_USE_EMIT_OVERLAY=0",
                {"expr_digit_count", "body_marker_visit_mask_data"},
            ),
        )
        try:
            for setting, required in cases:
                with self.subTest(setting=setting):
                    self.run_checked(
                        [
                            "env",
                            setting,
                            "ACTC_ENABLE_REAL_CONST_EVALUATOR=0",
                            build,
                        ]
                    )
                    self.assert_actc_stays_inside_tool_window()
                    labels = self.current_actc_labels()
                    self.assertTrue(required <= labels, msg=sorted(required - labels))
                    self.assertIn("actc_eval_real_const", labels)
                    self.assertNotIn("actc_real_const_parse_expr", labels)
        finally:
            self.run_checked([build])

    def assert_production_actc_loads_and_compiles_reu_source(
        self,
        source_len: int,
        min_proc_offset: int,
        max_steps: str,
        timeout: int,
    ) -> dict:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.assert_actc_stays_inside_tool_window()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-capacity"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            header = "MODULE MAIN\r"
            body = '\rPROC MAIN()\rPrintE("OK")\rRETURN\r'
            filler_len = source_len - len(header) - len(body)
            self.assertGreaterEqual(filler_len, 0)
            source = header + (" " * filler_len) + body
            self.assertGreaterEqual(source.index("PROC MAIN"), min_proc_offset)
            source_path = source_dir / "main.act"
            source_path.write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    max_steps,
                    "--dump",
                    "source_total_len:3",
                    "--dump",
                    "source_window_next_offset:3",
                    "--dump",
                    "source_window_len:2",
                ],
                timeout=timeout,
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            output_path = object_dir / "MAIN.OBJ"
            self.assertTrue(output_path.is_file(), msg=result.stdout)
            assert_single_proc_object(
                self,
                output_path.read_text(encoding="ascii"),
                "x main 0 7\nb e0r\ns OK\nk 2\nn main\n",
                min_line=3,
            )
            reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
            reu_reads = [op for op in summary["ops"] if op["kind"] == "rrd"]
            self.assertEqual(reu_stage["path"], "SRC/MAIN.ACT")
            self.assertEqual(reu_stage["actual_len"], source_len)
            self.assertEqual(reu_stage["status"], 1)
            self.assertTrue(reu_reads, msg=result.stdout)
            self.assertTrue(all(op["status"] == 1 for op in reu_reads), msg=result.stdout)
            source_total_dump = summary["dumps"]["source_total_len"]
            source_next_dump = summary["dumps"]["source_window_next_offset"]
            source_window_len_dump = summary["dumps"]["source_window_len"]
            source_total = source_total_dump[0] | (source_total_dump[1] << 8) | (source_total_dump[2] << 16)
            source_next = source_next_dump[0] | (source_next_dump[1] << 8) | (source_next_dump[2] << 16)
            source_window_len = source_window_len_dump[0] | (source_window_len_dump[1] << 8)
            self.assertEqual(source_total, source_len, msg=result.stdout)
            self.assertEqual(source_next, source_len, msg=result.stdout)
            self.assertEqual(source_window_len, 0, msg=result.stdout)
            return summary

    def test_production_actc_loads_and_compiles_256k_reu_source(self) -> None:
        summary = self.assert_production_actc_loads_and_compiles_reu_source(
            256 * 1024,
            240000,
            "240000000",
            300,
        )
        reu_reads = [op for op in summary["ops"] if op["kind"] == "rrd"]
        reu_writes = [op for op in summary["ops"] if op["kind"] == "rwr"]
        self.assertTrue(
            any(
                op["params"][2] == 1
                and ((op["params"][1] << 8) | op["params"][0]) >= 0x9000
                for op in reu_reads
            ),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xD0, 0] and op["actual_len"] == 255 for op in reu_writes),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xD0, 0] and op["actual_len"] == 255 for op in reu_reads),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xE0, 0] and op["actual_len"] == 24 for op in reu_writes),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xE0, 0] and op["actual_len"] == 24 for op in reu_reads),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xE6, 0] and op["actual_len"] == 25 for op in reu_writes),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xE6, 0] and op["actual_len"] == 25 for op in reu_reads),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xEB, 0] and op["actual_len"] == 4 for op in reu_writes),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xED, 0] and op["actual_len"] == 3 for op in reu_writes),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xED, 0] and op["actual_len"] == 3 for op in reu_reads),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0x10, 0xFF] and op["actual_len"] == 3 for op in reu_writes),
            msg=json.dumps(summary),
        )
        self.assertTrue(
            any(op["params"][0:3] == [0, 0xEC, 0] and op["actual_len"] == 1 for op in reu_writes),
            msg=json.dumps(summary),
        )

    def test_production_actc_loads_and_compiles_2mib_reu_source(self) -> None:
        self.assert_production_actc_loads_and_compiles_reu_source(
            2 * 1024 * 1024,
            2000000,
            "2000000000",
            900,
        )

    def test_production_actc_loads_and_compiles_4mib_reu_source(self) -> None:
        self.assert_production_actc_loads_and_compiles_reu_source(
            4 * 1024 * 1024,
            4000000,
            "4000000000",
            1800,
        )

    def test_production_actc_loads_and_compiles_8mib_reu_source(self) -> None:
        self.assert_production_actc_loads_and_compiles_reu_source(
            8 * 1024 * 1024,
            8000000,
            "8000000000",
            3600,
        )

    def test_production_actc_loads_and_compiles_near_16mib_reu_source(self) -> None:
        self.assert_production_actc_loads_and_compiles_reu_source(
            0xFE0000,
            16600000,
            "16600000000",
            7200,
        )

    def test_production_actc_streams_object_larger_than_legacy_content_buffer(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.assert_actc_stays_inside_tool_window()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-output-stream"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            calls = "T()\r" * 100
            source = (
                "MODULE MAIN\r"
                "INT X=[1]\r"
                "PROC T()\r"
                "RETURN\r"
                "PROC F()\r"
                f"{calls}"
                "RETURN\r"
                "PROC G()\r"
                f"{calls}"
                "RETURN\r"
                "PROC MAIN()\r"
                f"{calls}"
                "PrintIE(7)\r"
                "RETURN\r"
            )
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            output_path = object_dir / "MAIN.OBJ"
            output_text = output_path.read_text(encoding="ascii")
            self.assertGreater(len(output_text), 640)
            self.assertTrue(
                output_text.startswith(
                    "OBJ1\n"
                    "f 0 src/main.act\n"
                    "q 0 0 3 6\n"
                    "q 1 0 5 6\n"
                    "q 2 0 107 6\n"
                    "q 3 0 209 6\n"
                ),
                msg=output_text,
            )
            self.assertIn("l 0 0 0 4 1\n", output_text)
            self.assertIn("x t 0 1\nx f 1 301\n", output_text)
            self.assertIn("\ni 7\n", output_text)
            self.assertTrue(output_text.endswith("v x 1\nk 6\nn main\n"), msg=output_text)

            open_ops = [op for op in summary["ops"] if op["kind"] == "wopn"]
            write_ops = [op for op in summary["ops"] if op["kind"] == "wrte"]
            close_ops = [op for op in summary["ops"] if op["kind"] == "wcls"]
            save_ops = [op for op in summary["ops"] if op["kind"] == "save"]
            self.assertEqual(len(open_ops), 1, msg=result.stdout)
            self.assertEqual(open_ops[0]["path"], "OBJ/MAIN.OBJ")
            self.assertGreaterEqual(len(write_ops), 2, msg=result.stdout)
            self.assertEqual(sum(op["actual_len"] for op in write_ops), len(output_text))
            self.assertTrue(all(op["status"] == 1 for op in write_ops), msg=result.stdout)
            self.assertEqual(len(close_ops), 1, msg=result.stdout)
            self.assertEqual(close_ops[0]["status"], 1, msg=result.stdout)
            self.assertFalse(save_ops, msg=result.stdout)
            reu_reads = [op for op in summary["ops"] if op["kind"] == "rrd"]
            reu_writes = [op for op in summary["ops"] if op["kind"] == "rwr"]
            self.assertTrue(reu_reads, msg=result.stdout)
            self.assertTrue(
                any(op["params"][0:3] == [0, 0xE4, 0] and op["actual_len"] == 25 for op in reu_writes),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["params"][0:3] == [0, 0xE9, 0] and op["actual_len"] == 4 for op in reu_writes),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["params"][0:3] == [0, 0xEA, 0] and op["actual_len"] == 4 for op in reu_writes),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["params"][0:3] == [0, 0xE8, 0] and op["actual_len"] == 2 for op in reu_writes),
                msg=result.stdout,
            )


if __name__ == "__main__":
    unittest.main()
