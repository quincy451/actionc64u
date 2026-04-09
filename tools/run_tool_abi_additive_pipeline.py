#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
UDOS_ROOT = ROOT.parent / "udos"
BUILD_DIR = ROOT / "build" / "udos_tools"
HARNESS = BUILD_DIR / "tool_abi_harness"
ACTC_PRG = BUILD_DIR / "ACTC.PRG"
ALINK_PRG = BUILD_DIR / "ALINK.PRG"
AVMRUN_PRG = BUILD_DIR / "AVMRUN.PRG"
ACTC_LABELS = BUILD_DIR / "actc.current.labels"
ALINK_LABELS = BUILD_DIR / "alink.current.labels"
AVMRUN_LABELS = BUILD_DIR / "avmrun.current.labels"
SERVICES_INC = BUILD_DIR / "udos_services.inc"
DEFAULT_BASE_FS = UDOS_ROOT / "build" / "udos-release-fs-manual-pipeline-44"

SCENARIOS = {
    "additive": {
        "out_fs_name": "harness-actc-alink-avmrun-additive",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintE("HELLO")\r'
            'W()\r'
            'PrintI(50 + 7 - 3)\r'
            'PrintIE(60 - 3 + 2)\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 38\n"
            "b e0u0p0p1ap2myp3p4mp5azr\n"
            "u w\n"
            "s HELLO\n"
            "i 50\n"
            "i 7\n"
            "i 3\n"
            "i 60\n"
            "i 3\n"
            "i 2\n"
            "k 7\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 64, 0, 0, 0, 1, 53, 0, 97, 53, 0, 73,
                16, 255, 69, 40, 0, 17, 50, 0, 17, 7, 0, 20, 17, 3, 0, 21,
                73, 48, 255, 17, 60, 0, 17, 3, 0, 21, 17, 2, 0, 20, 73, 49,
                255, 73, 32, 255, 97, 59, 0, 73, 0, 255, 17, 7, 0, 73, 49,
                255, 72, 72, 69, 76, 76, 79, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "HELLO\nTOOL7\n5459\n",
    },
    "precedence": {
        "out_fs_name": "harness-actc-alink-avmrun-precedence",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintI(2 + 3 * 4)\r'
            'PrintIE((20 - 5) / 3)\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 17\n"
            "b p0p1ayi2r\n"
            "i 2\n"
            "i 12\n"
            "i 5\n"
            "k 7\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 19, 0, 0, 0, 1, 19, 0, 17, 2, 0, 17,
                12, 0, 20, 73, 48, 255, 17, 5, 0, 73, 49, 255, 73, 32, 255,
            ]
        ),
        "expected_console": "145\n",
    },
    "comparisons": {
        "out_fs_name": "harness-actc-alink-avmrun-comparisons",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintIE(2 + 3 * 4)\r'
            'PrintIE((20 - 5) / 3)\r'
            'PrintIE((2 + 3) * 4 = 20)\r'
            'PrintIE((2 + 3 * 4) > 10)\r'
            'W()\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 40\n"
            "b p0p1azi2p3p4qzp5p6gzu0r\n"
            "u w\n"
            "i 2\n"
            "i 12\n"
            "i 5\n"
            "i 20\n"
            "i 20\n"
            "i 14\n"
            "i 10\n"
            "k 6\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 60, 0, 0, 0, 1, 55, 0, 17, 2, 0, 17,
                12, 0, 20, 73, 49, 255, 17, 5, 0, 73, 49, 255, 17, 20, 0,
                17, 20, 0, 22, 73, 49, 255, 17, 14, 0, 17, 10, 0, 29, 73,
                49, 255, 69, 42, 0, 73, 32, 255, 97, 55, 0, 73, 0, 255, 17,
                7, 0, 73, 49, 255, 72, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "14\n5\n1\n1\nTOOL7\n",
    },
    "comparison_else": {
        "out_fs_name": "harness-actc-alink-avmrun-comparison-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'PrintE("YES")\r'
            'ELSE\r'
            'PrintE("NO")\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 36\n"
            "b p0p1ap2ghe0we1ve2r\n"
            "s YES\n"
            "s NO\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 50, 0, 0, 0, 1, 38, 0, 17, 2, 0, 17,
                12, 0, 20, 17, 10, 0, 29, 24, 23, 0, 97, 38, 0, 73, 16,
                255, 25, 29, 0, 97, 42, 0, 73, 16, 255, 97, 45, 0, 73,
                16, 255, 73, 32, 255, 89, 69, 83, 0, 78, 79, 0, 68, 79,
                78, 69, 0,
            ]
        ),
        "expected_console": "YES\nDONE\n",
    },
    "branch_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-branch-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC BYE()\r'
            'PrintE("BYE")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'IF 1 = 1 THEN\r'
            'HELLO()\r'
            'ELSE\r'
            'BYE()\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x bye 7 7\n"
            "x main 14 26\n"
            "b e0r\n"
            "b e1r\n"
            "b p0p1qhc0wc1ve2r\n"
            "s HELLO\n"
            "s BYE\n"
            "s DONE\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 57, 0, 14, 0, 1, 42, 0, 97, 42, 0, 73,
                16, 255, 72, 97, 48, 0, 73, 16, 255, 72, 17, 1, 0, 17, 1,
                0, 22, 24, 30, 0, 69, 0, 0, 25, 33, 0, 69, 7, 0, 97, 52,
                0, 73, 16, 255, 73, 32, 255, 72, 69, 76, 76, 79, 0, 66, 89,
                69, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "HELLO\nDONE\n",
    },
    "comparison_branch_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-comparison-branch-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC BYE()\r'
            'PrintE("BYE")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'HELLO()\r'
            'ELSE\r'
            'BYE()\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x bye 7 7\n"
            "x main 14 30\n"
            "b e0r\n"
            "b e1r\n"
            "b p0p1ap2ghc0wc1ve2r\n"
            "s HELLO\n"
            "s BYE\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 61, 0, 14, 0, 1, 46, 0, 97, 46, 0, 73,
                16, 255, 72, 97, 52, 0, 73, 16, 255, 72, 17, 2, 0, 17, 12,
                0, 20, 17, 10, 0, 29, 24, 34, 0, 69, 0, 0, 25, 37, 0, 69,
                7, 0, 97, 56, 0, 73, 16, 255, 73, 32, 255, 72, 69, 76, 76,
                79, 0, 66, 89, 69, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "HELLO\nDONE\n",
    },
    "nested_branch_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-branch-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC BYE()\r'
            'PrintE("BYE")\r'
            'RETURN\r'
            'PROC OUTER()\r'
            'PrintE("OUTER")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'IF 1 = 1 THEN\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'HELLO()\r'
            'ELSE\r'
            'BYE()\r'
            'FI\r'
            'ELSE\r'
            'OUTER()\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x bye 7 7\n"
            "x outer 14 7\n"
            "x main 21 46\n"
            "b e0r\n"
            "b e1r\n"
            "b e2r\n"
            "b p0p1qhp2p3ap4ghc0wc1vwc2ve3r\n"
            "s HELLO\n"
            "s BYE\n"
            "s OUTER\n"
            "s DONE\n"
            "i 1\n"
            "i 1\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 90, 0, 21, 0, 1, 69, 0, 97, 69, 0, 73,
                16, 255, 72, 97, 75, 0, 73, 16, 255, 72, 97, 79, 0, 73, 16,
                255, 72, 17, 1, 0, 17, 1, 0, 22, 24, 57, 0, 17, 2, 0, 17,
                12, 0, 20, 17, 10, 0, 29, 24, 51, 0, 69, 0, 0, 25, 60, 0,
                69, 7, 0, 25, 60, 0, 69, 14, 0, 97, 85, 0, 73, 16, 255, 73,
                32, 255, 72, 69, 76, 76, 79, 0, 66, 89, 69, 0, 79, 85, 84,
                69, 82, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "HELLO\nDONE\n",
    },
    "branch_external": {
        "out_fs_name": "harness-actc-alink-avmrun-branch-external",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'W()\r'
            'ELSE\r'
            'PrintE("BAD")\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 33\n"
            "b p0p1ap2ghu0we0ve1r\n"
            "u w\n"
            "s BAD\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 62, 0, 0, 0, 1, 48, 0, 17, 2, 0, 17,
                12, 0, 20, 17, 10, 0, 29, 24, 20, 0, 69, 35, 0, 25, 26,
                0, 97, 48, 0, 73, 16, 255, 97, 52, 0, 73, 16, 255, 73,
                32, 255, 97, 57, 0, 73, 0, 255, 17, 7, 0, 73, 49, 255,
                72, 66, 65, 68, 0, 68, 79, 78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "TOOL7\nDONE\n",
    },
    "nested_branch_external": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-branch-external",
        "source": (
            'MODULE MAIN\r'
            'PROC OUTER()\r'
            'PrintE("OUTER")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'IF 1 = 1 THEN\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'W()\r'
            'ELSE\r'
            'PrintE("BAD1")\r'
            'FI\r'
            'ELSE\r'
            'OUTER()\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x outer 0 7\n"
            "x main 7 49\n"
            "b e0r\n"
            "b p0p1qhp2p3ap4ghu0we1vwc0ve2r\n"
            "u w\n"
            "s OUTER\n"
            "s BAD1\n"
            "s DONE\n"
            "i 1\n"
            "i 1\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 92, 0, 7, 0, 1, 71, 0, 97, 71, 0, 73,
                16, 255, 72, 17, 1, 0, 17, 1, 0, 22, 24, 46, 0, 17, 2, 0,
                17, 12, 0, 20, 17, 10, 0, 29, 24, 37, 0, 69, 58, 0, 25, 49,
                0, 97, 77, 0, 73, 16, 255, 25, 49, 0, 69, 0, 0, 97, 82, 0,
                73, 16, 255, 73, 32, 255, 97, 87, 0, 73, 0, 255, 17, 7, 0,
                73, 49, 255, 72, 79, 85, 84, 69, 82, 0, 66, 65, 68, 49, 0,
                68, 79, 78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "TOOL7\nDONE\n",
    },
    "transitive_external": {
        "out_fs_name": "harness-actc-alink-avmrun-transitive-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'W()\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID")\r'
                'Z()\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("END")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["Z", "W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 16\n"
                "b e0u0e1r\n"
                "u w\n"
                "s START\n"
                "s DONE\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 10\n"
                "b e0u0r\n"
                "u z\n"
                "s MID\n"
                "k 2\n"
                "n w\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s END\n"
                "k 2\n"
                "n z\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 54, 0, 0, 0, 1, 35, 0, 97, 35, 0, 73,
                16, 255, 69, 18, 0, 97, 41, 0, 73, 16, 255, 73, 32, 255,
                97, 46, 0, 73, 16, 255, 69, 28, 0, 72, 97, 50, 0, 73, 16,
                255, 72, 83, 84, 65, 82, 84, 0, 68, 79, 78, 69, 0, 77, 73,
                68, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "START\nMID\nEND\nDONE\n",
    },
    "transitive_branch_external": {
        "out_fs_name": "harness-actc-alink-avmrun-transitive-branch-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 2 + 3 * 4 > 10 THEN\r'
                'PrintE("START")\r'
                'W()\r'
                'ELSE\r'
                'PrintE("BAD")\r'
                'FI\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID")\r'
                'Z()\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("END")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["Z", "W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 39\n"
                "b p0p1ap2ghe0u0we1ve2r\n"
                "u w\n"
                "s START\n"
                "s BAD\n"
                "s DONE\n"
                "i 2\n"
                "i 12\n"
                "i 10\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 10\n"
                "b e0u0r\n"
                "u z\n"
                "s MID\n"
                "k 2\n"
                "n w\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s END\n"
                "k 2\n"
                "n z\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 81, 0, 0, 0, 1, 58, 0, 17, 2, 0, 17,
                12, 0, 20, 17, 10, 0, 29, 24, 26, 0, 97, 58, 0, 73, 16,
                255, 69, 41, 0, 25, 32, 0, 97, 64, 0, 73, 16, 255, 97,
                68, 0, 73, 16, 255, 73, 32, 255, 97, 73, 0, 73, 16, 255,
                69, 51, 0, 72, 97, 77, 0, 73, 16, 255, 72, 83, 84, 65,
                82, 84, 0, 66, 65, 68, 0, 68, 79, 78, 69, 0, 77, 73, 68,
                0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "START\nMID\nEND\nDONE\n",
    },
    "sibling_externals": {
        "out_fs_name": "harness-actc-alink-avmrun-sibling-externals",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'W()\r'
                'Z()\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID1")\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("MID2")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "Z", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 19\n"
                "b e0u0u1e1r\n"
                "u w\n"
                "u z\n"
                "s START\n"
                "s DONE\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s MID1\n"
                "k 2\n"
                "n w\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s MID2\n"
                "k 2\n"
                "n z\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 56, 0, 0, 0, 1, 35, 0, 97, 35, 0, 73,
                16, 255, 69, 21, 0, 69, 28, 0, 97, 41, 0, 73, 16, 255, 73,
                32, 255, 97, 46, 0, 73, 16, 255, 72, 97, 51, 0, 73, 16,
                255, 72, 83, 84, 65, 82, 84, 0, 68, 79, 78, 69, 0, 77, 73,
                68, 49, 0, 77, 73, 68, 50, 0,
            ]
        ),
        "expected_console": "START\nMID1\nMID2\nDONE\n",
    },
    "child_sibling_externals": {
        "out_fs_name": "harness-actc-alink-avmrun-child-sibling-externals",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'W()\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID")\r'
                'Z()\r'
                'Q()\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("END1")\r'
                'RETURN\r'
            ),
            "Q": (
                'MODULE Q\r'
                'PROC Q()\r'
                'PrintE("END2")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "Z", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 16\n"
                "b e0u0e1r\n"
                "u w\n"
                "s START\n"
                "s DONE\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 13\n"
                "b e0u0u1r\n"
                "u z\n"
                "u q\n"
                "s MID\n"
                "k 2\n"
                "n w\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s END1\n"
                "k 2\n"
                "n z\n"
            ),
            "Q": (
                "AVO1\n"
                "x q 0 7\n"
                "b e0r\n"
                "s END2\n"
                "k 2\n"
                "n q\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 70, 0, 0, 0, 1, 45, 0, 97, 45, 0, 73,
                16, 255, 69, 18, 0, 97, 51, 0, 73, 16, 255, 73, 32, 255,
                97, 56, 0, 73, 16, 255, 69, 31, 0, 69, 38, 0, 72, 97, 60,
                0, 73, 16, 255, 72, 97, 65, 0, 73, 16, 255, 72, 83, 84,
                65, 82, 84, 0, 68, 79, 78, 69, 0, 77, 73, 68, 0, 69, 78,
                68, 49, 0, 69, 78, 68, 50, 0,
            ]
        ),
        "expected_console": "START\nMID\nEND1\nEND2\nDONE\n",
    },
    "branch_transitive_local": {
        "out_fs_name": "harness-actc-alink-avmrun-branch-transitive-local",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC LOCAL()\r'
                'PrintE("LOCAL")\r'
                'RETURN\r'
                'PROC MAIN()\r'
                'IF 2 + 3 * 4 > 10 THEN\r'
                'LOCAL()\r'
                'W()\r'
                'ELSE\r'
                'PrintE("BAD")\r'
                'FI\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID")\r'
                'Z()\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("END")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "Z", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x local 0 7\n"
                "x main 7 36\n"
                "b e0r\n"
                "b p0p1ap2ghc0u0we1ve2r\n"
                "u w\n"
                "s LOCAL\n"
                "s BAD\n"
                "s DONE\n"
                "i 2\n"
                "i 12\n"
                "i 10\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 10\n"
                "b e0u0r\n"
                "u z\n"
                "s MID\n"
                "k 2\n"
                "n w\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s END\n"
                "k 2\n"
                "n z\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 85, 0, 7, 0, 1, 62, 0, 97, 62, 0, 73,
                16, 255, 72, 17, 2, 0, 17, 12, 0, 20, 17, 10, 0, 29, 24,
                30, 0, 69, 0, 0, 69, 45, 0, 25, 36, 0, 97, 68, 0, 73, 16,
                255, 97, 72, 0, 73, 16, 255, 73, 32, 255, 97, 77, 0, 73,
                16, 255, 69, 55, 0, 72, 97, 81, 0, 73, 16, 255, 72, 76,
                79, 67, 65, 76, 0, 66, 65, 68, 0, 68, 79, 78, 69, 0, 77,
                73, 68, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "LOCAL\nMID\nEND\nDONE\n",
    },
    "repeated_root_externals": {
        "out_fs_name": "harness-actc-alink-avmrun-repeated-root-externals",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'W()\r'
                'Z()\r'
                'W()\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID1")\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("MID2")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "Z", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 22\n"
                "b e0u0u1u0e1r\n"
                "u w\n"
                "u z\n"
                "s START\n"
                "s DONE\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s MID1\n"
                "k 2\n"
                "n w\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s MID2\n"
                "k 2\n"
                "n z\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 59, 0, 0, 0, 1, 38, 0, 97, 38, 0, 73,
                16, 255, 69, 24, 0, 69, 31, 0, 69, 24, 0, 97, 44, 0, 73,
                16, 255, 73, 32, 255, 97, 49, 0, 73, 16, 255, 72, 97, 54,
                0, 73, 16, 255, 72, 83, 84, 65, 82, 84, 0, 68, 79, 78, 69,
                0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0,
            ]
        ),
        "expected_console": "START\nMID1\nMID2\nMID1\nDONE\n",
    },
    "shared_transitive_external": {
        "out_fs_name": "harness-actc-alink-avmrun-shared-transitive-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'W()\r'
                'Q()\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID1")\r'
                'Z()\r'
                'RETURN\r'
            ),
            "Q": (
                'MODULE Q\r'
                'PROC Q()\r'
                'PrintE("MID2")\r'
                'Z()\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("END")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "Q", "Z", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 19\n"
                "b e0u0u1e1r\n"
                "u w\n"
                "u q\n"
                "s START\n"
                "s DONE\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 10\n"
                "b e0u0r\n"
                "u z\n"
                "s MID1\n"
                "k 2\n"
                "n w\n"
            ),
            "Q": (
                "AVO1\n"
                "x q 0 10\n"
                "b e0u0r\n"
                "u z\n"
                "s MID2\n"
                "k 2\n"
                "n q\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s END\n"
                "k 2\n"
                "n z\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 73, 0, 0, 0, 1, 48, 0, 97, 48, 0, 73,
                16, 255, 69, 21, 0, 69, 31, 0, 97, 54, 0, 73, 16, 255, 73,
                32, 255, 97, 59, 0, 73, 16, 255, 69, 41, 0, 72, 97, 64, 0,
                73, 16, 255, 69, 41, 0, 72, 97, 69, 0, 73, 16, 255, 72, 83,
                84, 65, 82, 84, 0, 68, 79, 78, 69, 0, 77, 73, 68, 49, 0, 77,
                73, 68, 50, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "START\nMID1\nEND\nMID2\nEND\nDONE\n",
    },
    "branch_sibling_externals": {
        "out_fs_name": "harness-actc-alink-avmrun-branch-sibling-externals",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 2 + 3 * 4 > 10 THEN\r'
                'W()\r'
                'Z()\r'
                'ELSE\r'
                'PrintE("BAD")\r'
                'FI\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID1")\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("MID2")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "Z", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 36\n"
                "b p0p1ap2ghu0u1we0ve1r\n"
                "u w\n"
                "u z\n"
                "s BAD\n"
                "s DONE\n"
                "i 2\n"
                "i 12\n"
                "i 10\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s MID1\n"
                "k 2\n"
                "n w\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s MID2\n"
                "k 2\n"
                "n z\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 71, 0, 0, 0, 1, 52, 0, 17, 2, 0, 17,
                12, 0, 20, 17, 10, 0, 29, 24, 23, 0, 69, 38, 0, 69, 45, 0,
                25, 29, 0, 97, 52, 0, 73, 16, 255, 97, 56, 0, 73, 16, 255,
                73, 32, 255, 97, 61, 0, 73, 16, 255, 72, 97, 66, 0, 73, 16,
                255, 72, 66, 65, 68, 0, 68, 79, 78, 69, 0, 77, 73, 68, 49,
                0, 77, 73, 68, 50, 0,
            ]
        ),
        "expected_console": "MID1\nMID2\nDONE\n",
    },
    "branch_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-branch-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 2 + 3 * 4 > 10 THEN\r'
                'W()\r'
                'Q()\r'
                'ELSE\r'
                'PrintE("BAD")\r'
                'FI\r'
                'PrintE("DONE")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("MID1")\r'
                'Z()\r'
                'RETURN\r'
            ),
            "Q": (
                'MODULE Q\r'
                'PROC Q()\r'
                'PrintE("MID2")\r'
                'Z()\r'
                'RETURN\r'
            ),
            "Z": (
                'MODULE Z\r'
                'PROC Z()\r'
                'PrintE("END")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "Q", "Z", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 36\n"
                "b p0p1ap2ghu0u1we0ve1r\n"
                "u w\n"
                "u q\n"
                "s BAD\n"
                "s DONE\n"
                "i 2\n"
                "i 12\n"
                "i 10\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 10\n"
                "b e0u0r\n"
                "u z\n"
                "s MID1\n"
                "k 2\n"
                "n w\n"
            ),
            "Q": (
                "AVO1\n"
                "x q 0 10\n"
                "b e0u0r\n"
                "u z\n"
                "s MID2\n"
                "k 2\n"
                "n q\n"
            ),
            "Z": (
                "AVO1\n"
                "x z 0 7\n"
                "b e0r\n"
                "s END\n"
                "k 2\n"
                "n z\n"
            ),
        },
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 88, 0, 0, 0, 1, 65, 0, 17, 2, 0, 17,
                12, 0, 20, 17, 10, 0, 29, 24, 23, 0, 69, 38, 0, 69, 48, 0,
                25, 29, 0, 97, 65, 0, 73, 16, 255, 97, 69, 0, 73, 16, 255,
                73, 32, 255, 97, 74, 0, 73, 16, 255, 69, 58, 0, 72, 97, 79,
                0, 73, 16, 255, 69, 58, 0, 72, 97, 84, 0, 73, 16, 255, 72,
                66, 65, 68, 0, 68, 79, 78, 69, 0, 77, 73, 68, 49, 0, 77, 73,
                68, 50, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "MID1\nEND\nMID2\nEND\nDONE\n",
    },
    "procedures": {
        "out_fs_name": "harness-actc-alink-avmrun-procedures",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("ONE")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'HELLO()\r'
            'PrintE("TWO")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 10\n"
            "b e0r\n"
            "b c0e1r\n"
            "s ONE\n"
            "s TWO\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 27, 0, 7, 0, 1, 19, 0, 97, 19, 0, 73,
                16, 255, 72, 69, 0, 0, 97, 23, 0, 73, 16, 255, 73, 32, 255,
                79, 78, 69, 0, 84, 87, 79, 0,
            ]
        ),
        "expected_console": "ONE\nTWO\n",
    },
    "if_blocks": {
        "out_fs_name": "harness-actc-alink-avmrun-if-blocks",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 1 = 0 THEN\r'
            'PrintE("NO")\r'
            'FI\r'
            'IF 1 = 1 THEN\r'
            'PrintE("YES")\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 39\n"
            "b p0p1qhe0vp2p3qhe1ve2r\n"
            "s NO\n"
            "s YES\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 53, 0, 0, 0, 1, 41, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 16, 0, 97, 41, 0, 73, 16, 255, 17, 1, 0, 17,
                1, 0, 22, 24, 32, 0, 97, 44, 0, 73, 16, 255, 97, 48, 0, 73,
                16, 255, 73, 32, 255, 78, 79, 0, 89, 69, 83, 0, 68, 79, 78,
                69, 0,
            ]
        ),
        "expected_console": "YES\nDONE\n",
    },
    "else_blocks": {
        "out_fs_name": "harness-actc-alink-avmrun-else-blocks",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 1 = 0 THEN\r'
            'PrintE("BAD")\r'
            'ELSE\r'
            'PrintE("GOOD")\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 32\n"
            "b p0p1qhe0we1ve2r\n"
            "s BAD\n"
            "s GOOD\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 48, 0, 0, 0, 1, 34, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 19, 0, 97, 34, 0, 73, 16, 255, 25, 25, 0, 97,
                38, 0, 73, 16, 255, 97, 43, 0, 73, 16, 255, 73, 32, 255, 66,
                65, 68, 0, 71, 79, 79, 68, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "GOOD\nDONE\n",
    },
    "nested_else": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 1 = 1 THEN\r'
            'IF 1 = 0 THEN\r'
            'PrintE("BAD1")\r'
            'ELSE\r'
            'PrintE("GOOD1")\r'
            'FI\r'
            'ELSE\r'
            'PrintE("BAD2")\r'
            'FI\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 51\n"
            "b p0p1qhp2p3qhe0we1vwe2ve3r\n"
            "s BAD1\n"
            "s GOOD1\n"
            "s BAD2\n"
            "s DONE\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 74, 0, 0, 0, 1, 53, 0, 17, 1, 0, 17,
                1, 0, 22, 24, 38, 0, 17, 1, 0, 17, 0, 0, 22, 24, 29, 0,
                97, 53, 0, 73, 16, 255, 25, 44, 0, 97, 58, 0, 73, 16, 255,
                25, 44, 0, 97, 64, 0, 73, 16, 255, 97, 69, 0, 73, 16, 255,
                73, 32, 255, 66, 65, 68, 49, 0, 71, 79, 79, 68, 49, 0, 66,
                65, 68, 50, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "GOOD1\nDONE\n",
    },
    "do_until": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'PrintE("BODY")\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 23\n"
            "b de0p0p1qtoe1r\n"
            "s BODY\n"
            "s DONE\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 35, 0, 0, 0, 1, 25, 0, 97, 25, 0, 73,
                16, 255, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0, 97, 30, 0, 73,
                16, 255, 73, 32, 255, 66, 79, 68, 89, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "BODY\nDONE\n",
    },
    "do_until_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'DO\r'
            'HELLO()\r'
            'W()\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 23\n"
            "b e0r\n"
            "b dc0u0p0p1qtoe1r\n"
            "u w\n"
            "s HELLO\n"
            "s DONE\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 61, 0, 7, 0, 1, 45, 0, 97, 45, 0, 73,
                16, 255, 72, 69, 0, 0, 69, 32, 0, 17, 1, 0, 17, 1, 0, 22,
                24, 7, 0, 97, 51, 0, 73, 16, 255, 73, 32, 255, 97, 56, 0,
                73, 0, 255, 17, 7, 0, 73, 49, 255, 72, 72, 69, 76, 76, 79,
                0, 68, 79, 78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "HELLO\nTOOL7\nDONE\n",
    },
    "do_until_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'PrintE("YES")\r'
            'ELSE\r'
            'PrintE("BAD")\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 46\n"
            "b dp0p1ap2ghe0we1vp3p4qtoe2r\n"
            "s YES\n"
            "s BAD\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 61, 0, 0, 0, 1, 48, 0, 17, 2, 0, 17, 12,
                0, 20, 17, 10, 0, 29, 24, 23, 0, 97, 48, 0, 73, 16, 255, 25,
                29, 0, 97, 52, 0, 73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24,
                0, 0, 97, 56, 0, 73, 16, 255, 73, 32, 255, 89, 69, 83, 0,
                66, 65, 68, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "YES\nDONE\n",
    },
    "do_until_branch_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-branch-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC BYE()\r'
            'PrintE("BYE")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'HELLO()\r'
            'ELSE\r'
            'BYE()\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x bye 7 7\n"
            "x main 14 40\n"
            "b e0r\n"
            "b e1r\n"
            "b dp0p1ap2ghc0wc1vp3p4qtoe2r\n"
            "s HELLO\n"
            "s BYE\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 71, 0, 14, 0, 1, 56, 0, 97, 56, 0, 73,
                16, 255, 72, 97, 62, 0, 73, 16, 255, 72, 17, 2, 0, 17, 12,
                0, 20, 17, 10, 0, 29, 24, 34, 0, 69, 0, 0, 25, 37, 0, 69,
                7, 0, 17, 1, 0, 17, 1, 0, 22, 24, 14, 0, 97, 66, 0, 73, 16,
                255, 73, 32, 255, 72, 69, 76, 76, 79, 0, 66, 89, 69, 0, 68,
                79, 78, 69, 0,
            ]
        ),
        "expected_console": "HELLO\nDONE\n",
    },
    "do_until_branch_external": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-branch-external",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'W()\r'
            'ELSE\r'
            'PrintE("BAD")\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 43\n"
            "b dp0p1ap2ghu0we0vp3p4qtoe1r\n"
            "u w\n"
            "s BAD\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 72, 0, 0, 0, 1, 58, 0, 17, 2, 0, 17, 12,
                0, 20, 17, 10, 0, 29, 24, 20, 0, 69, 45, 0, 25, 26, 0, 97,
                58, 0, 73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0, 97,
                62, 0, 73, 16, 255, 73, 32, 255, 97, 67, 0, 73, 0, 255, 17,
                7, 0, 73, 49, 255, 72, 66, 65, 68, 0, 68, 79, 78, 69, 0, 84,
                79, 79, 76, 0,
            ]
        ),
        "expected_console": "TOOL7\nDONE\n",
    },
    "nested_if": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-if",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 1 = 1 THEN\r'
            'IF 1 = 0 THEN\r'
            'PrintE("BAD")\r'
            'FI\r'
            'PrintE("INNERDONE")\r'
            'FI\r'
            'PrintE("OUTERDONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 39\n"
            "b p0p1qhp2p3qhe0ve1ve2r\n"
            "s BAD\n"
            "s INNERDONE\n"
            "s OUTERDONE\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 65, 0, 0, 0, 1, 41, 0, 17, 1, 0, 17,
                1, 0, 22, 24, 32, 0, 17, 1, 0, 17, 0, 0, 22, 24, 26, 0,
                97, 41, 0, 73, 16, 255, 97, 45, 0, 73, 16, 255, 97, 55, 0,
                73, 16, 255, 73, 32, 255, 66, 65, 68, 0, 73, 78, 78, 69, 82,
                68, 79, 78, 69, 0, 79, 85, 84, 69, 82, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "INNERDONE\nOUTERDONE\n",
    },
}


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=False,
        capture_output=True,
    )
    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=stdout,
            stderr=stderr,
        )
    return subprocess.CompletedProcess(result.args, result.returncode, stdout, stderr)


def build_current_tools() -> None:
    for script in (
        "build_tool_abi_harness.sh",
        "build_actc_udos.sh",
        "build_alink_udos.sh",
        "build_avmrun_udos.sh",
    ):
        run([str(ROOT / "tools" / script)], cwd=ROOT)


def scenario_sources(scenario: dict) -> dict[str, str]:
    if "sources" in scenario:
        return {name.upper(): source for name, source in scenario["sources"].items()}
    return {"MAIN": scenario["source"]}


def prepare_workspace(base_fs: Path, out_fs: Path, scenario: dict) -> Path:
    project_root = out_fs / "IMAGES" / "ACTION.DNP" / "PROJ3"
    compile_modules = list(scenario_sources(scenario))
    shutil.rmtree(out_fs, ignore_errors=True)
    shutil.copytree(base_fs, out_fs)
    manifest = "ACTION PROJECT\r" + "".join(f"{module}.ACT\r" for module in scenario_sources(scenario))
    (project_root / "ACTION.PROJ").write_text(manifest, encoding="ascii")
    for module, source in scenario_sources(scenario).items():
        (project_root / "src" / f"{module.lower()}.act").write_text(source, encoding="ascii")
    stale_paths = [
        project_root / "bin" / "MAIN.AVM",
        project_root / "bin" / "main.avm",
        project_root / "MAIN.AVM",
        project_root / "main.avm",
    ]
    for module in compile_modules:
        stale_paths.extend(
            [
                project_root / "obj" / f"{module}.AVO",
                project_root / "obj" / f"{module.lower()}.avo",
                project_root / f"{module}.AVO",
                project_root / f"{module.lower()}.avo",
            ]
        )
    for stale in stale_paths:
        if stale.exists():
            stale.unlink()
    return project_root


def run_harness(prg: Path, workspace: Path, cmdline: str, labels: Path, extra: list[str]) -> dict:
    cmd = [
        str(HARNESS),
        "--prg",
        str(prg),
        "--workspace",
        str(workspace),
        "--cmdline",
        cmdline,
        "--services-inc",
        str(SERVICES_INC),
        "--labels",
        str(labels),
        "--max-steps",
        "4000000",
        *extra,
    ]
    result = run(cmd, cwd=ROOT)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"failed to decode harness output for {prg.name}:\n{result.stdout}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def find_last_op(summary: dict, kind: str) -> dict:
    matches = [op for op in summary.get("ops", []) if op.get("kind") == kind]
    require(bool(matches), f"missing {kind!r} operation in harness summary")
    return matches[-1]


def verify_actc(project_root: Path, summary: dict, module: str, expected_avo: str) -> None:
    require(summary["exit_status"] == 0, f"ACTC exited nonzero: {summary['exit_status']}")
    save_op = find_last_op(summary, "save")
    require(save_op["path"] == f"OBJ/{module}.AVO", f"unexpected ACTC save path: {save_op['path']!r}")
    require(save_op["actual_len"] == len(expected_avo.encode("ascii")), f"unexpected ACTC object size: {save_op['actual_len']}")
    output_path = project_root / "obj" / f"{module}.AVO"
    require(output_path.is_file(), f"missing ACTC output: {output_path}")
    text = output_path.read_text(encoding="ascii", errors="replace")
    require(text == expected_avo, f"unexpected ACTC object text:\n{text}")


def verify_alink(project_root: Path, summary: dict, expected_avm: bytes) -> None:
    require(summary["exit_status"] == 0, f"ALINK exited nonzero: {summary['exit_status']}")
    save_op = find_last_op(summary, "save")
    require(save_op["path"] == "BIN/MAIN.AVM", f"unexpected ALINK save path: {save_op['path']!r}")
    require(save_op["actual_len"] == len(expected_avm), f"unexpected ALINK image size: {save_op['actual_len']}")
    output_path = project_root / "bin" / "MAIN.AVM"
    require(output_path.is_file(), f"missing ALINK output: {output_path}")
    data = output_path.read_bytes()
    require(data == expected_avm, f"unexpected ALINK bytes: {list(data)}")


def verify_avmrun(summary: dict, expected_console: str) -> None:
    require(summary["exit_status"] == 0, f"AVMRUN exited nonzero: {summary['exit_status']}")
    require(summary.get("console", "") == expected_console, f"unexpected AVMRUN console: {summary.get('console', '')!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run named ACTC -> ALINK -> AVMRUN harness proofs")
    parser.add_argument("--base-fs", type=Path, default=DEFAULT_BASE_FS)
    parser.add_argument("--out-fs", type=Path)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="additive")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--keep-workspace", action="store_true")
    args = parser.parse_args()
    scenario = SCENARIOS[args.scenario]

    if not args.base_fs.is_dir():
        raise RuntimeError(f"missing base fs tree: {args.base_fs}")

    if not args.skip_build:
        build_current_tools()

    out_fs = args.out_fs if args.out_fs is not None else (UDOS_ROOT / "build" / scenario["out_fs_name"])
    project_root = prepare_workspace(args.base_fs, out_fs, scenario)
    compile_modules = [module.upper() for module in scenario.get("compile_modules", ["MAIN"])]
    raw_expected_objects = scenario["expected_objects"] if "expected_objects" in scenario else {"MAIN": scenario["expected_avo"]}
    expected_objects = {
        module.upper(): expected
        for module, expected in raw_expected_objects.items()
    }

    for module in compile_modules:
        require(module in expected_objects, f"missing expected object text for {module}")
        actc = run_harness(
            ACTC_PRG,
            project_root,
            module,
            ACTC_LABELS,
            ["--op-dump-cstr", "target_path:32", "--op-dump-cstr", "content_buffer:256"],
        )
        verify_actc(project_root, actc, module, expected_objects[module])

    alink = run_harness(
        ALINK_PRG,
        project_root,
        "MAIN",
        ALINK_LABELS,
        ["--op-dump-cstr", "target_path:32", "--op-dump-cstr", "binary_target_path:32", "--op-dump", "content_buffer:80"],
    )
    verify_alink(project_root, alink, scenario["expected_avm"])

    avmrun = run_harness(
        AVMRUN_PRG,
        project_root,
        "BIN/MAIN.AVM",
        AVMRUN_LABELS,
        [],
    )
    verify_avmrun(avmrun, scenario["expected_console"])

    summary = {
        "scenario": args.scenario,
        "workspace": str(project_root),
        "actc_object_path": str(project_root / "obj" / "MAIN.AVO"),
        "alink_image_path": str(project_root / "bin" / "MAIN.AVM"),
        "avmrun_console": avmrun["console"],
    }
    print(json.dumps(summary, indent=2))

    if not args.keep_workspace:
        shutil.rmtree(out_fs, ignore_errors=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
