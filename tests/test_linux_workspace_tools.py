from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestLinuxWorkspaceTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["bash", str(cls.root / "tools" / "build_linux_tools.sh")],
            cwd=cls.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=1200,
        )
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        cls.tool_dir = Path(result.stdout.strip().splitlines()[-1])

    def run_tool(
        self,
        workspace: Path,
        tool: str,
        *args: str,
        expected_status: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(self.tool_dir / tool), *args],
            cwd=workspace,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(
            result.returncode,
            expected_status,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def run_linked_main(self, project: Path, dump: str) -> dict:
        built = subprocess.run(
            ["bash", str(self.root / "tools" / "build_tool_abi_harness.sh")],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        self.assertEqual(
            built.returncode,
            0,
            msg=f"stdout:\n{built.stdout}\nstderr:\n{built.stderr}",
        )
        services_inc = project / ".test-services.inc"
        services_inc.write_text("", encoding="ascii")
        executed = subprocess.run(
            [
                built.stdout.strip().splitlines()[-1],
                "--prg",
                str(project / "BIN" / "MAIN.PRG"),
                "--workspace",
                str(project),
                "--services-inc",
                str(services_inc),
                "--entry-addr",
                "0x1000",
                "--dump",
                dump,
                "--max-steps",
                "100000",
            ],
            cwd=project,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(
            executed.returncode,
            0,
            msg=f"stdout:\n{executed.stdout}\nstderr:\n{executed.stderr}",
        )
        return json.loads(executed.stdout)

    def test_project_workflow_uses_host_filesystem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            created = self.run_tool(root, "actnew", "demo")
            self.assertEqual(created.stdout, "ACTNEW OK\n")

            project = root / "DEMO"
            self.assertTrue((project / "ACTION.PROJ").is_file())
            self.assertTrue((project / "SRC" / "MAIN.ACT").is_file())
            self.assertTrue((project / "BIN").is_dir())
            self.assertTrue((project / "OBJ").is_dir())
            self.assertFalse((project / "UDOSDIR.TXT").exists())
            self.assertFalse((project / "SRC" / "UDOSDIR.TXT").exists())

            added = self.run_tool(project, "actadd", "worker")
            self.assertEqual(added.stdout, "ACTADD OK\n")
            self.assertIn("WORKER.ACT", (project / "ACTION.PROJ").read_text(encoding="ascii"))
            self.assertEqual(
                (project / "SRC" / "WORKER.ACT").read_text(encoding="ascii"),
                "PROC WORKER()\nENDPROC\n",
            )
            self.assertFalse((project / "SRC" / "UDOSDIR.TXT").exists())

            sources = self.run_tool(project, "actsrc")
            self.assertEqual(sources.stdout.splitlines(), ["MAIN.ACT", "WORKER.ACT"])

            work = self.run_tool(project, "actwork")
            self.assertEqual(
                work.stdout.splitlines(),
                ["PROJECT YES", "SRC YES", "BIN YES", "OBJ YES", "MODULES 2"],
            )

            check = self.run_tool(project, "actchk")
            self.assertIn("ACTCHK OK\n", check.stdout)

    def test_actfile_has_no_255_byte_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            long_source = "PROC MAIN()\n" + ("; comment line\n" * 80) + "ENDPROC\n"
            self.assertGreater(len(long_source), 255)
            (project / "SRC" / "MAIN.ACT").write_text(long_source, encoding="ascii")

            result = self.run_tool(project, "actfile", "main")
            self.assertEqual(result.stdout, long_source)
            self.assertNotIn("TRUNCATED", result.stdout)

    def test_actedit_line_operations_are_linux_side(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"

            self.run_tool(project, "actedit", "main", "replace", "1", "PROC MAIN()")
            self.run_tool(project, "actedit", "main", "insert", "2", "HELPER()")
            self.run_tool(project, "actedit", "main", "append", "RETURN")
            self.run_tool(project, "actedit", "main", "delete", "3")

            source = (project / "SRC" / "MAIN.ACT").read_text(encoding="ascii")
            self.assertEqual(source, "PROC MAIN()\nHELPER()\nRETURN\n")
            printed = self.run_tool(project, "actedit", "main", "print")
            self.assertEqual(printed.stdout, source)
            indexed = self.run_tool(project, "actedit", "main", "index")
            self.assertEqual(indexed.stdout, "ACTEDIT INDEXED\n")
            found = self.run_tool(project, "actedit", "main", "find", "HELPER")
            self.assertEqual(found.stdout, "SRC/MAIN.ACT:2:HELPER()\n")
            symbols = self.run_tool(project, "actedit", "main", "symbols")
            self.assertIn("PROC MAIN SRC/MAIN.ACT:1\n", symbols.stdout)
            self.assertTrue((project / ".action" / "workspace.sqlite3").is_file())
            self.assertFalse((project / "SRC" / "UDOSDIR.TXT").exists())

    def test_linux_filesystem_tools_do_not_need_udos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            write = self.run_tool(root, "actwrite", "one.txt", "hello", "world")
            self.assertEqual(write.stdout, "ACTWRITE OK\n")
            self.assertEqual((root / "one.txt").read_text(encoding="ascii"), "hello world\n")

            mkdir = self.run_tool(root, "actmkdir", "sub")
            self.assertEqual(mkdir.stdout, "ACTMKDIR OK\n")
            self.assertTrue((root / "sub").is_dir())

            copy = self.run_tool(root, "actcopy", "one.txt", "sub/two.txt")
            self.assertEqual(copy.stdout, "ACTCOPY OK\n")
            self.assertEqual((root / "sub" / "two.txt").read_text(encoding="ascii"), "hello world\n")

            directory = self.run_tool(root, "actdir")
            self.assertIn("F one.txt", directory.stdout)
            self.assertIn("D sub", directory.stdout)

            move = self.run_tool(root, "actmove", "sub/two.txt", "sub/three.txt")
            self.assertEqual(move.stdout, "ACTMOVE OK\n")
            self.assertFalse((root / "sub" / "two.txt").exists())
            self.assertTrue((root / "sub" / "three.txt").is_file())

            tree = self.run_tool(root, "acttree")
            self.assertIn("F one.txt", tree.stdout)
            self.assertIn("F sub/three.txt", tree.stdout)

            delete = self.run_tool(root, "actdel", "sub/three.txt")
            self.assertEqual(delete.stdout, "ACTDEL OK\n")
            self.assertFalse((root / "sub" / "three.txt").exists())

            rmdir = self.run_tool(root, "actrmdir", "sub")
            self.assertEqual(rmdir.stdout, "ACTRMDIR OK\n")
            self.assertFalse((root / "sub").exists())
            self.assertFalse((root / "UDOSDIR.TXT").exists())

    def test_recursive_linux_filesystem_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "nested").mkdir(parents=True)
            (root / "src" / "nested" / "file.txt").write_text("payload\n", encoding="ascii")

            copied = self.run_tool(root, "xcopy", "src", "dst")
            self.assertEqual(copied.stdout, "XCOPY OK\n")
            self.assertEqual((root / "dst" / "nested" / "file.txt").read_text(encoding="ascii"), "payload\n")

            removed = self.run_tool(root, "deltree", "dst")
            self.assertEqual(removed.stdout, "DELTREE OK\n")
            self.assertFalse((root / "dst").exists())

            info = self.run_tool(root, "actinfo")
            self.assertIn("ACTIONC64U IDUN LINUX TOOLS", info.stdout)

    def test_actchk_reports_missing_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").unlink()

            result = self.run_tool(project, "actchk", expected_status=1)
            self.assertIn("MISSING 1\n", result.stdout)
            self.assertIn("MISSING MAIN.ACT\n", result.stdout)
            self.assertIn("ACTCHK BROKEN\n", result.stdout)

    def test_act2save_compatibility_name_uses_real_linker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "OBJ" / "MAIN.OBJ").write_text("OBJ1\nx MAIN 0 1\nb M\nm 60\n", encoding="ascii")

            result = self.run_tool(project, "act2save")
            self.assertEqual(result.stdout, "ALINK OK\nACT2SAVE OK\n")
            self.assertEqual((project / "BIN" / "MAIN.PRG").read_bytes(), bytes([0x00, 0x10, 0x60]))

    def test_actc_alink_write_direct_prg_without_udos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"

            compiled = self.run_tool(project, "actc", "main")
            self.assertEqual(compiled.stdout, "ACTC OK\n")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("OBJ1\n", obj_text)
            self.assertIn("x MAIN 0 1\n", obj_text)
            self.assertIn("m 60\n", obj_text)

            linked = self.run_tool(project, "alink", "main")
            self.assertEqual(linked.stdout, "ALINK OK\n")
            self.assertEqual((project / "BIN" / "MAIN.PRG").read_bytes(), bytes([0x00, 0x10, 0x60]))
            self.assertTrue((project / "BIN" / "MAIN.DBG").is_file())

            debug = self.run_tool(project, "actdbg", "main")
            self.assertIn("ACTDBG INFO\n", debug.stdout)
            self.assertIn("MODULE MAIN\n", debug.stdout)
            self.assertIn("LOAD 4096\n", debug.stdout)
            self.assertIn("SIZE 1\n", debug.stdout)
            self.assertIn("e 4096\n", debug.stdout)
            self.assertIn("f 0 SRC/MAIN.ACT\n", debug.stdout)
            self.assertIn("l 4096 0 1\n", debug.stdout)
            self.assertIn("y 4096 1 MAIN\n", debug.stdout)

            line = self.run_tool(project, "actdbg", "main", "line", "1")
            self.assertEqual(line.stdout, "ADDRESS 4096 SRC/MAIN.ACT:1\n")
            source = self.run_tool(project, "actdbg", "main", "source", "$1000")
            self.assertEqual(source.stdout, "SOURCE 4096 SRC/MAIN.ACT:1\n")
            symbols = self.run_tool(project, "actdbg", "main", "symbols", "MAIN")
            self.assertIn("SYMBOL 4096 1 MAIN\n", symbols.stdout)

            stored = self.run_tool(project, "actdbg", "main", "break", "1")
            self.assertIn(" 4096 SRC/MAIN.ACT:1\n", stored.stdout)
            breakpoint_id = stored.stdout.split()[1]
            listed = self.run_tool(project, "actdbg", "main", "breaks")
            self.assertIn(
                f"BREAKPOINT {breakpoint_id} 4096 SRC/MAIN.ACT:1 ENABLED\n",
                listed.stdout,
            )
            cleared = self.run_tool(
                project, "actdbg", "main", "clear", breakpoint_id
            )
            self.assertEqual(
                cleared.stdout, f"BREAKPOINT CLEARED {breakpoint_id}\n"
            )
            self.assertTrue((project / ".action" / "debug.sqlite3").is_file())

            monitor = self.run_tool(project, "actmon")
            self.assertIn("ACTIONC64U MONITOR\n", monitor.stdout)
            self.assertIn("PROJECT YES\n", monitor.stdout)
            self.assertIn("MAIN.ACT\n", monitor.stdout)
            self.assertIn("COMMANDS actnew actadd actedit actc alink actdbg actchk\n", monitor.stdout)

    def test_actc_alink_patch_local_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC HELPER()\nRETURN\nENDPROC\nPROC MAIN()\nHELPER()\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertEqual(prg[:2], bytes([0x00, 0x10]))
            self.assertEqual(prg[2:5], bytes([0x20, 0x04, 0x10]))
            self.assertEqual(prg[5:], bytes([0x60, 0x60]))

    def test_actc_module_globals_are_shared_across_procedures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            (shared_lib / "RT_PRINT_I.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(
                    encoding="ascii"
                ),
                encoding="ascii",
            )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "MODULE MAIN",
                        "CARD counter",
                        "PROC BUMP()",
                        "counter = counter + 1",
                        "RETURN",
                        "PROC MAIN()",
                        "counter = 5 ; inline comments are ignored",
                        "BUMP()",
                        "PrintI(counter)",
                        "RETURN",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertEqual(obj_text.count("x MAIN_COUNTER_LO "), 1)
            self.assertEqual(obj_text.count("x MAIN_COUNTER_HI "), 1)
            self.assertIn("x BUMP ", obj_text)
            self.assertGreaterEqual(obj_text.count("x MAIN_COUNTER_LO"), 1)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0x20]), prg)
            self.assertIn(bytes.fromhex("85FB86FC"), prg)

    def test_actc_bracket_initializers_become_linked_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "MODULE MAIN",
                        "BYTE flag=[$7F]",
                        "CARD count=[$1234]",
                        "PROC MAIN()",
                        "BYTE local=[2 + 3]",
                        "flag = local + 0",
                        "count = count + 0",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x MAIN_FLAG_LO", obj_text)
            self.assertIn("x MAIN_COUNT_HI", obj_text)
            self.assertIn("x MAIN_LOCAL_LO", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertTrue(prg.endswith(bytes([0x7F, 0x34, 0x12, 0x05])))

    def test_actc_address_bound_variables_use_direct_c64_addresses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "MODULE MAIN",
                        "BYTE border=$D020",
                        "CARD clock=$00A0",
                        "PROC MAIN()",
                        "BYTE copy",
                        "border = 6",
                        "clock = $1234",
                        "copy = border + 0",
                        "copy = copy + border",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertNotIn("MAIN_BORDER_LO", obj_text)
            self.assertNotIn("MAIN_CLOCK_LO", obj_text)
            self.assertIn("8D20D0", obj_text)
            self.assertIn("8DA000", obj_text)
            self.assertIn("8EA100", obj_text)
            self.assertIn("AD20D0", obj_text)
            self.assertIn("6D20D0", obj_text)
            self.run_tool(project, "alink", "main")

    def test_actc_rejects_declaration_binding_ranges(self) -> None:
        cases = {
            "byte_initializer": (
                "MODULE MAIN\nBYTE x=[256]\nPROC MAIN()\nENDPROC\n",
                "INITIALIZER RANGE LINE 2: X\n",
            ),
            "card_address": (
                "MODULE MAIN\nCARD x=$FFFF\nPROC MAIN()\nENDPROC\n",
                "ADDRESS RANGE LINE 2: X\n",
            ),
        }
        for name, (source, expected_error) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "SRC" / "MAIN.ACT").write_text(source, encoding="ascii")
                result = self.run_tool(project, "actc", "main", expected_status=1)
                self.assertEqual(result.stderr, expected_error)

    def test_actc_arrays_pointers_strings_and_local_procedure_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE main\n"
                'BYTE ARRAY greeting="HI"\n'
                "BYTE ARRAY bytes(4)=[1 2 3 4]\n"
                "CARD ARRAY words(3)=[256 512 768]\n"
                "BYTE value\n"
                "CARD wide\n"
                "BYTE POINTER ptr\n"
                "PROC consume(BYTE n,CARD w,BYTE ARRAY text,BYTE POINTER out)\n"
                "out^=n\n"
                "bytes(2)=out^+1\n"
                "words(1)=w+bytes(2)\n"
                "PrintE(text)\n"
                "RETURN\n"
                "ENDPROC\n"
                "PROC main()\n"
                "ptr=@value\n"
                "consume(7,500,greeting,ptr)\n"
                'consume(9,600,"OK",ptr)\n'
                "wide=words(1)\n"
                "RETURN\n"
                "ENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            for symbol in (
                "MAIN_GREETING_DATA",
                "MAIN_BYTES_DATA",
                "MAIN_WORDS_DATA",
                "CONSUME_N_LO",
                "CONSUME_W_HI",
                "CONSUME_TEXT_LO",
                "CONSUME_OUT_HI",
            ):
                self.assertIn(symbol, obj_text)
            self.assertIn("\nx CONSUME ", obj_text)
            self.assertIn("024849", obj_text)
            self.assertIn("024F4B", obj_text)
            self.assertNotIn("\nu ", obj_text)

            self.run_tool(project, "alink", "main")
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("MAIN", debug)
            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes()[:2],
                bytes([0x00, 0x10]),
            )

    def test_actc_real_arrays_pointers_and_indirect_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in (
                "rt_f_add.obj",
                "rt_f_addsub_core.obj",
                "rt_f_special.obj",
                "rt_f_cmp.obj",
                "rt_print_f.obj",
                "rt_s_to_f.obj",
            ):
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "REAL ARRAY samples(3)=[1.25,2.5,3.75]\n"
                "PROC CopyAndAdd(REAL ARRAY source,REAL POINTER destination)\n"
                "destination^=source(1)+source(0)\n"
                "RETURN\n"
                "ENDPROC\n"
                "PROC MAIN()\n"
                "REAL ARRAY local(2)=[4.0,5.5]\n"
                "REAL result\n"
                "REAL POINTER ptr\n"
                "ptr=@result\n"
                "CopyAndAdd(samples,ptr)\n"
                "local(1)=result+local(0)\n"
                "PrintRE(local(1))\n"
                "IF local(1)>samples(2) THEN\n"
                "PrintRE(ptr^)\n"
                "FI\n"
                "RETURN\n"
                "ENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            for symbol in (
                "MAIN_SAMPLES_DATA",
                "MAIN_SAMPLES_PTR_LO",
                "MAIN_LOCAL_DATA",
                "MAIN_RESULT_B0",
                "MAIN_PTR_LO",
                "COPYANDADD_SOURCE_LO",
                "COPYANDADD_DESTINATION_HI",
            ):
                self.assertIn(symbol, obj_text)
            self.assertIn("0000A03F0000204000007040", obj_text)
            self.assertIn("\nu RT_F_ADD\n", obj_text)
            self.assertIn("\nu RT_F_CMP\n", obj_text)
            self.assertIn("\nu RT_PRINT_F\n", obj_text)

            self.run_tool(project, "alink", "main")
            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes()[:2],
                bytes([0x00, 0x10]),
            )
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("COPYANDADD", debug)
            self.assertIn("RT_F_ADD", debug)

    def test_actc_user_functions_return_word_and_real_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in (
                "rt_f_add.obj",
                "rt_f_addsub_core.obj",
                "rt_f_special.obj",
                "rt_i_mul.obj",
                "rt_i_to_f.obj",
                "rt_print_f.obj",
                "rt_print_i.obj",
                "rt_s_to_f.obj",
            ):
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "CARD FUNC Square(CARD value)\n"
                "RETURN (value*value)\n"
                "BYTE FUNC Limit(BYTE value)\n"
                "IF value>10 THEN\n"
                "RETURN(10)\n"
                "FI\n"
                "RETURN (value)\n"
                "INT FUNC Negate(INT value)\n"
                "RETURN (-value)\n"
                "REAL FUNC Twice(REAL value)\n"
                "RETURN (value+value)\n"
                "PROC MAIN()\n"
                "CARD total\n"
                "INT signed\n"
                "REAL doubled\n"
                "total=Square(9)+Limit(12)\n"
                "signed=Negate(7)\n"
                "doubled=Twice(1.5)+REAL(total)\n"
                "PrintIE(total)\n"
                "PrintIE(signed)\n"
                "PrintRE(doubled)\n"
                "RETURN\n"
                "ENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            for function in ("SQUARE", "LIMIT", "NEGATE", "TWICE"):
                self.assertIn(f"\nx {function} ", obj_text)
                self.assertNotIn(f"\nu {function}\n", obj_text)
            for symbol in (
                "SQUARE_VALUE_HI",
                "LIMIT_VALUE_LO",
                "NEGATE_VALUE_HI",
                "TWICE_VALUE_B0",
                "TWICE_RETURN_B0",
                "TWICE_RETURN_PTR_LO",
            ):
                self.assertIn(symbol, obj_text)
            self.assertIn("\nu RT_I_MUL\n", obj_text)
            self.assertIn("\nu RT_F_ADD\n", obj_text)
            self.assertIn("\nu RT_I_TO_F\n", obj_text)

            self.run_tool(project, "alink", "main")
            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes()[:2],
                bytes([0x00, 0x10]),
            )
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            for function in ("SQUARE", "LIMIT", "NEGATE", "TWICE"):
                self.assertIn(function, debug)

    def test_actc_direct_recursive_function_preserves_caller_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE MAIN\n"
                "BYTE marker=$03D0\n"
                "CARD FUNC SumDown(CARD value)\n"
                "CARD saved\n"
                "saved=value\n"
                "IF value=0 THEN\n"
                "RETURN (0)\n"
                "FI\n"
                "RETURN (saved+SumDown(value-1))\n"
                "PROC MAIN()\n"
                "marker=SumDown(5)\n"
                "RETURN\n"
                "ENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")

            summary = self.run_linked_main(project, "0x03D0:1")
            self.assertTrue(summary["exited"])
            self.assertFalse(summary["hit_limit"])
            self.assertEqual(summary["dumps"]["0x03D0"], [15])
            self.assertEqual(summary["registers"]["sp"], 0xFF)

    def test_actc_direct_recursive_real_function_preserves_caller_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in (
                "rt_f_add.obj",
                "rt_f_addsub_core.obj",
                "rt_f_special.obj",
                "rt_f_cmp.obj",
                "rt_f_sub.obj",
            ):
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE MAIN\n"
                "REAL result=$03D0\n"
                "REAL FUNC SumDown(REAL value)\n"
                "REAL saved\n"
                "saved=value\n"
                "IF value=0.0 THEN\n"
                "RETURN (0.0)\n"
                "FI\n"
                "RETURN (saved+SumDown(value-1.0))\n"
                "PROC MAIN()\n"
                "result=SumDown(3.0)\n"
                "RETURN\n"
                "ENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")

            summary = self.run_linked_main(project, "0x03D0:4")
            self.assertTrue(summary["exited"])
            self.assertFalse(summary["hit_limit"])
            self.assertEqual(summary["dumps"]["0x03D0"], [0x00, 0x00, 0xC0, 0x40])
            self.assertEqual(summary["registers"]["sp"], 0xFF)

    def test_actc_mutual_recursion_preserves_each_caller_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE MAIN\n"
                "BYTE marker=$03D0\n"
                "CARD FUNC EvenSum(CARD value)\n"
                "CARD saved\n"
                "saved=value\n"
                "IF value=0 THEN\n"
                "RETURN (0)\n"
                "FI\n"
                "RETURN (saved+OddSum(value-1))\n"
                "CARD FUNC OddSum(CARD value)\n"
                "CARD saved\n"
                "saved=value\n"
                "IF value=0 THEN\n"
                "RETURN (0)\n"
                "FI\n"
                "RETURN (saved+EvenSum(value-1))\n"
                "PROC MAIN()\n"
                "marker=EvenSum(5)\n"
                "RETURN\n"
                "ENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")

            summary = self.run_linked_main(project, "0x03D0:1")
            self.assertTrue(summary["exited"])
            self.assertFalse(summary["hit_limit"])
            self.assertEqual(summary["dumps"]["0x03D0"], [15])
            self.assertEqual(summary["registers"]["sp"], 0xFF)

    def test_actc_diagnoses_invalid_function_returns(self) -> None:
        cases = {
            "missing": (
                "BYTE FUNC Missing()\nBYTE value\nPROC MAIN()\nRETURN\nENDPROC\n",
                "MISSING FUNC RETURN LINE 1: MISSING\n",
            ),
            "bare": (
                "BYTE FUNC Broken()\nRETURN\nPROC MAIN()\nRETURN\nENDPROC\n",
                "FUNC RETURN VALUE REQUIRED LINE 2\n",
            ),
            "proc_value": (
                "PROC MAIN()\nRETURN(1)\nENDPROC\n",
                "PROC RETURN HAS VALUE LINE 2\n",
            ),
        }
        for name, (source, expected_error) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "SRC" / "MAIN.ACT").write_text(
                    source,
                    encoding="ascii",
                )
                result = self.run_tool(
                    project,
                    "actc",
                    "main",
                    expected_status=1,
                )
                self.assertEqual(result.stderr, expected_error)
                self.assertFalse((project / "OBJ" / "MAIN.OBJ").exists())

    def test_actc_rejects_array_storage_beyond_c64_address_space(self) -> None:
        for declaration in (
            "BYTE ARRAY huge(65536)",
            "REAL ARRAY huge(16384)",
        ):
            with self.subTest(declaration=declaration), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "SRC" / "MAIN.ACT").write_text(
                    f"PROC MAIN()\n{declaration}\nRETURN\nENDPROC\n",
                    encoding="ascii",
                )

                result = self.run_tool(project, "actc", "main", expected_status=1)
                self.assertEqual(result.stderr, "ARRAY SIZE RANGE LINE 2: HUGE\n")
                self.assertFalse((project / "OBJ" / "MAIN.OBJ").exists())

    def test_actc_real_expressions_select_only_referenced_helpers(self) -> None:
        runtime_names = tuple(
            path.name
            for path in (self.root / "src" / "runtime" / "modules").glob("rt_*f*.obj")
            if path.name
            in {
                "rt_f_abs.obj",
                "rt_f_add.obj",
                "rt_f_addsub_core.obj",
                "rt_f_special.obj",
                "rt_f_cmp.obj",
                "rt_f_div.obj",
                "rt_f_mul.obj",
                "rt_f_sqrt.obj",
                "rt_f_sub.obj",
                "rt_f_to_i.obj",
                "rt_i_to_f.obj",
                "rt_print_f.obj",
                "rt_s_to_f.obj",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in runtime_names:
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD n",
                        "REAL a=[1.5],b=[2.0],sum,difference,product,quotient,root,absolute,fromint",
                        "n = 3",
                        "sum = a + b",
                        "difference = a - b",
                        "product = a * b",
                        "quotient = a / b",
                        "root = FSqrt(b)",
                        "absolute = FAbs(difference)",
                        "fromint = REAL(n)",
                        "IF sum > a THEN",
                        "PrintRE(sum)",
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            for symbol in (
                "RT_F_ADD",
                "RT_F_SUB",
                "RT_F_MUL",
                "RT_F_DIV",
                "RT_F_SQRT",
                "RT_F_ABS",
                "RT_I_TO_F",
                "RT_F_CMP",
                "RT_PRINT_F",
            ):
                self.assertIn(f"\nu {symbol}\n", obj_text)
            self.assertNotIn("\nu RT_F_TO_I\n", obj_text)
            self.assertNotIn("\nu RT_S_TO_F\n", obj_text)
            self.assertIn("x MAIN_A_B0", obj_text)
            self.assertIn("x MAIN___REAL_TEMP_", obj_text)
            self.run_tool(project, "alink", "main")

            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            for symbol in (
                "RT_F_ADD",
                "RT_F_SUB",
                "RT_F_MUL",
                "RT_F_DIV",
                "RT_F_SQRT",
                "RT_F_ABS",
                "RT_I_TO_F",
                "RT_F_CMP",
                "RT_PRINT_F",
            ):
                self.assertIn(symbol, debug)
            self.assertNotIn("RT_S_TO_F", debug)

    def test_actc_constant_real_expression_and_condition_fold_without_math_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            (shared_lib / "RT_PRINT_F.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_f.obj").read_text(
                    encoding="ascii"
                ),
                encoding="ascii",
            )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "REAL x",
                        "x = (1.5 + 2.25) * 2",
                        "IF 1.0 < 2.0 THEN",
                        "PrintRE(x)",
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("\nu RT_PRINT_F\n", obj_text)
            for symbol in ("RT_F_ADD", "RT_F_MUL", "RT_F_CMP"):
                self.assertNotIn(f"\nu {symbol}\n", obj_text)
            self.assertIn("0000F040", obj_text)
            self.run_tool(project, "alink", "main")

    def test_actc_int_signed_comparison_and_real_bridges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in ("rt_s_to_f.obj", "rt_f_to_i.obj"):
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "INT signed=[-7],converted",
                        "REAL source=[3.75],fromsigned",
                        "fromsigned = REAL(signed)",
                        "converted = INT(source)",
                        "IF signed < 0 THEN",
                        'PrintE("NEG")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("\nu RT_S_TO_F\n", obj_text)
            self.assertIn("\nu RT_F_TO_I\n", obj_text)
            self.assertIn("49808502", obj_text)
            self.assertIn("F9FF", obj_text)
            self.run_tool(project, "alink", "main")

            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("RT_S_TO_F", debug)
            self.assertIn("RT_F_TO_I", debug)

    def test_actc_rejects_call_arguments_until_their_abi_is_lowered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nUnknownHelper(5,2,65)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            result = self.run_tool(project, "actc", "main", expected_status=1)
            self.assertEqual(result.stderr, "UNSUPPORTED CALL ARGS LINE 2: UNKNOWNHELPER\n")
            self.assertFalse((project / "OBJ" / "MAIN.OBJ").exists())

    def test_gfx_cell_calls_lower_arguments_and_link_standalone_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in ("rt_gfx_screen_cell.obj", "rt_gfx_color_cell.obj"):
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(encoding="ascii"),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                (self.root / "examples" / "gfx1_demo.act").read_text(encoding="ascii"),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("\nu RT_GFX_SCREEN_CELL\n", obj_text)
            self.assertIn("\nu RT_GFX_COLOR_CELL\n", obj_text)
            self.assertIn("MAIN_EXPR_", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes.fromhex("85048405A9008502A9048503"), prg)
            self.assertIn(bytes.fromhex("850498290F8505A9008502A9D8"), prg)
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("RT_GFX_SCREEN_CELL", debug)
            self.assertIn("RT_GFX_COLOR_CELL", debug)

    def test_complete_gfx1_procedure_family_is_link_selectable(self) -> None:
        runtime_names = (
            "rt_gfx_vic_bank.obj",
            "rt_gfx_bgcolor.obj",
            "rt_gfx_bordercolor.obj",
            "rt_gfx_screen_base.obj",
            "rt_gfx_bitmap_base.obj",
            "rt_gfx_screen_cell.obj",
            "rt_gfx_color_cell.obj",
            "rt_gfx_screen_copy.obj",
            "rt_gfx_color_copy.obj",
            "rt_gfx_bitmap_fill.obj",
            "rt_gfx_bitmap_copy.obj",
            "rt_gfx_bitmap_on.obj",
            "rt_gfx_bitmap_off.obj",
            "rt_gfx_mbitmap_on.obj",
            "rt_gfx_mbitmap_off.obj",
        )
        source_lines = (
            "VicBank(1)",
            "BgColor(6)",
            "BorderColor(14)",
            "ScreenBase($0400)",
            "BitmapBase($2000)",
            "ScreenCell(5,2,65)",
            "ColorCell(5,2,10)",
            "ScreenCopy($3000)",
            "ColorCopy($3400)",
            "BitmapFill(0)",
            "BitmapCopy($4000)",
            "BitmapOn()",
            "BitmapOff()",
            "MBitmapOn()",
            "MBitmapOff()",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in runtime_names:
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(encoding="ascii"),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\n" + "\n".join(source_lines) + "\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            for name in runtime_names:
                symbol = name.removesuffix(".obj").upper()
                self.assertIn(f"\nu {symbol}\n", obj_text)
            self.run_tool(project, "alink", "main")

            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            for name in runtime_names:
                self.assertIn(name.removesuffix(".obj").upper(), debug)

    def test_input1_demo_lowers_byte_function_results_and_transitive_state(self) -> None:
        runtime_names = (
            "rt_joy.obj",
            "rt_js.obj",
            "rt_jp.obj",
            "rt_jb1.obj",
            "rt_jb2.obj",
            "rt_ms.obj",
            "rt_mp.obj",
            "rt_mseen.obj",
            "rt_mx.obj",
            "rt_my.obj",
            "rt_mb.obj",
            "rt_mb1.obj",
            "rt_mb2.obj",
        )
        direct_helpers = (
            "RT_JOY",
            "RT_JP",
            "RT_JB1",
            "RT_JB2",
            "RT_MP",
            "RT_MSEEN",
            "RT_MX",
            "RT_MY",
            "RT_MB",
            "RT_MB1",
            "RT_MB2",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in runtime_names:
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(encoding="ascii"),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                (self.root / "examples" / "input1_demo.act").read_text(encoding="ascii"),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            for helper in direct_helpers:
                self.assertIn(f"\nu {helper}\n", obj_text)
            self.assertNotIn("\nu RT_JS\n", obj_text)
            self.assertNotIn("\nu RT_MS\n", obj_text)
            self.assertIn("A200", obj_text)
            self.run_tool(project, "alink", "main")

            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            for name in runtime_names:
                self.assertIn(name.removesuffix(".obj").upper(), debug)
            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes.fromhex("AD19D4"), prg)
            self.assertIn(bytes.fromhex("AD1AD4"), prg)

    def test_input_runtime_executes_c64_two_button_and_1351_semantics(self) -> None:
        generated = subprocess.run(
            ["python3", str(self.root / "tools" / "generate_input_runtime.py"), "--check"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(generated.returncode, 0, msg=generated.stdout + generated.stderr)

        runtime_names = (
            "rt_joy.obj",
            "rt_js.obj",
            "rt_jp.obj",
            "rt_jb1.obj",
            "rt_jb2.obj",
            "rt_ms.obj",
            "rt_mp.obj",
            "rt_mseen.obj",
            "rt_mx.obj",
            "rt_my.obj",
            "rt_mb.obj",
            "rt_mb1.obj",
            "rt_mb2.obj",
        )
        outputs = "".join(f"BYTE O{index:02d}=${0x03D0 + index:04X}\n" for index in range(30))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in runtime_names:
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE MAIN\n"
                "BYTE CIAA=$DC00\n"
                "BYTE CIAB=$DC01\n"
                "BYTE POTX=$D419\n"
                "BYTE POTY=$D41A\n"
                + outputs
                + "PROC MAIN()\n"
                "CIAA=$FF\n"
                "CIAB=$FF\n"
                "POTX=$15\n"
                "POTY=$A8\n"
                "O00=MousePoll(1)\n"
                "O01=MouseSeen()\n"
                "O02=MouseX()\n"
                "O03=MouseY()\n"
                "CIAB=$EE\n"
                "POTX=$9B\n"
                "POTY=$A5\n"
                "O04=MousePoll(1)\n"
                "O05=MouseX()\n"
                "O06=MouseY()\n"
                "O07=MouseBtn()\n"
                "O08=MouseBtn1()\n"
                "O09=MouseBtn2()\n"
                "O10=MouseSeen()\n"
                "CIAA=$FF\n"
                "POTX=$FC\n"
                "POTY=$83\n"
                "O11=MousePoll(2)\n"
                "O12=MouseX()\n"
                "O13=MouseY()\n"
                "CIAA=$EE\n"
                "POTX=$05\n"
                "POTY=$FE\n"
                "O14=MousePoll(2)\n"
                "O15=MouseX()\n"
                "O16=MouseY()\n"
                "O17=MouseBtn()\n"
                "O18=MouseSeen()\n"
                "CIAB=$FF\n"
                "POTX=$9B\n"
                "POTY=$A5\n"
                "O19=MousePoll(1)\n"
                "O20=MouseX()\n"
                "O21=MouseY()\n"
                "O22=MouseBtn()\n"
                "O23=MouseSeen()\n"
                "CIAA=$FF\n"
                "POTX=$FF\n"
                "O24=JoySeen(2)\n"
                "CIAA=$EA\n"
                "POTX=$40\n"
                "O25=Joy(2)\n"
                "O26=JoySeen(2)\n"
                "O27=JoyBtn1(2)\n"
                "O28=JoyBtn2(2)\n"
                "CIAB=$F5\n"
                "POTX=$FF\n"
                "O29=Joy(1)\n"
                "RETURN\n"
                "ENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")
            summary = self.run_linked_main(project, "0x03D0:30")

            self.assertTrue(summary["exited"])
            self.assertFalse(summary["hit_limit"])
            self.assertEqual(
                summary["dumps"]["0x03D0"],
                [
                    0, 0, 0, 0,
                    1, 3, 2, 3, 1, 1, 1,
                    0, 0, 0,
                    1, 4, 2, 3, 1,
                    1, 3, 2, 0, 1,
                    0, 0x35, 1, 1, 1, 0x0A,
                ],
            )
            self.assertEqual(summary["registers"]["sp"], 0xFF)

    def test_complete_sidspr1_family_uses_register_and_carry_abis(self) -> None:
        runtime_names = tuple(
            sorted(
                path.name
                for pattern in ("rt_sid_*.obj", "rt_sprite_*.obj")
                for path in (self.root / "src" / "runtime" / "modules").glob(pattern)
            )
        )
        source_lines = (
            "BYTE hit,hitbg,osc,env",
            "PROC MAIN()",
            "hit=SpriteHit()",
            "hitbg=SpriteHitBg()",
            "osc=SidOsc3()",
            "env=SidEnv3()",
            "SpriteOn(1)",
            "SpriteOff(1)",
            "SpritePos(1,$0101,50)",
            "SpritePtr(1,128)",
            "SpriteData(1,$2000)",
            "SpriteColor(1,10)",
            "SpriteMC(1,1)",
            "SpriteXExp(1,1)",
            "SpriteYExp(1,1)",
            "SpritePrio(1,SPR_BACK)",
            "SetSpriteMC(5,7)",
            "SidFreq(1,$1234)",
            "SidPulse(1,$0800)",
            "SidWave(1,SID_TRI+SID_SAW)",
            "SidAD(1,$24)",
            "SidSR(1,$A8)",
            "SidOn(1)",
            "SidOff(1)",
            "SidVol(15)",
            "SidCutoff($345)",
            "SidRes(8)",
            "SidMode(SID_LOW+SID_HIGH)",
            "SidRoute(3)",
            "SidRst()",
            "RETURN",
            "ENDPROC",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in runtime_names:
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(encoding="ascii"),
                    encoding="ascii",
                )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE MAIN\n" + "\n".join(source_lines) + "\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("\nu RT_SPRITE_POS\n", obj_text)
            self.assertIn("\nu RT_SID_RST\n", obj_text)
            self.assertNotIn("\nu RT_SID_STATE\n", obj_text)
            self.assertIn("4AAD", obj_text)
            self.run_tool(project, "alink", "main")

            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            for name in runtime_names:
                self.assertIn(name.removesuffix(".obj").upper(), debug)
            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes.fromhex("AD1ED060"), prg)
            self.assertIn(bytes.fromhex("A900A2189D00D4"), prg)

    def test_shipped_simple_examples_compile_and_link_on_linux(self) -> None:
        for example in ("hello.act", "if.act", "math.act"):
            with self.subTest(example=example), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shared_lib = root / "LIB"
                shared_lib.mkdir()
                (shared_lib / "RT_PRINT_I.OBJ").write_text(
                    (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "SRC" / "MAIN.ACT").write_text(
                    (self.root / "examples" / example).read_text(encoding="ascii"),
                    encoding="ascii",
                )

                self.run_tool(project, "actc", "main")
                self.run_tool(project, "alink", "main")
                self.assertGreater((project / "BIN" / "MAIN.PRG").stat().st_size, 3)

    def test_shipped_real_examples_compile_and_link_on_linux(self) -> None:
        runtime_names = (
            "rt_f_abs.obj",
            "rt_f_add.obj",
            "rt_f_addsub_core.obj",
            "rt_f_special.obj",
            "rt_f_cmp.obj",
            "rt_f_div.obj",
            "rt_f_mul.obj",
            "rt_f_sqrt.obj",
            "rt_f_sub.obj",
            "rt_f_to_i.obj",
            "rt_i_to_f.obj",
            "rt_print_f.obj",
            "rt_s_to_f.obj",
        )
        for example in (
            "real_demo.act",
            "real_math.act",
            "real_cmp.act",
            "math1_demo.act",
        ):
            with self.subTest(example=example), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shared_lib = root / "LIB"
                shared_lib.mkdir()
                for name in runtime_names:
                    (shared_lib / name.upper()).write_text(
                        (self.root / "src" / "runtime" / "modules" / name).read_text(
                            encoding="ascii"
                        ),
                        encoding="ascii",
                    )
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "SRC" / "MAIN.ACT").write_text(
                    (self.root / "examples" / example).read_text(encoding="ascii"),
                    encoding="ascii",
                )

                self.run_tool(project, "actc", "main")
                self.run_tool(project, "alink", "main")
                self.assertGreater((project / "BIN" / "MAIN.PRG").stat().st_size, 3)

    def test_alink_loads_external_object_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nHELPER()\nRETURN\nENDPROC\n",
                encoding="ascii",
            )
            (project / "OBJ" / "HELPER.OBJ").write_text(
                "OBJ1\nx HELPER 0 1\nb M\nm 60\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertEqual(prg[:2], bytes([0x00, 0x10]))
            self.assertEqual(prg[2:5], bytes([0x20, 0x04, 0x10]))
            self.assertEqual(prg[5:], bytes([0x60, 0x60]))

    def test_alink_deduplicates_mixed_obj_lib_diamond_with_back_edge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (root / "LIB").mkdir()
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\n"
                "x MAIN 0 7\n"
                "b u0u1M\n"
                "u A\n"
                "u B\n"
                "m 20 00 00 20 00 00 60\n"
                "r 1 u0\n"
                "r 4 u1\n",
                encoding="ascii",
            )
            (project / "OBJ" / "A.OBJ").write_text(
                "OBJ1\nx A 0 4\nb u0M\nu C\nm 20 00 00 60\nr 1 u0\n",
                encoding="ascii",
            )
            (project / "LIB" / "B.OBJ").write_text(
                "OBJ1\nx B 0 4\nb u0M\nu C\nm 20 00 00 60\nr 1 u0\n",
                encoding="ascii",
            )
            (root / "LIB" / "C.OBJ").write_text(
                "OBJ1\nx C 0 4\nb u0M\nu A\nm 20 00 00 60\nr 1 u0\n",
                encoding="ascii",
            )

            self.run_tool(project, "alink", "main")

            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes(),
                bytes.fromhex(
                    "0010"
                    "200710200B1060"
                    "200F1060"
                    "200F1060"
                    "20071060"
                ),
            )
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("m 1 A\n", debug)
            self.assertIn("m 2 B\n", debug)
            self.assertEqual(debug.count(" C\n"), 1)

    def test_alink_imports_nested_export_through_shared_parent_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\n"
                "x MAIN 0 4\n"
                "b u0M\n"
                "u INNER\n"
                "m 20 00 00 60\n"
                "r 1 u0\n",
                encoding="ascii",
            )
            (project / "LIB" / "PACKAGE.OBJ").write_text(
                "OBJ1\n"
                "x OUTER 0 5\n"
                "x INNER 2 3\n"
                "b M\n"
                "m EA EA A9 2A 60\n",
                encoding="ascii",
            )

            self.run_tool(project, "alink", "main")

            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes(),
                bytes.fromhex("001020061060EAEAA92A60"),
            )
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("m 1 PACKAGE\n", debug)

    def test_alink_discovers_export_in_differently_named_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nHELPER()\nRETURN\nENDPROC\n",
                encoding="ascii",
            )
            (project / "OBJ" / "UTIL.OBJ").write_text(
                "OBJ1\n"
                "f 0 SRC/UTIL.ACT\n"
                "q 0 0 1 1\n"
                "L 0 0 0 2 1\n"
                "x HELPER 0 1\n"
                "b M\n"
                "m 60\n"
                "n helper\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertEqual(prg, bytes([0x00, 0x10, 0x20, 0x04, 0x10, 0x60, 0x60]))
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("m 1 UTIL\n", debug)
            self.assertIn("f 1 0 SRC/UTIL.ACT\n", debug)
            self.assertIn("q 1 0 4100 0 1 1 HELPER\n", debug)
            self.assertIn("l 1 0 4100 0 2 1\n", debug)

    def test_alink_rejects_ambiguous_scanned_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\nx MAIN 0 4\nb u0M\nu HELPER\nm 20000060\nr 1 u0\n",
                encoding="ascii",
            )
            for module in ("FIRST", "SECOND"):
                (project / "OBJ" / f"{module}.OBJ").write_text(
                    "OBJ1\nx HELPER 0 1\nb M\nm 60\n",
                    encoding="ascii",
                )

            result = self.run_tool(project, "alink", "main", expected_status=1)
            self.assertEqual(result.stderr, "DUPLICATE EXPORT HELPER\n")
            self.assertFalse((project / "BIN" / "MAIN.PRG").exists())

    def test_alink_strictly_validates_obj1_records(self) -> None:
        cases = {
            "compact_body": (
                "OBJ1\nx MAIN 0 1\nb s0i0r\nm 60\n",
                "UNSUPPORTED OBJECT BODY\n",
            ),
            "bad_body_import": (
                "OBJ1\nx MAIN 0 1\nb u1M\nu HELPER\nm 60\n",
                "BAD OBJECT\n",
            ),
            "bad_relocation": (
                "OBJ1\nx MAIN 0 2\nb M\nm 0000\nr 0 x\n",
                "BAD OBJECT\n",
            ),
            "noncanonical_import_code": (
                "OBJ1\nx MAIN 0 2\nb u10M\nu FIRST\nu SECOND\nm 0000\n",
                "UNSUPPORTED OBJECT BODY\n",
            ),
            "unknown_record": (
                "OBJ1\nx MAIN 0 1\nb M\nq ignored\nm 60\n",
                "BAD OBJECT\n",
            ),
        }
        for name, (object_text, expected_error) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "OBJ" / "MAIN.OBJ").write_text(
                    object_text,
                    encoding="ascii",
                )

                result = self.run_tool(project, "alink", "main", expected_status=1)
                self.assertEqual(result.stderr, expected_error)
                self.assertFalse((project / "BIN" / "MAIN.PRG").exists())

    def test_alink_links_native_udos_obj1_debug_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\n"
                "f 0 SRC/MAIN.ACT\n"
                "q 0 0 1 1\n"
                "L 0 0 0 2 1\n"
                "V g c 0 0 2 5\n"
                "x MAIN 0 3\n"
                "x __IDATA 1 2\n"
                "b M\n"
                "b M\n"
                "m 60 07 00\n"
                "i 7\n"
                "v value 7\n"
                "k 0\n"
                "n main\n",
                encoding="ascii",
            )

            self.run_tool(project, "alink", "main")

            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes(),
                bytes([0x00, 0x10, 0x60, 0x07, 0x00]),
            )
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("f 0 0 SRC/MAIN.ACT\n", debug)
            self.assertIn("q 0 0 4096 0 1 1 MAIN\n", debug)
            self.assertIn("l 0 0 4096 0 2 1\n", debug)
            self.assertIn("v g c 0 0 4097 2 0 2 5 value\n", debug)

            by_line = self.run_tool(project, "actdbg", "main", "line", "2")
            self.assertEqual(by_line.stdout, "ADDRESS 4096 SRC/MAIN.ACT:2\n")
            by_address = self.run_tool(
                project, "actdbg", "main", "source", "4096"
            )
            self.assertEqual(by_address.stdout, "SOURCE 4096 SRC/MAIN.ACT:2\n")

    def test_alink_selects_nonfirst_root_export_and_prunes_unused_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\n"
                "f 0 SRC/MAIN.ACT\n"
                "q 0 0 1 1\n"
                "q 1 0 5 1\n"
                "L 0 0 0 2 1\n"
                "L 1 0 0 6 1\n"
                "x UNUSED 0 4\n"
                "x MAIN 4 1\n"
                "b u0M\n"
                "b M\n"
                "u MISSING\n"
                "m 20 00 00 60 60\n"
                "r 1 u0\n"
                "n main\n",
                encoding="ascii",
            )

            self.run_tool(project, "alink", "main")

            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes(),
                bytes([0x00, 0x10, 0x60]),
            )
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("q 0 1 4096 0 5 1 MAIN\n", debug)
            self.assertIn("l 0 1 4096 0 6 1\n", debug)
            self.assertNotIn("UNUSED", debug)
            self.assertNotIn("MISSING", debug)

    def test_alink_selects_nonfirst_dependency_with_lettered_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\n"
                "x MAIN 0 4\n"
                "b u0M\n"
                "u API\n"
                "m 20 00 00 60\n"
                "r 1 u0\n"
                "n main\n",
                encoding="ascii",
            )
            imports = "".join(f"u D{index}\n" for index in range(10))
            (project / "OBJ" / "A.OBJ").write_text(
                "OBJ1\n"
                "f 0 SRC/A.ACT\n"
                "q 0 0 1 1\n"
                "q 1 0 5 1\n"
                "L 0 0 0 2 1\n"
                "L 1 0 0 6 1\n"
                "x UNUSED 0 4\n"
                "x API 4 4\n"
                "b u0M\n"
                "b uAM\n"
                + imports
                + "u HELPER\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 uA\n"
                "n api\n",
                encoding="ascii",
            )
            (project / "LIB" / "HELPER.OBJ").write_text(
                "OBJ1\nx HELPER 0 1\nb M\nm 60\nn helper\n",
                encoding="ascii",
            )

            self.run_tool(project, "alink", "main")

            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes(),
                bytes.fromhex("0010200410602008106060"),
            )
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("m 1 A\n", debug)
            self.assertIn("q 1 1 4100 0 5 1 API\n", debug)
            self.assertIn("l 1 1 4100 0 6 1\n", debug)
            self.assertNotIn("q 1 0 ", debug)
            self.assertNotIn("D0", debug)

    def test_alink_accepts_case_insensitive_final_letter_import_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            imports = "".join(f"u D{index}\n" for index in range(35))
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\n"
                "x MAIN 0 4\n"
                "b uzM\n"
                + imports
                + "u HELPER\n"
                "m 20 00 00 60\n"
                "r 1 uZ\n",
                encoding="ascii",
            )
            (project / "LIB" / "HELPER.OBJ").write_text(
                "OBJ1\nx HELPER 0 1\nb M\nm 60\n",
                encoding="ascii",
            )

            self.run_tool(project, "alink", "main")

            self.assertEqual(
                (project / "BIN" / "MAIN.PRG").read_bytes(),
                bytes.fromhex("00102004106060"),
            )

    def test_alink_rejects_legacy_placeholder_runtime_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            name = "rt_print_line.obj"
            (project / "LIB" / name.upper()).write_text(
                (self.root / "src" / "runtime" / "modules" / name).read_text(encoding="ascii"),
                encoding="ascii",
            )
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\nx MAIN 0 4\nb u0M\nu RT.PRINT_LINE\nm 20000060\nr 1 u0\n",
                encoding="ascii",
            )

            result = self.run_tool(project, "alink", "main", expected_status=1)
            self.assertEqual(result.stderr, "PLACEHOLDER OBJECT RT.PRINT_LINE\n")
            self.assertFalse((project / "BIN" / "MAIN.PRG").exists())

    def test_alink_rejects_duplicate_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\nx MAIN 0 4\nb u0M\nu HELPER\nm 20000060\nr 1 u0\n",
                encoding="ascii",
            )
            (project / "OBJ" / "HELPER.OBJ").write_text(
                "OBJ1\nx HELPER 0 1\nx MAIN 0 1\nb M\nm 60\n",
                encoding="ascii",
            )

            result = self.run_tool(project, "alink", "main", expected_status=1)
            self.assertEqual(result.stderr, "DUPLICATE EXPORT MAIN\n")
            self.assertFalse((project / "BIN" / "MAIN.PRG").exists())

    def test_alink_rejects_out_of_range_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "OBJ1\nx MAIN 1 1\nb M\nm 60\n",
                encoding="ascii",
            )

            result = self.run_tool(project, "alink", "main", expected_status=1)
            self.assertEqual(result.stderr, "BAD OBJECT\n")
            self.assertFalse((project / "BIN" / "MAIN.PRG").exists())

    def test_alink_loads_standalone_real_runtime_family_and_closure(self) -> None:
        runtime_names = (
            "rt_f_abs.obj",
            "rt_f_add.obj",
            "rt_f_addsub_core.obj",
            "rt_f_special.obj",
            "rt_f_cmp.obj",
            "rt_f_div.obj",
            "rt_f_mul.obj",
            "rt_f_sqrt.obj",
            "rt_f_sub.obj",
            "rt_f_to_i.obj",
            "rt_i_to_f.obj",
            "rt_print_f.obj",
            "rt_s_to_f.obj",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            for name in runtime_names:
                (project / "LIB" / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )

            symbols = [name.removesuffix(".obj").upper() for name in runtime_names]
            import_codes = [
                str(index) if index < 10 else chr(ord("A") + index - 10)
                for index in range(len(symbols))
            ]
            code = bytearray()
            relocations = []
            for import_code in import_codes:
                code.extend((0x20, 0x00, 0x00))
                relocations.append(f"r {len(code) - 2} u{import_code}")
            code.append(0x60)
            object_lines = [
                "OBJ1",
                f"x MAIN 0 {len(code)}",
                "b " + "".join(f"u{code}" for code in import_codes) + "M",
                *(f"u {symbol}" for symbol in symbols),
                "m " + code.hex().upper(),
                *relocations,
                "",
            ]
            (project / "OBJ" / "MAIN.OBJ").write_text(
                "\n".join(object_lines), encoding="ascii"
            )

            self.run_tool(project, "alink", "main")
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            for symbol in symbols:
                self.assertIn(symbol, debug)
            self.assertEqual(debug.count("RT_S_TO_F"), 1)
            self.assertGreater((project / "BIN" / "MAIN.PRG").stat().st_size, 2000)

    def test_math_runtime_modules_are_reproducible_and_shared(self) -> None:
        generated = subprocess.run(
            ["python3", str(self.root / "tools" / "generate_math_runtime.py"), "--check"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(generated.returncode, 0, msg=generated.stdout + generated.stderr)

        for name, export in (
            ("rt_f_add", "x rt_f_add 0 6\n"),
            ("rt_f_addsub_core", "x rt_f_addsub_core 0 703\n"),
            ("rt_f_special", "x rt_f_special 0 419\n"),
            ("rt_f_cmp", "x rt_f_cmp 0 137\n"),
            ("rt_f_div", "x rt_f_div 0 653\n"),
            ("rt_f_mul", "x rt_f_mul 0 518\n"),
            ("rt_f_sqrt", "x rt_f_sqrt 0 506\n"),
            ("rt_f_sub", "x rt_f_sub 0 6\n"),
            ("rt_f_to_i", "x rt_f_to_i 0 124\n"),
            ("rt_print_f", "x rt_print_f 0 909\n"),
        ):
            host_module = self.root / "src" / "runtime" / "modules" / f"{name}.obj"
            udos_module = self.root / "src" / "runtime" / "udos_modules" / f"{name}.obj"
            self.assertEqual(
                host_module.read_text(encoding="ascii"),
                udos_module.read_text(encoding="ascii"),
            )
            module = host_module.read_text(encoding="ascii")
            self.assertIn(export, module)
            self.assertIn(f"n {name}\n", module)

        comparator = (
            self.root / "src" / "runtime" / "modules" / "rt_f_cmp.obj"
        ).read_text(encoding="ascii")
        self.assertIn("A0 03 B1 02 51 04", comparator)

    def test_generated_float_division_matches_exact_binary32_reference(self) -> None:
        verified = subprocess.run(
            [
                "python3",
                str(self.root / "tools" / "verify_f_div_runtime.py"),
                "--random-cases",
                "1024",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(verified.returncode, 0, msg=verified.stdout + verified.stderr)
        self.assertIn("1465 exact edge/random cases passed", verified.stdout)

    def test_generated_float_square_root_matches_exact_binary32_reference(self) -> None:
        verified = subprocess.run(
            [
                "python3",
                str(self.root / "tools" / "verify_f_sqrt_runtime.py"),
                "--random-cases",
                "1024",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(verified.returncode, 0, msg=verified.stdout + verified.stderr)
        self.assertIn(
            "2590 exact exponent-boundary/edge/random cases passed",
            verified.stdout,
        )

    def test_generated_float_print_matches_exact_decimal_reference(self) -> None:
        verified = subprocess.run(
            [
                "python3",
                str(self.root / "tools" / "verify_f_print_runtime.py"),
                "--random-cases",
                "1024",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(verified.returncode, 0, msg=verified.stdout + verified.stderr)
        self.assertIn("1055 exact edge/random strings passed", verified.stdout)

    def test_reu_source_calls_link_direct_hardware_runtime_without_udos(self) -> None:
        generated = subprocess.run(
            ["python3", str(self.root / "tools" / "generate_reu_runtime.py"), "--check"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(generated.returncode, 0, msg=generated.stdout + generated.stderr)

        runtime_names = (
            "rt_reu_alloc.obj",
            "rt_reu_state.obj",
            "rt_reu_resolve.obj",
            "rt_reu_transfer.obj",
            "rt_reu_peek8.obj",
            "rt_reu_peek16.obj",
            "rt_reu_poke8.obj",
            "rt_reu_poke16.obj",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            for name in runtime_names:
                (project / "LIB" / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(
                        encoding="ascii"
                    ),
                    encoding="ascii",
                )
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE main\n"
                "REU BYTE ARRAY global(50000)\n"
                "BYTE value\n"
                "PROC main()\n"
                "REU BYTE ARRAY local(32)\n"
                "ReuPoke8(global,0,65)\n"
                "ReuPoke16(local,2,$1234)\n"
                "value=ReuPeek8(global,0)+1\n"
                "IF ReuPeek16(local,2)=$1234 THEN\n"
                'PrintE("reu ok")\n'
                "FI\n"
                "RETURN\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            for symbol in (
                "RT_REU_ALLOC",
                "RT_REU_PEEK8",
                "RT_REU_PEEK16",
                "RT_REU_POKE8",
                "RT_REU_POKE16",
            ):
                self.assertIn(f"\nu {symbol}\n", obj_text)
            self.assertIn("850E", obj_text)

            self.run_tool(project, "alink", "main")
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            for module in (
                "RT_REU_STATE",
                "RT_REU_RESOLVE",
                "RT_REU_TRANSFER",
            ):
                self.assertIn(module, debug)
            self.assertNotIn("UDOS", debug)
            self.assertGreater((project / "BIN" / "MAIN.PRG").stat().st_size, 1800)

    def test_actc_rejects_invalid_reu_array_sizes(self) -> None:
        cases = (
            ("REU BYTE ARRAY big(0)", "REU SIZE RANGE LINE 2: BIG\n"),
            ("REU BYTE ARRAY big(65536)", "REU SIZE RANGE LINE 2: BIG\n"),
            (
                "BYTE size\nREU BYTE ARRAY big(size)",
                "REU SIZE MUST BE CONSTANT LINE 3\n",
            ),
        )
        for declaration, expected_error in cases:
            with self.subTest(declaration=declaration), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "SRC" / "MAIN.ACT").write_text(
                    "MODULE main\n"
                    + declaration
                    + "\nPROC main()\nRETURN\n",
                    encoding="ascii",
                )
                result = self.run_tool(project, "actc", "main", expected_status=1)
                self.assertEqual(result.stderr, expected_error)

    def test_shipped_overlay_is_linked_as_program_owned_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                (self.root / "examples" / "ovl_demo.act").read_text(encoding="ascii"),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertRegex(obj_text, r"(?m)^x MAIN 0 ")
            self.assertRegex(obj_text, r"(?m)^x MATH [1-9][0-9]* ")
            self.assertNotIn("RT_OVL_", obj_text)

            self.run_tool(project, "alink", "main")
            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertEqual(prg[:2], bytes([0x00, 0x10]))
            self.assertIn(bytes([0xA9, ord("4"), 0x20, 0xD2, 0xFF]), prg)
            self.assertIn(bytes([0xA9, ord("2"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_rejects_unknown_program_owned_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE main\n"
                "PROC main()\n"
                "OverlayCall(Missing)\n"
                "RETURN\n",
                encoding="ascii",
            )

            result = self.run_tool(project, "actc", "main", expected_status=1)
            self.assertEqual(result.stderr, "UNKNOWN OVERLAY LINE 3: MISSING\n")

    def test_dbf_family_links_reu_and_kernal_adapters_without_udos_calls(self) -> None:
        generated = subprocess.run(
            ["python3", str(self.root / "tools" / "generate_dbf_runtime.py"), "--check"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(generated.returncode, 0, msg=generated.stdout + generated.stderr)

        runtime_dir = self.root / "src" / "runtime" / "modules"
        for path in runtime_dir.glob("rt_dbf_*.obj"):
            text = path.read_text(encoding="ascii").replace(" ", "")
            for address in ("2DCF", "30CF", "33CF", "36CF", "39CF", "3CCF"):
                self.assertNotIn("20" + address, text, msg=path.name)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            for source in runtime_dir.glob("rt_dbf_*.obj"):
                (project / "LIB" / source.name.upper()).write_text(
                    source.read_text(encoding="ascii"),
                    encoding="ascii",
                )
            for name in (
                "rt_reu_alloc.obj",
                "rt_reu_state.obj",
                "rt_reu_resolve.obj",
                "rt_reu_transfer.obj",
                "rt_reu_peek8.obj",
                "rt_reu_poke8.obj",
            ):
                (project / "LIB" / name.upper()).write_text(
                    (runtime_dir / name).read_text(encoding="ascii"),
                    encoding="ascii",
                )
            (project / "SRC" / "MAIN.ACT").write_text(
                "MODULE main\n"
                "CARD filename\n"
                "BYTE handle\n"
                "BYTE result\n"
                "PROC main()\n"
                "filename=$3000\n"
                "handle=DbfCreate(filename)\n"
                "handle=DbfOpen(filename)\n"
                "result=DbfGo(handle,2)\n"
                "result=DbfFieldCount(handle)\n"
                "result=DbfFieldLen(handle,1)\n"
                "result=DbfReadByte(handle,0)\n"
                "result=DbfReadFieldByte(handle,1,0)\n"
                "result=DbfWriteFieldByte(handle,1,0,65)\n"
                "result=DbfWriteByte(handle,0,65)\n"
                "result=DbfAppend(handle)\n"
                "result=DbfPack(handle)\n"
                "result=DbfSave(handle)\n"
                "result=DbfDelete(handle)\n"
                "result=DbfUndelete(handle)\n"
                "result=DbfDeleted(handle)\n"
                "result=DbfHeaderLen(handle)\n"
                "result=DbfRecordLen(handle)\n"
                "result=DbfTotalRecs(handle)\n"
                "result=DbfCurrRecNo(handle)\n"
                "DbfClose(handle)\n"
                "RETURN\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            for symbol in (
                "RT_DBF_CREATE",
                "RT_DBF_OPEN",
                "RT_DBF_WRITEFIELDBYTE",
                "RT_DBF_PACK",
                "RT_DBF_SAVE",
                "RT_DBF_CLOSE",
            ):
                self.assertIn(f"\nu {symbol}\n", obj_text)
            self.assertIn("85E0", obj_text)

            self.run_tool(project, "alink", "main")
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            for module in (
                "RT_DBF_STATE",
                "RT_DBF_ADAPTER_STATE",
                "RT_DBF_ENSURE_REU",
                "RT_DBF_FILE_LOAD_REU",
                "RT_DBF_RAW_REU_READ",
                "RT_DBF_RAW_REU_WRITE",
                "RT_DBF_FILE_OPEN_WRITE",
                "RT_DBF_FILE_WRITE_BYTE",
                "RT_DBF_FILE_CLOSE",
                "RT_REU_ALLOC",
                "RT_REU_TRANSFER",
            ):
                self.assertIn(module, debug)
            self.assertNotIn("UDOS", debug)
            self.assertGreater((project / "BIN" / "MAIN.PRG").stat().st_size, 3000)

            (project / "SRC" / "MAIN.ACT").write_text(
                (self.root / "examples" / "dbf1_demo.act").read_text(encoding="ascii"),
                encoding="ascii",
            )
            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")
            shipped_debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("RT_DBF_OPEN", shipped_debug)
            self.assertIn("RT_DBF_FILE_LOAD_REU", shipped_debug)
            self.assertNotIn("UDOS", shipped_debug)

    def test_actc_emits_printe_without_runtime_helper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                'PROC MAIN()\nPrintE("HI")\nRETURN\nENDPROC\n',
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertNotIn("\nu PRINTE\n", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertEqual(prg[:2], bytes([0x00, 0x10]))
            self.assertIn(bytes([0xA9, ord("H"), 0x20, 0xD2, 0xFF]), prg)
            self.assertIn(bytes([0xA9, ord("I"), 0x20, 0xD2, 0xFF]), prg)
            self.assertIn(bytes([0xA9, 0x0D, 0x20, 0xD2, 0xFF]), prg)

    def test_actc_emits_printie_for_constant_integer_expression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nPrintIE((2 + 3) * 4)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertNotIn("\nu PRINTIE\n", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0xA9, ord("2"), 0x20, 0xD2, 0xFF]), prg)
            self.assertIn(bytes([0xA9, ord("0"), 0x20, 0xD2, 0xFF]), prg)
            self.assertIn(bytes([0xA9, 0x0D, 0x20, 0xD2, 0xFF]), prg)

    def test_actc_printie_variable_imports_helper_and_emits_newline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (project / "LIB" / "RT_PRINT_I.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(encoding="ascii"),
                encoding="ascii",
            )
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nCARD x\nx = 300\nPrintIE(x)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("\nu RT_PRINT_I\n", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0xA9, 0x2C, 0xA2, 0x01]), prg)
            self.assertIn(bytes([0xA9, 0x0D, 0x20, 0xD2, 0xFF]), prg)

    def test_actc_printie_simple_variable_addition_emits_native_adc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (project / "LIB" / "RT_PRINT_I.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(encoding="ascii"),
                encoding="ascii",
            )
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nCARD x\nx = 300\nPrintIE(x + 5)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("\nu RT_PRINT_I\n", obj_text)
            self.assertNotIn(bytes("305", "ascii").hex().upper(), obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0x18, 0x69, 0x05, 0x48, 0x8A, 0x69, 0x00, 0xAA, 0x68]), prg)
            self.assertIn(bytes([0xA9, 0x0D, 0x20, 0xD2, 0xFF]), prg)

    def test_actc_assignment_from_variable_addition_stores_runtime_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (project / "LIB" / "RT_PRINT_I.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(encoding="ascii"),
                encoding="ascii",
            )
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nCARD x,y\nx = 300\ny = x + 5\nPrintIE(y)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x MAIN_Y_LO", obj_text)
            self.assertIn("x MAIN_Y_HI", obj_text)
            self.assertIn("\nu RT_PRINT_I\n", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0x18, 0x69, 0x05, 0x48, 0x8A, 0x69, 0x00, 0xAA, 0x68]), prg)
            self.assertIn(bytes([0x8D]), prg)
            self.assertIn(bytes([0x8E]), prg)
            self.assertIn(bytes([0xA9, 0x0D, 0x20, 0xD2, 0xFF]), prg)

    def test_actc_assignment_from_two_variables_emits_native_adc_absolute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (project / "LIB" / "RT_PRINT_I.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(encoding="ascii"),
                encoding="ascii",
            )
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nCARD x,y,z\nx = 300\ny = 7\nz = x + y\nPrintIE(z)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x MAIN_Z_LO", obj_text)
            self.assertIn("x MAIN_Z_HI", obj_text)
            self.assertIn("\nu RT_PRINT_I\n", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0x18, 0x6D]), prg)
            self.assertIn(bytes([0x48, 0x8A, 0x6D]), prg)
            self.assertIn(bytes([0xAA, 0x68, 0x8D]), prg)
            self.assertIn(bytes([0x8E]), prg)
            self.assertIn(bytes([0xA9, 0x0D, 0x20, 0xD2, 0xFF]), prg)

    def test_actc_card_plus_byte_zero_extends_rhs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (project / "LIB" / "RT_PRINT_I.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(encoding="ascii"),
                encoding="ascii",
            )
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nCARD x,z\nBYTE y\nx = 300\ny = 7\nz = x + y\nPrintIE(z)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x MAIN_Y_LO", obj_text)
            self.assertNotIn("x MAIN_Y_HI", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0x48, 0x8A, 0x69, 0x00, 0xAA, 0x68]), prg)
            self.assertIn(bytes([0xA9, 0x0D, 0x20, 0xD2, 0xFF]), prg)

    def test_actc_dynamic_expression_tree_selects_mul_and_div_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            for name in ("rt_i_mul.obj", "rt_i_div.obj", "rt_print_i.obj"):
                (shared_lib / name.upper()).write_text(
                    (self.root / "src" / "runtime" / "modules" / name).read_text(encoding="ascii"),
                    encoding="ascii",
                )

            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD seed,a,b,result",
                        "seed = 6",
                        "a = seed + 0",
                        "b = a + 1",
                        "result = -((b + 3) * 4) / (a - 4)",
                        "PrintI(result)",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("\nu RT_I_MUL\n", obj_text)
            self.assertIn("\nu RT_I_DIV\n", obj_text)
            self.assertIn("\nu RT_PRINT_I\n", obj_text)
            self.assertIn("MAIN_EXPR_", obj_text)
            self.assertFalse((project / "LIB").exists())

            self.run_tool(project, "alink", "main")
            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes.fromhex("85E086E1A000B10285E2"), prg)
            self.assertIn(bytes.fromhex("85E086E1A000B10285E2C8B10285E305E2"), prg)
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("RT_I_MUL", debug)
            self.assertIn("RT_I_DIV", debug)
            self.assertIn("RT_PRINT_I", debug)

    def test_actc_folds_constant_product_inside_dynamic_expression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_lib = root / "LIB"
            shared_lib.mkdir()
            (shared_lib / "RT_PRINT_I.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(
                    encoding="ascii"
                ),
                encoding="ascii",
            )
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nCARD seed,x,y\nseed = 5\nx = seed + 0\n"
                "y = x + (2 * 3)\nPrintI(y)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertNotIn("RT_I_MUL", obj_text)
            self.assertNotIn("RT_I_DIV", obj_text)
            self.assertIn("\nu RT_PRINT_I\n", obj_text)
            self.assertIn("6906", obj_text)
            self.run_tool(project, "alink", "main")

    def test_actc_expression_storage_grows_past_6502_style_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            expression = "x + (" * 40 + "x" + ")" * 40
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nCARD seed,x,y\nseed = 1\nx = seed + 0\ny = "
                + expression
                + "\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertGreater(len(obj_text), 4096)
            self.assertIn("MAIN_EXPR_30_VALUE_LO", obj_text)

    def test_actc_runtime_if_variable_equals_constant_emits_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD x,y",
                        "x = 300",
                        "y = x + 5",
                        "IF y = 305 THEN",
                        'PrintE("YES")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn("MAIN_MAIN_IF_NEXT_", obj_text)
            self.assertIn("MAIN_EXPR_", obj_text)
            self.assertIn(bytes([0xCD]), prg)
            self.assertIn(bytes([0xD0]), prg)
            self.assertIn(bytes([0xA9, ord("Y"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_runtime_if_variable_not_equals_constant_emits_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD x,y",
                        "x = 300",
                        "y = x + 5",
                        "IF y # 0 THEN",
                        'PrintE("NE")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn("MAIN_MAIN_IF_NEXT_", obj_text)
            self.assertIn("MAIN_EXPR_", obj_text)
            self.assertGreaterEqual(prg.count(bytes([0xD0])), 2)
            self.assertIn(bytes([0xA9, ord("N"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_runtime_if_card_less_than_constant_emits_unsigned_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD x,y",
                        "x = 300",
                        "y = x + 5",
                        "IF y < 400 THEN",
                        'PrintE("LT")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn("MAIN_EXPR_", obj_text)
            self.assertIn(bytes([0x90]), prg)
            self.assertIn(bytes([0xD0]), prg)
            self.assertIn(bytes([0xA9, ord("L"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_runtime_if_byte_greater_equal_constant_emits_unsigned_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD x",
                        "BYTE b",
                        "x = 2",
                        "b = x + 5",
                        "IF b >= 7 THEN",
                        'PrintE("GE")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn("MAIN_EXPR_", obj_text)
            self.assertIn(bytes([0x90]), prg)
            self.assertIn(bytes([0xB0]), prg)
            self.assertIn(bytes([0xA9, ord("G"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_runtime_if_card_less_than_out_of_range_constant_runs_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD x,y",
                        "x = 300",
                        "y = x + 5",
                        "IF y < 70000 THEN",
                        'PrintE("OK")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertNotIn("MAIN_EXPR_", obj_text)
            self.assertIn(bytes([0xA9, ord("O"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_runtime_if_card_equals_out_of_range_constant_skips_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD x,y",
                        "x = 0",
                        "y = x + 0",
                        "IF y = 65536 THEN",
                        'PrintE("BAD")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertNotIn("MAIN_EXPR_", obj_text)
            self.assertIn("MAIN_MAIN_IF_NEXT_", obj_text)
            self.assertIn(bytes([0x4C]), prg)
            self.assertIn(bytes([0xA9, ord("B"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_runtime_if_byte_equals_out_of_range_constant_skips_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD x",
                        "BYTE b",
                        "x = 2",
                        "b = x + 5",
                        "IF b = 263 THEN",
                        'PrintE("BAD")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertNotIn("MAIN_EXPR_", obj_text)
            self.assertIn("MAIN_MAIN_IF_NEXT_", obj_text)
            self.assertIn(bytes([0x4C]), prg)
            self.assertIn(bytes([0xA9, ord("B"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_runtime_if_byte_not_equals_out_of_range_constant_runs_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "BYTE b",
                        "b = 7",
                        "IF b <> 263 THEN",
                        'PrintE("OK")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertNotIn("MAIN_EXPR_", obj_text)
            self.assertIn(bytes([0xA9, ord("O"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_if_else_body_has_no_relative_branch_size_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            long_text = "T" * 80
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "BYTE x",
                        "x = 1",
                        "IF x = 1 THEN",
                        f'PrintE("{long_text}")',
                        "ELSE",
                        'PrintE("FALSE")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("MAIN_MAIN_IF_NEXT_", obj_text)
            self.assertIn("MAIN_MAIN_IF_END_", obj_text)
            self.assertIn("r ", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertGreater(len(prg), 400)
            self.assertIn(bytes([0x4C]), prg)

    def test_actc_elseif_compares_arbitrary_word_expressions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD x,y",
                        "x = 2",
                        "y = x + 1",
                        "IF x + 1 < y THEN",
                        'PrintE("LESS")',
                        "ELSEIF x + 1 = y THEN",
                        'PrintE("EQUAL")',
                        "ELSE",
                        'PrintE("GREATER")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertGreaterEqual(obj_text.count("_IF_NEXT_"), 2)
            self.assertGreaterEqual(obj_text.count("_VALUE_LO"), 4)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            for initial in ("L", "E", "G"):
                self.assertIn(bytes([0xA9, ord(initial), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_do_until_while_and_exit_use_absolute_control_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "BYTE x",
                        "x = 0",
                        "DO",
                        "x = x + 1",
                        "UNTIL x = 3",
                        "OD",
                        "WHILE x < 10",
                        "DO",
                        "x = x + 1",
                        "IF x = 5 THEN",
                        "EXIT",
                        "FI",
                        "OD",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertGreaterEqual(obj_text.count("_LOOP_START_"), 2)
            self.assertGreaterEqual(obj_text.count("_LOOP_END_"), 2)
            self.assertIn("x MAIN_MAIN_IF_END_", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertGreaterEqual(prg.count(bytes([0x4C])), 4)

    def test_actc_for_loops_stage_bounds_and_support_descending_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "CARD first,last,i,j",
                        "first = 1",
                        "last = first + 4",
                        "FOR i=first TO last STEP 2",
                        "DO",
                        "j = i + 0",
                        "OD",
                        "FOR j=5 TO 1 STEP -2",
                        "DO",
                        "i = j + 0",
                        "OD",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertGreaterEqual(obj_text.count("__FOR_"), 8)
            self.assertGreaterEqual(obj_text.count("_LOOP_START_"), 2)
            self.assertIn("A9FEA2FF", obj_text)
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertGreaterEqual(prg.count(bytes([0x4C])), 2)
            self.assertIn(bytes([0x90]), prg)

    def test_actc_rejects_invalid_for_steps(self) -> None:
        cases = {
            "zero": (
                "PROC MAIN()\nBYTE i\nFOR i=0 TO 3 STEP 0\nDO\nOD\nENDPROC\n",
                "ZERO FOR STEP LINE 3\n",
            ),
            "dynamic": (
                "PROC MAIN()\nBYTE i,s\nFOR i=0 TO 3 STEP s\nDO\nOD\nENDPROC\n",
                "DYNAMIC FOR STEP LINE 3\n",
            ),
            "missing_do": (
                "PROC MAIN()\nBYTE i\nFOR i=0 TO 3\nRETURN\nENDPROC\n",
                "FOR REQUIRES DO LINE 3\n",
            ),
        }
        for name, (source, expected_error) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "SRC" / "MAIN.ACT").write_text(source, encoding="ascii")
                result = self.run_tool(project, "actc", "main", expected_status=1)
                self.assertEqual(result.stderr, expected_error)

    def test_actc_structured_control_stack_is_vector_backed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            depth = 40
            lines = ["PROC MAIN()"] + ["DO"] * depth + ["OD"] * depth + ["RETURN", "ENDPROC", ""]
            (project / "SRC" / "MAIN.ACT").write_text("\n".join(lines), encoding="ascii")

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            export_lines = [line for line in obj_text.splitlines() if line.startswith("x ")]
            self.assertEqual(sum("MAIN_MAIN_LOOP_START_" in line for line in export_lines), depth)
            self.assertEqual(sum("MAIN_MAIN_LOOP_END_" in line for line in export_lines), depth)
            self.run_tool(project, "alink", "main")

    def test_actc_rejects_malformed_structured_control(self) -> None:
        cases = {
            "while": ("PROC MAIN()\nWHILE 1\nRETURN\nENDPROC\n", "WHILE REQUIRES DO LINE 2\n"),
            "exit": ("PROC MAIN()\nEXIT\nRETURN\nENDPROC\n", "EXIT OUTSIDE LOOP LINE 2\n"),
            "od": ("PROC MAIN()\nOD\nRETURN\nENDPROC\n", "BAD OD LINE 2\n"),
        }
        for name, (source, expected_error) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.run_tool(root, "actnew", "demo")
                project = root / "DEMO"
                (project / "SRC" / "MAIN.ACT").write_text(source, encoding="ascii")
                result = self.run_tool(project, "actc", "main", expected_status=1)
                self.assertEqual(result.stderr, expected_error)

    def test_actc_printi_imports_link_selected_runtime_helper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "LIB").mkdir()
            (project / "LIB" / "RT_PRINT_I.OBJ").write_text(
                (self.root / "src" / "runtime" / "modules" / "rt_print_i.obj").read_text(encoding="ascii"),
                encoding="ascii",
            )
            (project / "SRC" / "MAIN.ACT").write_text(
                "PROC MAIN()\nCARD x\nx = 300\nPrintI(x)\nPrintI(-1)\nRETURN\nENDPROC\n",
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            obj_text = (project / "OBJ" / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("\nu RT_PRINT_I\n", obj_text)
            self.assertIn("x MAIN_X_LO", obj_text)
            self.assertIn("x MAIN_X_HI", obj_text)

            self.run_tool(project, "alink", "main")
            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0xA9, 0x2C, 0xA2, 0x01]), prg)
            self.assertIn(bytes([0xA9, 0xFF, 0xA2, 0xFF]), prg)
            self.assertIn(bytes([0x20, 0xD2, 0xFF]), prg)
            debug = (project / "BIN" / "MAIN.DBG").read_text(encoding="ascii")
            self.assertIn("m 1 RT_PRINT_I\n", debug)
            runtime = (project / "LIB" / "RT_PRINT_I.OBJ").read_text(encoding="ascii")
            self.assertIn("x RT_PRINT_I 0 126\n", runtime)
            self.assertIn("r 38 x RT_PRINT_I_EMIT_DIGIT\n", runtime)

    def test_actc_compile_time_if_condition_controls_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "IF 1 = 1 THEN",
                        'PrintE("YES")',
                        "FI",
                        "IF 1 = 0 THEN",
                        'PrintE("NO")',
                        "FI",
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0xA9, ord("Y"), 0x20, 0xD2, 0xFF]), prg)
            self.assertIn(bytes([0xA9, ord("E"), 0x20, 0xD2, 0xFF]), prg)
            self.assertIn(bytes([0xA9, ord("S"), 0x20, 0xD2, 0xFF]), prg)
            self.assertNotIn(bytes([0xA9, ord("N"), 0x20, 0xD2, 0xFF]), prg)
            self.assertNotIn(bytes([0xA9, ord("O"), 0x20, 0xD2, 0xFF]), prg)

    def test_actc_compile_time_if_skips_inactive_unknown_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_tool(root, "actnew", "demo")
            project = root / "DEMO"
            (project / "SRC" / "MAIN.ACT").write_text(
                "\n".join(
                    [
                        "PROC MAIN()",
                        "IF 0 THEN",
                        "IF missing = 1 THEN",
                        'PrintE("BAD")',
                        "FI",
                        "FI",
                        'PrintE("OK")',
                        "RETURN",
                        "ENDPROC",
                        "",
                    ]
                ),
                encoding="ascii",
            )

            self.run_tool(project, "actc", "main")
            self.run_tool(project, "alink", "main")

            prg = (project / "BIN" / "MAIN.PRG").read_bytes()
            self.assertIn(bytes([0xA9, ord("O"), 0x20, 0xD2, 0xFF]), prg)
            self.assertIn(bytes([0xA9, ord("K"), 0x20, 0xD2, 0xFF]), prg)
            self.assertNotIn(bytes([0xA9, ord("B"), 0x20, 0xD2, 0xFF]), prg)


if __name__ == "__main__":
    unittest.main()
