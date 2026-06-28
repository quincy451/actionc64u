from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path


class TestAlinkPrgObjectCodeMatrix(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parents[2]
        self.make_text = (self.workspace / "udos" / "Makefile").read_text()

    def test_object_code_launch_groups_reference_valid_probe_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        grouped_shapes = {shape for shapes in groups.values() for shape in shapes}
        direct_cases = set(probe.DIRECT_PRG_CASES)
        successful_object_cases = {
            shape
            for shape, case in probe.DIRECT_PRG_CASES.items()
            if shape.startswith("object_code_") and not bool(case.get("expect_alink_failure", False))
        }
        rejection_object_cases = {
            shape
            for shape, case in probe.DIRECT_PRG_CASES.items()
            if shape.startswith("object_code_") and bool(case.get("expect_alink_failure", False))
        }

        stale = sorted(grouped_shapes - direct_cases)
        non_object = sorted(shape for shape in grouped_shapes if not shape.startswith("object_code_"))
        missing_successful = sorted(successful_object_cases - grouped_shapes)
        grouped_rejections = sorted(rejection_object_cases & grouped_shapes)
        unrun_groups = sorted(group for group in groups if f"for shape in $({group})" not in self.make_text)

        self.assertTrue(groups, "No ALINK PRG object-code launch shape groups found")
        self.assertFalse(stale, "Object-code launch group references missing probe cases: " + ", ".join(stale))
        self.assertFalse(non_object, "Object-code launch group contains non-object-code cases: " + ", ".join(non_object))
        self.assertFalse(
            missing_successful,
            "Successful object-code probe cases missing from launch groups: " + ", ".join(missing_successful),
        )
        self.assertFalse(
            grouped_rejections,
            "Object-code rejection probe cases should stay in the skip-launch matrix: "
            + ", ".join(grouped_rejections),
        )
        self.assertFalse(unrun_groups, "Object-code launch groups not used by a target: " + ", ".join(unrun_groups))

    def test_object_code_rejection_cases_have_focused_skip_launch_target(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        rejection_cases = self._makefile_object_code_rejection_cases(self.make_text)
        expected_rejections = {
            shape
            for shape, case in probe.DIRECT_PRG_CASES.items()
            if shape.startswith("object_code_") and bool(case.get("expect_alink_failure", False))
        }

        stale = sorted(rejection_cases - set(probe.DIRECT_PRG_CASES))
        missing = sorted(expected_rejections - rejection_cases)
        unexpected = sorted(rejection_cases - expected_rejections)

        self.assertTrue(rejection_cases, "No focused ALINK object-code rejection cases found")
        self.assertFalse(stale, "Object-code rejection group references missing probe cases: " + ", ".join(stale))
        self.assertFalse(missing, "Object-code rejection probe cases missing from focused target: " + ", ".join(missing))
        self.assertFalse(unexpected, "Non-rejection object-code cases listed in rejection target: " + ", ".join(unexpected))
        self.assertIn(
            "for shape in $(ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES)",
            self.make_text,
            "Object-code rejection cases are not used by a Makefile target",
        )
        self.assertIn(
            "--shape \"$$shape\" --skip-launch --attempts 1",
            self.make_text,
            "Object-code rejection target must run probes with --skip-launch",
        )
        self.assertIn(
            "object_code_dependency_unknown_lowercase_import_index_rejects",
            rejection_cases,
            "Object-code rejection matrix must cover unresolved lowercase high-index dependency imports",
        )
        self.assertIn(
            "object_code_project_unknown_lowercase_import_index_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover bad project OBJ lowercase imports blocking library fallback",
        )
        self.assertIn(
            "object_code_project_second_export_named_symbol_local_export",
            rejection_cases,
            "Object-code rejection matrix must cover named local exports outside the selected object-code range",
        )
        self.assertIn(
            "object_code_library_duplicate_export_rejects",
            rejection_cases,
            "Object-code rejection matrix must cover duplicate exports in loaded library OBJs",
        )
        self.assertIn(
            "object_code_project_duplicate_export_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover duplicate project OBJ exports blocking library fallback",
        )
        self.assertIn(
            "object_code_project_zero_size_export_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover zero-size project OBJ exports blocking library fallback",
        )
        self.assertIn(
            "object_code_project_export_offset_past_machine_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover project OBJ export offsets past machine data blocking library fallback",
        )
        self.assertIn(
            "object_code_project_export_size_overruns_machine_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover project OBJ export sizes overrunning machine data blocking library fallback",
        )
        self.assertIn(
            "object_code_project_reloc_malformed_offset_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover malformed project OBJ relocations blocking library fallback",
        )

    def test_object_code_aggregate_target_runs_all_focused_matrices(self) -> None:
        targets = self._makefile_target_submakes(self.make_text, "vice-action-alink-prg-object-code-matrices")

        self.assertEqual(
            targets,
            [
                "vice-action-alink-prg-object-code-graph-launch-matrix",
                "vice-action-alink-prg-object-code-core-launch-matrix",
                "vice-action-alink-prg-object-code-rejection-matrix",
            ],
        )

    def test_object_code_launch_matrices_clean_stale_vice_before_each_shape(self) -> None:
        for target in (
            "vice-action-alink-prg-object-code-graph-launch-matrix",
            "vice-action-alink-prg-object-code-core-launch-matrix",
        ):
            with self.subTest(target=target):
                body = self._makefile_target_body(self.make_text, target)
                cleanup = "vp.cleanup_stale_vice(settle_seconds=1.0)"
                retry_loop = "for attempt in $$(seq 1 $(ACTION_ALINK_PRG_OBJECT_CODE_PROBE_ATTEMPTS))"
                self.assertIn(cleanup, body)
                self.assertIn(retry_loop, body)
                self.assertLess(
                    body.index(cleanup),
                    body.index(retry_loop),
                    "Object-code launch matrices should clean stale VICE before the first attempt",
                )

    def test_alink_prg_probe_progress_output_is_verbose_gated(self) -> None:
        probe_text = (self.workspace / "udos" / "tools" / "run_action_alink_prg_probe.py").read_text()

        self.assertIn('parser.add_argument("--verbose"', probe_text)
        self.assertIn("def log_progress(verbose: bool", probe_text)
        self.assertNotIn('print({"stage":', probe_text)
        self.assertNotIn('print({"attempt":', probe_text)
        self.assertNotIn("print(result, flush=True)", probe_text)

    def test_alink_prg_probe_quits_vice_before_process_termination(self) -> None:
        probe_text = (self.workspace / "udos" / "tools" / "run_action_alink_prg_probe.py").read_text()

        quit_index = probe_text.index("client.quit_emulator()")
        close_index = probe_text.index("client.close()", quit_index)
        terminate_index = probe_text.index("vp.terminate_process_tree(process)", close_index)

        self.assertLess(quit_index, close_index)
        self.assertLess(close_index, terminate_index)

    def test_alink_prg_probe_mirrors_main_prg_for_linux_host_launch(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "UPPER" / "PROJ3"
            bin_root = project_root / "BIN"
            bin_root.mkdir(parents=True)
            payload = bytes([0x00, 0x10, 0x60])
            (bin_root / "MAIN.PRG").write_bytes(payload)
            (bin_root / "UDOSDIR.TXT").write_text("", encoding="ascii")

            probe.ensure_host_prg_catalog(project_root)

            catalog = (bin_root / "UDOSDIR.TXT").read_text(encoding="ascii")
            self.assertIn("F MAIN.PRG", catalog)
            self.assertEqual((bin_root / "main.prg").read_bytes(), payload)
            self.assertEqual((bin_root / "udosdir.txt").read_text(encoding="ascii"), catalog)

    def test_object_code_graph_matrix_covers_project_second_export_import(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())

        self.assertIn(
            "object_code_project_second_export_import",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ second-export imports before library fallback",
        )
        self.assertIn(
            "object_code_project_second_export_named_symbol_import",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named relocations adding imports",
        )
        self.assertIn(
            "object_code_project_second_export_imports_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover project second-export imports to project-local deps",
        )
        self.assertIn(
            "object_code_project_second_export_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected second-export lettered imports to project deps",
        )
        self.assertIn(
            "object_code_project_second_export_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected project second-export lettered imports to library deps",
        )
        self.assertIn(
            "object_code_project_second_export_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected project second-export lowercase imports to library deps",
        )
        self.assertIn(
            "object_code_project_second_export_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected project second-export lowercase imports to project deps",
        )
        self.assertIn(
            "object_code_project_second_export_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project second-export deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_project_second_export_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover transitive selected second-export project deps",
        )
        self.assertIn(
            "object_code_project_second_export_project_dependency_imports_library_tail",
            graph_shapes,
            "Object-code graph matrix must cover project second-export project deps importing library tails",
        )
        self.assertIn(
            "object_code_project_second_export_transitive_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover transitive selected second-export library deps",
        )
        self.assertIn(
            "object_code_mixed_second_export_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover mixed transitive selected second-export deps",
        )

    def test_object_code_graph_matrix_covers_library_dual_import_dependencies(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())

        self.assertIn(
            "object_code_library_dual_import_project_library_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one library OBJ relocating to project and library deps",
        )
        self.assertIn(
            "object_code_project_dual_import_project_library_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one project OBJ relocating to project and library deps",
        )
        self.assertIn(
            "object_code_mixed_dual_transitive_project_library_closure",
            graph_shapes,
            "Object-code graph matrix must cover mixed root project/library deps with opposite transitive tails",
        )
        self.assertIn(
            "object_code_library_dependency_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover library dependency lettered imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_library_dependency_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover library dependency lowercase imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_dependency_reloc_scan_windowed_imports",
            graph_shapes,
            "Object-code graph matrix must cover dependency relocation scans restored after source-windowed import lookup",
        )
        self.assertIn(
            "object_code_library_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library OBJ relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_imports_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library second-export imports to project-local deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_symbol_import",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named relocations adding imports",
        )
        self.assertIn(
            "object_code_library_second_export_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library second-export deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_library_second_export_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected library second-export lettered imports to project deps",
        )
        self.assertIn(
            "object_code_library_second_export_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected library second-export lettered imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected library second-export lowercase imports to project deps",
        )
        self.assertIn(
            "object_code_library_second_export_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected library second-export lowercase imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_imports_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library second-export imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_transitive_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover transitive selected second-export library deps",
        )
        self.assertIn(
            "object_code_library_second_export_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library selected second-export transitive project deps",
        )
        self.assertIn(
            "object_code_library_second_export_project_dependency_imports_library_tail",
            graph_shapes,
            "Object-code graph matrix must cover library second-export project deps importing library tails",
        )
        self.assertIn(
            "object_code_mixed_second_export_shared_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover mixed second-export imports sharing one library dep",
        )
        self.assertIn(
            "object_code_mixed_second_export_shared_project_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover mixed second-export imports sharing one project dep",
        )
        self.assertIn(
            "object_code_library_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover root-local export relocation from offset root bodies",
        )
        self.assertIn(
            "object_code_library_second_export_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover second-export dependencies relocating to root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_dependency_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover selected second-export deps relocating to root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_dependency_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover selected second-export deps relocating to offset root-local exports",
        )
        self.assertIn(
            "object_code_project_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_transitive_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover transitive dependency relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_mixed_transitive_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover mixed transitive relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_library_project_transitive_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library-to-project transitive root-local relocation",
        )
        self.assertIn(
            "object_code_project_transitive_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project-only transitive root-local relocation",
        )
        self.assertIn(
            "object_code_mixed_shared_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover project and library OBJs sharing one library dep",
        )
        self.assertIn(
            "object_code_root_library_share_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root and library OBJ sharing one library dep",
        )
        self.assertIn(
            "object_code_root_project_share_project_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root and project OBJ sharing one project dep",
        )
        self.assertIn(
            "object_code_root_project_share_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root and project OBJ sharing one library dep",
        )
        self.assertIn(
            "object_code_root_project_library_share_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root, project OBJ, and library OBJ sharing one library dep",
        )
        self.assertIn(
            "object_code_root_project_library_share_project_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root, project OBJ, and library OBJ sharing one project dep",
        )

    def test_object_code_graph_matrix_covers_project_lettered_import_pruning(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())

        self.assertIn(
            "object_code_project_lettered_import_pruned",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ lettered imports without loading pruned deps",
        )
        self.assertIn(
            "object_code_project_lettered_import_call",
            graph_shapes,
            "Object-code graph matrix must cover lettered imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_project_dependency_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover project dependency lettered imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_project_dependency_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover project dependency lettered imports resolving to library OBJs",
        )
        self.assertIn(
            "object_code_project_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project dependency dual lettered imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_library_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library dependency dual lettered imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_lowercase_z_import_call",
            graph_shapes,
            "Object-code graph matrix must cover lowercase high-index OBJ imports",
        )
        self.assertIn(
            "object_code_project_lowercase_z_import_call",
            graph_shapes,
            "Object-code graph matrix must cover lowercase high-index imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_dependency_lowercase_z_import_pruned",
            graph_shapes,
            "Object-code graph matrix must cover lowercase high-index imports in dependency bodies",
        )
        self.assertIn(
            "object_code_project_dependency_lowercase_z_import_pruned",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ lowercase high-index dependency imports",
        )
        self.assertIn(
            "object_code_project_dependency_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover project dependency lowercase imports resolving to project OBJs",
        )

    def test_object_code_graph_matrix_covers_project_dependency_lettered_library_helper(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_lettered_import_library_helper"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/A.OBJ", "LIB/HELPER.OBJ"])
        self.assertEqual(sorted(case["extra_objects"]), ["A.OBJ"])
        for unexpected_path in ("LIB/A.OBJ", "LIB/D0.OBJ", "LIB/D9.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_dependency_dual_lettered_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_dual_lettered_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertEqual(sorted(case["extra_objects"]), ["A.OBJ", "PROJHELPER.OBJ"])
        for unexpected_path in ("LIB/A.OBJ", "LIB/PROJHELPER.OBJ", "LIB/D0.OBJ", "LIB/D9.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_dependency_dual_lettered_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_dependency_dual_lettered_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertEqual(sorted(case["extra_objects"]), ["PROJHELPER.OBJ"])
        for unexpected_path in ("LIB/PROJHELPER.OBJ", "LIB/D0.OBJ", "LIB/D9.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_dependency_lowercase_library_helper(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_lowercase_z_import_pruned"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/A.OBJ", "LIB/HELPER.OBJ"])
        self.assertEqual(sorted(case["extra_objects"]), ["A.OBJ"])
        for unexpected_path in ("LIB/A.OBJ", "LIB/D0.OBJ", "LIB/D34.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_external_back_edge_cycle(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())

        self.assertIn(
            "object_code_external_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover relocations back to an already-loaded library OBJ",
        )
        self.assertIn(
            "object_code_mixed_project_library_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover library relocations back to a project-local OBJ",
        )
        self.assertIn(
            "object_code_mixed_project_offset_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover library relocations back to a sliced project OBJ export",
        )

    def test_object_code_core_matrix_covers_project_large_dependency_page_crossing(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())

        self.assertIn(
            "object_code_split_machine_records",
            core_shapes,
            "Object-code core matrix must cover concatenated split machine-code records",
        )
        self.assertIn(
            "object_code_split_dependency_machine_records",
            core_shapes,
            "Object-code core matrix must cover split dependency machine-code records",
        )
        self.assertIn(
            "object_code_named_symbol_relocations",
            core_shapes,
            "Object-code core matrix must cover symbol-name relocation targets",
        )
        self.assertIn(
            "object_code_named_symbol_relocation_import_closure",
            core_shapes,
            "Object-code core matrix must cover symbol-name relocations adding imports",
        )
        self.assertIn(
            "object_code_named_symbol_dependency_import_closure",
            core_shapes,
            "Object-code core matrix must cover dependency symbol-name relocations adding imports",
        )
        self.assertIn(
            "object_code_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover dependency symbol-name relocations to local exports",
        )
        self.assertIn(
            "object_code_reloc_scan_windowed_imports",
            core_shapes,
            "Object-code core matrix must cover relocation scans restored after source-windowed import lookup",
        )
        self.assertIn(
            "object_code_project_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover page-crossing relocations in project OBJ dependencies",
        )
        self.assertIn(
            "object_code_project_large_dependency_library_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover project large OBJ dependencies that import library tails",
        )
        self.assertIn(
            "object_code_root_second_export_imports_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports importing root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_imports_offset_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports importing offset root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_offset_local_and_library_project_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports importing offset root-local exports plus library/project tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_symbol_import",
            core_shapes,
            "Object-code core matrix must cover selected root exports whose named relocations add imports",
        )
        self.assertIn(
            "object_code_root_second_export_transitive_library_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing transitive library deps",
        )
        self.assertIn(
            "object_code_root_second_export_transitive_project_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing transitive project deps",
        )
        self.assertIn(
            "object_code_root_second_export_project_second_export_library_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through project second-export deps importing library tails",
        )
        self.assertIn(
            "object_code_root_second_export_library_second_export_project_second_export_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through library second-export deps importing project second-export tails",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing mixed project/library deps",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing mixed library/project deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_project_library_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly importing project and library deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_library_project_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly importing library and project deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a shared library dep",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_shared_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a shared project dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one project dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_library_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one project dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_library_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_library_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_library_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one project dep",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_dual_lettered_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_lowercase_z_import_project_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps with high-index project helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_lowercase_z_import_library_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps with high-index library helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_library_dependency_lowercase_z_import_project_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export library deps with high-index project helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_library_dependency_lowercase_z_import_library_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export library deps with high-index library helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_imports_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps importing root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_imports_offset_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps importing offset root-local exports",
        )

    @staticmethod
    def _makefile_object_code_shape_groups(make_text: str) -> dict[str, set[str]]:
        groups: dict[str, set[str]] = {}
        current_group: str | None = None

        for line in make_text.splitlines():
            group_match = re.match(r"^(ACTION_ALINK_PRG_OBJECT_CODE_[A-Z_]*SHAPES)\s*:=", line)
            if group_match:
                current_group = group_match.group(1)
                groups[current_group] = set()

            if current_group is not None:
                groups[current_group].update(re.findall(r"\bobject_code_[A-Za-z0-9_]+", line))
                if not line.rstrip().endswith("\\"):
                    current_group = None

        return groups

    @staticmethod
    def _makefile_object_code_rejection_cases(make_text: str) -> set[str]:
        cases: set[str] = set()
        in_group = False

        for line in make_text.splitlines():
            if re.match(r"^ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES\s*:=", line):
                in_group = True

            if in_group:
                cases.update(re.findall(r"\bobject_code_[A-Za-z0-9_]+", line))
                if not line.rstrip().endswith("\\"):
                    in_group = False

        return cases

    @staticmethod
    def _makefile_target_submakes(make_text: str, target_name: str) -> list[str]:
        target_header = f"{target_name}:"
        in_target = False
        targets: list[str] = []

        for line in make_text.splitlines():
            if line.startswith(target_header):
                in_target = True
                continue
            if in_target and line and not line.startswith(("\t", " ")):
                break
            if not in_target:
                continue
            match = re.match(r"[ \t]*\$\(MAKE\)\s+([A-Za-z0-9_.-]+)", line)
            if match:
                targets.append(match.group(1))

        return targets

    @staticmethod
    def _makefile_target_body(make_text: str, target_name: str) -> str:
        target_header = f"{target_name}:"
        in_target = False
        lines: list[str] = []

        for line in make_text.splitlines():
            if line.startswith(target_header):
                in_target = True
                continue
            if in_target and line and not line.startswith(("\t", " ")):
                break
            if in_target:
                lines.append(line)

        return "\n".join(lines)


if __name__ == "__main__":
    unittest.main()
