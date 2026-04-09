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
    "comparison_ops": {
        "out_fs_name": "harness-actc-alink-avmrun-comparison-ops",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintIE(2 <> 3)\r'
            'PrintIE(2 < 3)\r'
            'PrintIE(3 <= 3)\r'
            'PrintIE(4 >= 3)\r'
            'PrintIE(4 <= 3)\r'
            'PrintIE(2 >= 3)\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 77\n"
            "b p0p1nzp2p3lzp4p5gp6qzp7p8lp9qzpApBgpCqzpDpElpFqzr\n"
            "i 2\n"
            "i 3\n"
            "i 2\n"
            "i 3\n"
            "i 3\n"
            "i 3\n"
            "i 0\n"
            "i 4\n"
            "i 3\n"
            "i 0\n"
            "i 4\n"
            "i 3\n"
            "i 0\n"
            "i 2\n"
            "i 3\n"
            "i 0\n"
            "k 6\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 79, 0, 0, 0, 1, 79, 0, 17, 2, 0, 17,
                3, 0, 23, 73, 49, 255, 17, 2, 0, 17, 3, 0, 28, 73, 49,
                255, 17, 3, 0, 17, 3, 0, 29, 17, 0, 0, 22, 73, 49, 255,
                17, 4, 0, 17, 3, 0, 28, 17, 0, 0, 22, 73, 49, 255, 17,
                4, 0, 17, 3, 0, 29, 17, 0, 0, 22, 73, 49, 255, 17, 2, 0,
                17, 3, 0, 28, 17, 0, 0, 22, 73, 49, 255, 73, 32, 255,
            ]
        ),
        "expected_console": "1\n1\n1\n1\n0\n0\n",
    },
    "many_string_indices": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-indices",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintE("A")\r'
            'PrintE("B")\r'
            'PrintE("C")\r'
            'PrintE("D")\r'
            'PrintE("E")\r'
            'PrintE("F")\r'
            'PrintE("G")\r'
            'PrintE("H")\r'
            'PrintE("I")\r'
            'PrintE("J")\r'
            'PrintE("K")\r'
            'PrintE("L")\r'
            'PrintE("M")\r'
            'PrintE("N")\r'
            'PrintE("O")\r'
            'PrintE("P")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 97\n"
            "b e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFr\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 131, 0, 0, 0, 1, 99, 0, 97, 99, 0,
                73, 16, 255, 97, 101, 0, 73, 16, 255, 97, 103, 0, 73,
                16, 255, 97, 105, 0, 73, 16, 255, 97, 107, 0, 73, 16,
                255, 97, 109, 0, 73, 16, 255, 97, 111, 0, 73, 16, 255,
                97, 113, 0, 73, 16, 255, 97, 115, 0, 73, 16, 255, 97,
                117, 0, 73, 16, 255, 97, 119, 0, 73, 16, 255, 97, 121,
                0, 73, 16, 255, 97, 123, 0, 73, 16, 255, 97, 125, 0, 73,
                16, 255, 97, 127, 0, 73, 16, 255, 97, 129, 0, 73, 16,
                255, 73, 32, 255, 65, 0, 66, 0, 67, 0, 68, 0, 69, 0, 70,
                0, 71, 0, 72, 0, 73, 0, 74, 0, 75, 0, 76, 0, 77, 0, 78,
                0, 79, 0, 80, 0,
            ]
        ),
        "expected_console": "A\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n",
    },
    "many_string_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 1 = 0 THEN\r'
            'PrintE("A")\r'
            'PrintE("B")\r'
            'PrintE("C")\r'
            'PrintE("D")\r'
            'PrintE("E")\r'
            'PrintE("F")\r'
            'PrintE("G")\r'
            'PrintE("H")\r'
            'ELSE\r'
            'PrintE("I")\r'
            'PrintE("J")\r'
            'PrintE("K")\r'
            'PrintE("L")\r'
            'PrintE("M")\r'
            'PrintE("N")\r'
            'PrintE("O")\r'
            'PrintE("P")\r'
            'FI\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 110\n"
            "b p0p1qhe0e1e2e3e4e5e6e7we8e9eAeBeCeDeEeFvr\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 144, 0, 0, 0, 1, 112, 0, 17, 1, 0,
                17, 0, 0, 22, 24, 61, 0, 97, 112, 0, 73, 16, 255, 97,
                114, 0, 73, 16, 255, 97, 116, 0, 73, 16, 255, 97, 118,
                0, 73, 16, 255, 97, 120, 0, 73, 16, 255, 97, 122, 0, 73,
                16, 255, 97, 124, 0, 73, 16, 255, 97, 126, 0, 73, 16,
                255, 25, 109, 0, 97, 128, 0, 73, 16, 255, 97, 130, 0, 73,
                16, 255, 97, 132, 0, 73, 16, 255, 97, 134, 0, 73, 16,
                255, 97, 136, 0, 73, 16, 255, 97, 138, 0, 73, 16, 255,
                97, 140, 0, 73, 16, 255, 97, 142, 0, 73, 16, 255, 73,
                32, 255, 65, 0, 66, 0, 67, 0, 68, 0, 69, 0, 70, 0, 71,
                0, 72, 0, 73, 0, 74, 0, 75, 0, 76, 0, 77, 0, 78, 0, 79,
                0, 80, 0,
            ]
        ),
        "expected_console": "I\nJ\nK\nL\nM\nN\nO\nP\n",
    },
    "many_string_do_until": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-do-until",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'PrintE("A")\r'
            'PrintE("B")\r'
            'PrintE("C")\r'
            'PrintE("D")\r'
            'PrintE("E")\r'
            'PrintE("F")\r'
            'PrintE("G")\r'
            'PrintE("H")\r'
            'PrintE("I")\r'
            'PrintE("J")\r'
            'PrintE("K")\r'
            'PrintE("L")\r'
            'PrintE("M")\r'
            'PrintE("N")\r'
            'PrintE("O")\r'
            'PrintE("P")\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 107\n"
            "b de0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFp0p1qtor\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 141, 0, 0, 0, 1, 109, 0, 97, 109, 0,
                73, 16, 255, 97, 111, 0, 73, 16, 255, 97, 113, 0, 73,
                16, 255, 97, 115, 0, 73, 16, 255, 97, 117, 0, 73, 16,
                255, 97, 119, 0, 73, 16, 255, 97, 121, 0, 73, 16, 255,
                97, 123, 0, 73, 16, 255, 97, 125, 0, 73, 16, 255, 97,
                127, 0, 73, 16, 255, 97, 129, 0, 73, 16, 255, 97, 131,
                0, 73, 16, 255, 97, 133, 0, 73, 16, 255, 97, 135, 0, 73,
                16, 255, 97, 137, 0, 73, 16, 255, 97, 139, 0, 73, 16,
                255, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0, 73, 32, 255, 65,
                0, 66, 0, 67, 0, 68, 0, 69, 0, 70, 0, 71, 0, 72, 0, 73,
                0, 74, 0, 75, 0, 76, 0, 77, 0, 78, 0, 79, 0, 80, 0,
            ]
        ),
        "expected_console": "A\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n",
    },
    "many_int_indices": {
        "out_fs_name": "harness-actc-alink-avmrun-many-int-indices",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintIE(0)\r'
            'PrintIE(1)\r'
            'PrintIE(2)\r'
            'PrintIE(3)\r'
            'PrintIE(4)\r'
            'PrintIE(5)\r'
            'PrintIE(6)\r'
            'PrintIE(7)\r'
            'PrintIE(8)\r'
            'PrintIE(9)\r'
            'PrintIE(10)\r'
            'PrintIE(11)\r'
            'PrintIE(12)\r'
            'PrintIE(13)\r'
            'PrintIE(14)\r'
            'PrintIE(15)\r'
            'PrintIE(16)\r'
            'PrintIE(17)\r'
            'PrintIE(18)\r'
            'PrintIE(19)\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 121\n"
            "b i0i1i2i3i4i5i6i7i8i9iAiBiCiDiEiFiGiHiIiJr\n"
            "i 0\n"
            "i 1\n"
            "i 2\n"
            "i 3\n"
            "i 4\n"
            "i 5\n"
            "i 6\n"
            "i 7\n"
            "i 8\n"
            "i 9\n"
            "i 10\n"
            "i 11\n"
            "i 12\n"
            "i 13\n"
            "i 14\n"
            "i 15\n"
            "i 16\n"
            "i 17\n"
            "i 18\n"
            "i 19\n"
            "k 6\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 123, 0, 0, 0, 1, 123, 0, 17, 0, 0,
                73, 49, 255, 17, 1, 0, 73, 49, 255, 17, 2, 0, 73, 49,
                255, 17, 3, 0, 73, 49, 255, 17, 4, 0, 73, 49, 255, 17,
                5, 0, 73, 49, 255, 17, 6, 0, 73, 49, 255, 17, 7, 0, 73,
                49, 255, 17, 8, 0, 73, 49, 255, 17, 9, 0, 73, 49, 255,
                17, 10, 0, 73, 49, 255, 17, 11, 0, 73, 49, 255, 17, 12,
                0, 73, 49, 255, 17, 13, 0, 73, 49, 255, 17, 14, 0, 73,
                49, 255, 17, 15, 0, 73, 49, 255, 17, 16, 0, 73, 49, 255,
                17, 17, 0, 73, 49, 255, 17, 18, 0, 73, 49, 255, 17, 19,
                0, 73, 49, 255, 73, 32, 255,
            ]
        ),
        "expected_console": "0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n",
    },
    "many_int_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-many-int-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 1 = 0 THEN\r'
            'PrintIE(0)\r'
            'PrintIE(1)\r'
            'PrintIE(2)\r'
            'PrintIE(3)\r'
            'PrintIE(4)\r'
            'PrintIE(5)\r'
            'PrintIE(6)\r'
            'PrintIE(7)\r'
            'ELSE\r'
            'PrintIE(8)\r'
            'PrintIE(9)\r'
            'PrintIE(10)\r'
            'PrintIE(11)\r'
            'PrintIE(12)\r'
            'PrintIE(13)\r'
            'PrintIE(14)\r'
            'PrintIE(15)\r'
            'FI\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 110\n"
            "b p0p1qhi2i3i4i5i6i7i8i9wiAiBiCiDiEiFiGiHvr\n"
            "i 1\n"
            "i 0\n"
            "i 0\n"
            "i 1\n"
            "i 2\n"
            "i 3\n"
            "i 4\n"
            "i 5\n"
            "i 6\n"
            "i 7\n"
            "i 8\n"
            "i 9\n"
            "i 10\n"
            "i 11\n"
            "i 12\n"
            "i 13\n"
            "i 14\n"
            "i 15\n"
            "k 6\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 112, 0, 0, 0, 1, 112, 0, 17, 1, 0,
                17, 0, 0, 22, 24, 61, 0, 17, 0, 0, 73, 49, 255, 17, 1,
                0, 73, 49, 255, 17, 2, 0, 73, 49, 255, 17, 3, 0, 73, 49,
                255, 17, 4, 0, 73, 49, 255, 17, 5, 0, 73, 49, 255, 17,
                6, 0, 73, 49, 255, 17, 7, 0, 73, 49, 255, 25, 109, 0, 17,
                8, 0, 73, 49, 255, 17, 9, 0, 73, 49, 255, 17, 10, 0, 73,
                49, 255, 17, 11, 0, 73, 49, 255, 17, 12, 0, 73, 49, 255,
                17, 13, 0, 73, 49, 255, 17, 14, 0, 73, 49, 255, 17, 15,
                0, 73, 49, 255, 73, 32, 255,
            ]
        ),
        "expected_console": "8\n9\n10\n11\n12\n13\n14\n15\n",
    },
    "comparison_ops_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-comparison-ops-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 2 <> 3 THEN\r'
            'PrintE("NE")\r'
            'FI\r'
            'IF 2 < 3 THEN\r'
            'PrintE("LT")\r'
            'FI\r'
            'IF 3 <= 3 THEN\r'
            'PrintE("LE")\r'
            'FI\r'
            'IF 4 >= 3 THEN\r'
            'PrintE("GE")\r'
            'FI\r'
            'IF 4 <= 3 THEN\r'
            'PrintE("BAD1")\r'
            'FI\r'
            'IF 2 >= 3 THEN\r'
            'PrintE("BAD2")\r'
            'FI\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 113\n"
            "b p0p1nhe0vp2p3lhe1vp4p5gp6qhe2vp7p8lp9qhe3vpApBgpCqhe4vpDpElpFqhe5vr\n"
            "s NE\n"
            "s LT\n"
            "s LE\n"
            "s GE\n"
            "s BAD1\n"
            "s BAD2\n"
            "i 2\n"
            "i 3\n"
            "i 2\n"
            "i 3\n"
            "i 3\n"
            "i 3\n"
            "i 0\n"
            "i 4\n"
            "i 3\n"
            "i 0\n"
            "i 4\n"
            "i 3\n"
            "i 0\n"
            "i 2\n"
            "i 3\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 137, 0, 0, 0, 1, 115, 0, 17, 2, 0,
                17, 3, 0, 23, 24, 16, 0, 97, 115, 0, 73, 16, 255, 17, 2,
                0, 17, 3, 0, 28, 24, 32, 0, 97, 118, 0, 73, 16, 255, 17,
                3, 0, 17, 3, 0, 29, 17, 0, 0, 22, 24, 52, 0, 97, 121, 0,
                73, 16, 255, 17, 4, 0, 17, 3, 0, 28, 17, 0, 0, 22, 24,
                72, 0, 97, 124, 0, 73, 16, 255, 17, 4, 0, 17, 3, 0, 29,
                17, 0, 0, 22, 24, 92, 0, 97, 127, 0, 73, 16, 255, 17, 2,
                0, 17, 3, 0, 28, 17, 0, 0, 22, 24, 112, 0, 97, 132, 0,
                73, 16, 255, 73, 32, 255, 78, 69, 0, 76, 84, 0, 76, 69,
                0, 71, 69, 0, 66, 65, 68, 49, 0, 66, 65, 68, 50, 0,
            ]
        ),
        "expected_console": "NE\nLT\nLE\nGE\n",
    },
    "comparison_ops_loops": {
        "out_fs_name": "harness-actc-alink-avmrun-comparison-ops-loops",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'PrintE("DO")\r'
            'UNTIL 3 <= 3\r'
            'OD\r'
            'WHILE 2 >= 3 DO\r'
            'PrintE("BAD")\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 50\n"
            "b de0p0p1gp2qtodp3p4lp5qfe1xe2r\n"
            "s DO\n"
            "s BAD\n"
            "s DONE\n"
            "i 3\n"
            "i 3\n"
            "i 0\n"
            "i 2\n"
            "i 3\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 64, 0, 0, 0, 1, 52, 0, 97, 52, 0, 73,
                16, 255, 17, 3, 0, 17, 3, 0, 29, 17, 0, 0, 22, 24, 0, 0,
                17, 2, 0, 17, 3, 0, 28, 17, 0, 0, 22, 24, 43, 0, 97, 55,
                0, 73, 16, 255, 25, 20, 0, 97, 59, 0, 73, 16, 255, 73,
                32, 255, 68, 79, 0, 66, 65, 68, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "DO\nDONE\n",
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
    "comparison_ops_branch_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-comparison-ops-branch-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'IF 2 < 3 THEN\r'
            'HELLO()\r'
            'FI\r'
            'IF 2 >= 3 THEN\r'
            'PrintE("BAD")\r'
            'ELSE\r'
            'PrintE("OK")\r'
            'FI\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 43\n"
            "b e0r\n"
            "b p0p1lhc0vp2p3lp4qhe1we2vr\n"
            "s HELLO\n"
            "s BAD\n"
            "s OK\n"
            "i 2\n"
            "i 3\n"
            "i 2\n"
            "i 3\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 65, 0, 7, 0, 1, 52, 0, 97, 52, 0, 73,
                16, 255, 72, 17, 2, 0, 17, 3, 0, 28, 24, 20, 0, 69, 0,
                0, 17, 2, 0, 17, 3, 0, 28, 17, 0, 0, 22, 24, 43, 0, 97,
                58, 0, 73, 16, 255, 25, 49, 0, 97, 62, 0, 73, 16, 255,
                73, 32, 255, 72, 69, 76, 76, 79, 0, 66, 65, 68, 0, 79,
                75, 0,
            ]
        ),
        "expected_console": "HELLO\nOK\n",
    },
    "many_string_branch_external": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-branch-external",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 1 = 1 THEN\r'
            'W()\r'
            'PrintE("A")\r'
            'PrintE("B")\r'
            'PrintE("C")\r'
            'PrintE("D")\r'
            'PrintE("E")\r'
            'PrintE("F")\r'
            'PrintE("G")\r'
            'PrintE("H")\r'
            'PrintE("I")\r'
            'PrintE("J")\r'
            'PrintE("K")\r'
            'PrintE("L")\r'
            'ELSE\r'
            'PrintE("BAD")\r'
            'FI\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 95\n"
            "b p0p1qhu0e0e1e2e3e4e5e6e7e8e9eAeBweCvr\n"
            "u w\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 143, 0, 0, 0, 1, 110, 0, 17, 1, 0,
                17, 1, 0, 22, 24, 88, 0, 69, 97, 0, 97, 110, 0, 73, 16,
                255, 97, 112, 0, 73, 16, 255, 97, 114, 0, 73, 16, 255,
                97, 116, 0, 73, 16, 255, 97, 118, 0, 73, 16, 255, 97,
                120, 0, 73, 16, 255, 97, 122, 0, 73, 16, 255, 97, 124,
                0, 73, 16, 255, 97, 126, 0, 73, 16, 255, 97, 128, 0, 73,
                16, 255, 97, 130, 0, 73, 16, 255, 97, 132, 0, 73, 16,
                255, 25, 94, 0, 97, 134, 0, 73, 16, 255, 73, 32, 255,
                97, 138, 0, 73, 0, 255, 17, 7, 0, 73, 49, 255, 72, 65,
                0, 66, 0, 67, 0, 68, 0, 69, 0, 70, 0, 71, 0, 72, 0, 73,
                0, 74, 0, 75, 0, 76, 0, 66, 65, 68, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "TOOL7\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\n",
    },
    "many_string_do_until_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-do-until-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'IF 1 = 0 THEN\r'
            'PrintE("A")\r'
            'PrintE("B")\r'
            'PrintE("C")\r'
            'PrintE("D")\r'
            'PrintE("E")\r'
            'PrintE("F")\r'
            'PrintE("G")\r'
            'PrintE("H")\r'
            'ELSE\r'
            'PrintE("I")\r'
            'PrintE("J")\r'
            'PrintE("K")\r'
            'PrintE("L")\r'
            'PrintE("M")\r'
            'PrintE("N")\r'
            'PrintE("O")\r'
            'PrintE("P")\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 120\n"
            "b dp0p1qhe0e1e2e3e4e5e6e7we8e9eAeBeCeDeEeFvp2p3qtor\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 154, 0, 0, 0, 1, 122, 0, 17, 1, 0,
                17, 0, 0, 22, 24, 61, 0, 97, 122, 0, 73, 16, 255, 97,
                124, 0, 73, 16, 255, 97, 126, 0, 73, 16, 255, 97, 128,
                0, 73, 16, 255, 97, 130, 0, 73, 16, 255, 97, 132, 0, 73,
                16, 255, 97, 134, 0, 73, 16, 255, 97, 136, 0, 73, 16,
                255, 25, 109, 0, 97, 138, 0, 73, 16, 255, 97, 140, 0, 73,
                16, 255, 97, 142, 0, 73, 16, 255, 97, 144, 0, 73, 16,
                255, 97, 146, 0, 73, 16, 255, 97, 148, 0, 73, 16, 255,
                97, 150, 0, 73, 16, 255, 97, 152, 0, 73, 16, 255, 17,
                1, 0, 17, 1, 0, 22, 24, 0, 0, 73, 32, 255, 65, 0, 66, 0,
                67, 0, 68, 0, 69, 0, 70, 0, 71, 0, 72, 0, 73, 0, 74, 0,
                75, 0, 76, 0, 77, 0, 78, 0, 79, 0, 80, 0,
            ]
        ),
        "expected_console": "I\nJ\nK\nL\nM\nN\nO\nP\n",
    },
    "many_int_do_until_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-many-int-do-until-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'IF 1 = 0 THEN\r'
            'PrintIE(0)\r'
            'PrintIE(1)\r'
            'PrintIE(2)\r'
            'PrintIE(3)\r'
            'PrintIE(4)\r'
            'PrintIE(5)\r'
            'PrintIE(6)\r'
            'PrintIE(7)\r'
            'ELSE\r'
            'PrintIE(8)\r'
            'PrintIE(9)\r'
            'PrintIE(10)\r'
            'PrintIE(11)\r'
            'PrintIE(12)\r'
            'PrintIE(13)\r'
            'PrintIE(14)\r'
            'PrintIE(15)\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 120\n"
            "b dp0p1qhi2i3i4i5i6i7i8i9wiAiBiCiDiEiFiGiHvpIpJqtor\n"
            "i 1\n"
            "i 0\n"
            "i 0\n"
            "i 1\n"
            "i 2\n"
            "i 3\n"
            "i 4\n"
            "i 5\n"
            "i 6\n"
            "i 7\n"
            "i 8\n"
            "i 9\n"
            "i 10\n"
            "i 11\n"
            "i 12\n"
            "i 13\n"
            "i 14\n"
            "i 15\n"
            "i 1\n"
            "i 1\n"
            "k 6\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 122, 0, 0, 0, 1, 122, 0, 17, 1, 0,
                17, 0, 0, 22, 24, 61, 0, 17, 0, 0, 73, 49, 255, 17, 1,
                0, 73, 49, 255, 17, 2, 0, 73, 49, 255, 17, 3, 0, 73, 49,
                255, 17, 4, 0, 73, 49, 255, 17, 5, 0, 73, 49, 255, 17,
                6, 0, 73, 49, 255, 17, 7, 0, 73, 49, 255, 25, 109, 0, 17,
                8, 0, 73, 49, 255, 17, 9, 0, 73, 49, 255, 17, 10, 0, 73,
                49, 255, 17, 11, 0, 73, 49, 255, 17, 12, 0, 73, 49, 255,
                17, 13, 0, 73, 49, 255, 17, 14, 0, 73, 49, 255, 17, 15,
                0, 73, 49, 255, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0, 73, 32,
                255,
            ]
        ),
        "expected_console": "8\n9\n10\n11\n12\n13\n14\n15\n",
    },
    "many_string_branch_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-branch-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 1 = 1 THEN\r'
                'W()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'PrintE("K")\r'
                'PrintE("L")\r'
                'ELSE\r'
                'PrintE("BAD")\r'
                'FI\r'
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
                "x main 0 95\n"
                "b p0p1qhu0e0e1e2e3e4e5e6e7e8e9eAeBweCvr\n"
                "u w\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "s K\n"
                "s L\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 95\n"
            "b p0p1qhu0e0e1e2e3e4e5e6e7e8e9eAeBweCvr\n"
            "u w\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 150, 0, 0, 0, 1, 114, 0, 17, 1, 0,
                17, 1, 0, 22, 24, 88, 0, 69, 97, 0, 97, 114, 0, 73, 16,
                255, 97, 116, 0, 73, 16, 255, 97, 118, 0, 73, 16, 255,
                97, 120, 0, 73, 16, 255, 97, 122, 0, 73, 16, 255, 97,
                124, 0, 73, 16, 255, 97, 126, 0, 73, 16, 255, 97, 128,
                0, 73, 16, 255, 97, 130, 0, 73, 16, 255, 97, 132, 0, 73,
                16, 255, 97, 134, 0, 73, 16, 255, 97, 136, 0, 73, 16,
                255, 25, 94, 0, 97, 138, 0, 73, 16, 255, 73, 32, 255, 97,
                142, 0, 73, 16, 255, 69, 107, 0, 72, 97, 146, 0, 73, 16,
                255, 72, 65, 0, 66, 0, 67, 0, 68, 0, 69, 0, 70, 0, 71, 0,
                72, 0, 73, 0, 74, 0, 75, 0, 76, 0, 66, 65, 68, 0, 77, 73,
                68, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "MID\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\n",
    },
    "many_string_nested_loops_external": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-nested-loops-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'DO\r'
                'WHILE 1 = 0 DO\r'
                'PrintE("BAD")\r'
                'OD\r'
                'W()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("TOOL7")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 93\n"
                "b ddp0p1qfe0xu0e1e2e3e4e5e6e7e8e9eAp2p3qtor\n"
                "u w\n"
                "s BAD\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "i 1\n"
                "i 0\n"
                "i 1\n"
                "i 1\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s TOOL7\n"
                "k 2\n"
                "n w\n"
            ),
        },
        "expected_avo": (
            "AVO1\n"
            "x main 0 93\n"
            "b ddp0p1qfe0xu0e1e2e3e4e5e6e7e8e9eAp2p3qtor\n"
            "u w\n"
            "s BAD\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 132, 0, 0, 0, 1, 102, 0, 17, 1, 0,
                17, 0, 0, 22, 24, 19, 0, 97, 102, 0, 73, 16, 255, 25,
                0, 0, 69, 95, 0, 97, 106, 0, 73, 16, 255, 97, 108, 0,
                73, 16, 255, 97, 110, 0, 73, 16, 255, 97, 112, 0, 73,
                16, 255, 97, 114, 0, 73, 16, 255, 97, 116, 0, 73, 16,
                255, 97, 118, 0, 73, 16, 255, 97, 120, 0, 73, 16, 255,
                97, 122, 0, 73, 16, 255, 97, 124, 0, 73, 16, 255, 17,
                1, 0, 17, 1, 0, 22, 24, 0, 0, 73, 32, 255, 97, 126, 0,
                73, 16, 255, 72, 66, 65, 68, 0, 65, 0, 66, 0, 67, 0, 68,
                0, 69, 0, 70, 0, 71, 0, 72, 0, 73, 0, 74, 0, 84, 79, 79,
                76, 55, 0,
            ]
        ),
        "expected_console": "TOOL7\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\n",
    },
    "many_string_branch_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-branch-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 1 = 1 THEN\r'
                'W()\r'
                'Q()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'PrintE("K")\r'
                'PrintE("L")\r'
                'ELSE\r'
                'PrintE("BAD")\r'
                'FI\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 98\n"
                "b p0p1qhu0u1e0e1e2e3e4e5e6e7e8e9eAeBweCvr\n"
                "u w\n"
                "u q\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "s K\n"
                "s L\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 98\n"
            "b p0p1qhu0u1e0e1e2e3e4e5e6e7e8e9eAeBweCvr\n"
            "u w\n"
            "u q\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 169, 0, 0, 0, 1, 127, 0, 17, 1, 0,
                17, 1, 0, 22, 24, 91, 0, 69, 100, 0, 69, 110, 0, 97, 127,
                0, 73, 16, 255, 97, 129, 0, 73, 16, 255, 97, 131, 0, 73,
                16, 255, 97, 133, 0, 73, 16, 255, 97, 135, 0, 73, 16, 255,
                97, 137, 0, 73, 16, 255, 97, 139, 0, 73, 16, 255, 97, 141,
                0, 73, 16, 255, 97, 143, 0, 73, 16, 255, 97, 145, 0, 73,
                16, 255, 97, 147, 0, 73, 16, 255, 97, 149, 0, 73, 16, 255,
                25, 97, 0, 97, 151, 0, 73, 16, 255, 73, 32, 255, 97, 155,
                0, 73, 16, 255, 69, 120, 0, 72, 97, 160, 0, 73, 16, 255,
                69, 120, 0, 72, 97, 165, 0, 73, 16, 255, 72, 65, 0, 66, 0,
                67, 0, 68, 0, 69, 0, 70, 0, 71, 0, 72, 0, 73, 0, 74, 0,
                75, 0, 76, 0, 66, 65, 68, 0, 77, 73, 68, 49, 0, 77, 73, 68,
                50, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\n",
    },
    "many_string17_branch_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string17-branch-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 1 = 1 THEN\r'
                'W()\r'
                'Q()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'PrintE("K")\r'
                'PrintE("L")\r'
                'PrintE("M")\r'
                'PrintE("N")\r'
                'PrintE("O")\r'
                'PrintE("P")\r'
                'ELSE\r'
                'PrintE("BAD")\r'
                'FI\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 122\n"
                "b p0p1qhu0u1e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFweGvr\n"
                "u w\n"
                "u q\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "s K\n"
                "s L\n"
                "s M\n"
                "s N\n"
                "s O\n"
                "s P\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 122\n"
            "b p0p1qhu0u1e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFweGvr\n"
            "u w\n"
            "u q\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 201, 0, 0, 0, 1, 151, 0, 17, 1, 0,
                17, 1, 0, 22, 24, 115, 0, 69, 124, 0, 69, 134, 0, 97,
                151, 0, 73, 16, 255, 97, 153, 0, 73, 16, 255, 97, 155,
                0, 73, 16, 255, 97, 157, 0, 73, 16, 255, 97, 159, 0, 73,
                16, 255, 97, 161, 0, 73, 16, 255, 97, 163, 0, 73, 16,
                255, 97, 165, 0, 73, 16, 255, 97, 167, 0, 73, 16, 255,
                97, 169, 0, 73, 16, 255, 97, 171, 0, 73, 16, 255, 97,
                173, 0, 73, 16, 255, 97, 175, 0, 73, 16, 255, 97, 177,
                0, 73, 16, 255, 97, 179, 0, 73, 16, 255, 97, 181, 0, 73,
                16, 255, 25, 121, 0, 97, 183, 0, 73, 16, 255, 73, 32,
                255, 97, 187, 0, 73, 16, 255, 69, 144, 0, 72, 97, 192,
                0, 73, 16, 255, 69, 144, 0, 72, 97, 197, 0, 73, 16, 255,
                72, 65, 0, 66, 0, 67, 0, 68, 0, 69, 0, 70, 0, 71, 0, 72,
                0, 73, 0, 74, 0, 75, 0, 76, 0, 77, 0, 78, 0, 79, 0, 80,
                0, 66, 65, 68, 0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0,
                69, 78, 68, 0,
            ]
        ),
        "expected_console": "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n",
    },
    "dense_return_branch_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-dense-return-branch-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 1 = 1 THEN\r'
                'W()\r'
                'Q()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'PrintE("K")\r'
                'PrintE("L")\r'
                'PrintE("M")\r'
                'PrintE("N")\r'
                'PrintE("O")\r'
                'PrintE("P")\r'
                'RETURN\r'
                'ELSE\r'
                'PrintE("BAD")\r'
                'FI\r'
                'PrintE("TAIL")\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 129\n"
                "b p0p1qhu0u1e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFrweGveHr\n"
                "u w\n"
                "u q\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "s K\n"
                "s L\n"
                "s M\n"
                "s N\n"
                "s O\n"
                "s P\n"
                "s BAD\n"
                "s TAIL\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 129\n"
            "b p0p1qhu0u1e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFrweGveHr\n"
            "u w\n"
            "u q\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "s BAD\n"
            "s TAIL\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 215, 0, 0, 0, 1, 160, 0, 17, 1, 0,
                17, 1, 0, 22, 24, 118, 0, 69, 133, 0, 69, 143, 0, 97,
                160, 0, 73, 16, 255, 97, 162, 0, 73, 16, 255, 97, 164,
                0, 73, 16, 255, 97, 166, 0, 73, 16, 255, 97, 168, 0, 73,
                16, 255, 97, 170, 0, 73, 16, 255, 97, 172, 0, 73, 16,
                255, 97, 174, 0, 73, 16, 255, 97, 176, 0, 73, 16, 255,
                97, 178, 0, 73, 16, 255, 97, 180, 0, 73, 16, 255, 97,
                182, 0, 73, 16, 255, 97, 184, 0, 73, 16, 255, 97, 186,
                0, 73, 16, 255, 97, 188, 0, 73, 16, 255, 97, 190, 0, 73,
                16, 255, 25, 130, 0, 25, 124, 0, 97, 192, 0, 73, 16, 255,
                97, 196, 0, 73, 16, 255, 73, 32, 255, 97, 201, 0, 73, 16,
                255, 69, 153, 0, 72, 97, 206, 0, 73, 16, 255, 69, 153, 0,
                72, 97, 211, 0, 73, 16, 255, 72, 65, 0, 66, 0, 67, 0, 68,
                0, 69, 0, 70, 0, 71, 0, 72, 0, 73, 0, 74, 0, 75, 0, 76,
                0, 77, 0, 78, 0, 79, 0, 80, 0, 66, 65, 68, 0, 84, 65, 73,
                76, 0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0, 69, 78, 68,
                0,
            ]
        ),
        "expected_console": "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n",
    },
    "many_string_do_until_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-do-until-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'DO\r'
                'W()\r'
                'Q()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'UNTIL 1 = 1\r'
                'OD\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 77\n"
                "b du0u1e0e1e2e3e4e5e6e7e8e9p0p1qtor\n"
                "u w\n"
                "u q\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 77\n"
            "b du0u1e0e1e2e3e4e5e6e7e8e9p0p1qtor\n"
            "u w\n"
            "u q\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 140, 0, 0, 0, 1, 106, 0, 69, 79, 0,
                69, 89, 0, 97, 106, 0, 73, 16, 255, 97, 108, 0, 73, 16,
                255, 97, 110, 0, 73, 16, 255, 97, 112, 0, 73, 16, 255, 97,
                114, 0, 73, 16, 255, 97, 116, 0, 73, 16, 255, 97, 118, 0,
                73, 16, 255, 97, 120, 0, 73, 16, 255, 97, 122, 0, 73, 16,
                255, 97, 124, 0, 73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24,
                0, 0, 73, 32, 255, 97, 126, 0, 73, 16, 255, 69, 99, 0, 72,
                97, 131, 0, 73, 16, 255, 69, 99, 0, 72, 97, 136, 0, 73, 16,
                255, 72, 65, 0, 66, 0, 67, 0, 68, 0, 69, 0, 70, 0, 71, 0,
                72, 0, 73, 0, 74, 0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0,
                69, 78, 68, 0,
            ]
        ),
        "expected_console": "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\n",
    },
    "many_string_nested_branch_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-nested-branch-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 1 = 1 THEN\r'
                'IF 2 + 3 * 4 > 10 THEN\r'
                'W()\r'
                'Q()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'ELSE\r'
                'PrintE("BAD1")\r'
                'FI\r'
                'ELSE\r'
                'PrintE("BAD2")\r'
                'FI\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 97\n"
                "b p0p1qhp2p3ap4ghu0u1e0e1e2e3e4e5e6e7we8vwe9vr\n"
                "u w\n"
                "u q\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s BAD1\n"
                "s BAD2\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 97\n"
            "b p0p1qhp2p3ap4ghu0u1e0e1e2e3e4e5e6e7we8vwe9vr\n"
            "u w\n"
            "u q\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s BAD1\n"
            "s BAD2\n"
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
                65, 86, 77, 49, 2, 166, 0, 0, 0, 1, 126, 0, 17, 1, 0, 17,
                1, 0, 22, 24, 90, 0, 17, 2, 0, 17, 12, 0, 20, 17, 10, 0,
                29, 24, 81, 0, 69, 99, 0, 69, 109, 0, 97, 126, 0, 73, 16,
                255, 97, 128, 0, 73, 16, 255, 97, 130, 0, 73, 16, 255, 97,
                132, 0, 73, 16, 255, 97, 134, 0, 73, 16, 255, 97, 136, 0,
                73, 16, 255, 97, 138, 0, 73, 16, 255, 97, 140, 0, 73, 16,
                255, 25, 87, 0, 97, 142, 0, 73, 16, 255, 25, 96, 0, 97,
                147, 0, 73, 16, 255, 73, 32, 255, 97, 152, 0, 73, 16, 255,
                69, 119, 0, 72, 97, 157, 0, 73, 16, 255, 69, 119, 0, 72,
                97, 162, 0, 73, 16, 255, 72, 65, 0, 66, 0, 67, 0, 68, 0,
                69, 0, 70, 0, 71, 0, 72, 0, 66, 65, 68, 49, 0, 66, 65, 68,
                50, 0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\n",
    },
    "many_int_nested_loops_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-many-int-nested-loops-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'WHILE 1 = 0 DO\r'
            'OD\r'
            'IF 1 = 0 THEN\r'
            'PrintIE(0)\r'
            'PrintIE(1)\r'
            'PrintIE(2)\r'
            'PrintIE(3)\r'
            'PrintIE(4)\r'
            'PrintIE(5)\r'
            'PrintIE(6)\r'
            'PrintIE(7)\r'
            'ELSE\r'
            'PrintIE(8)\r'
            'PrintIE(9)\r'
            'PrintIE(10)\r'
            'PrintIE(11)\r'
            'PrintIE(12)\r'
            'PrintIE(13)\r'
            'PrintIE(14)\r'
            'PrintIE(15)\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 133\n"
            "b ddp0p1qfxp2p3qhi4i5i6i7i8i9iAiBwiCiDiEiFiGiHiIiJvpKpLqtor\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 0\n"
            "i 0\n"
            "i 1\n"
            "i 2\n"
            "i 3\n"
            "i 4\n"
            "i 5\n"
            "i 6\n"
            "i 7\n"
            "i 8\n"
            "i 9\n"
            "i 10\n"
            "i 11\n"
            "i 12\n"
            "i 13\n"
            "i 14\n"
            "i 15\n"
            "i 1\n"
            "i 1\n"
            "k 6\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 135, 0, 0, 0, 1, 135, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 13, 0, 25, 0, 0, 17, 1, 0, 17, 0, 0, 22, 24,
                74, 0, 17, 0, 0, 73, 49, 255, 17, 1, 0, 73, 49, 255, 17, 2,
                0, 73, 49, 255, 17, 3, 0, 73, 49, 255, 17, 4, 0, 73, 49,
                255, 17, 5, 0, 73, 49, 255, 17, 6, 0, 73, 49, 255, 17, 7,
                0, 73, 49, 255, 25, 122, 0, 17, 8, 0, 73, 49, 255, 17, 9,
                0, 73, 49, 255, 17, 10, 0, 73, 49, 255, 17, 11, 0, 73, 49,
                255, 17, 12, 0, 73, 49, 255, 17, 13, 0, 73, 49, 255, 17,
                14, 0, 73, 49, 255, 17, 15, 0, 73, 49, 255, 17, 1, 0, 17,
                1, 0, 22, 24, 0, 0, 73, 32, 255,
            ]
        ),
        "expected_console": "8\n9\n10\n11\n12\n13\n14\n15\n",
    },
    "many_string_nested_loops_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-many-string-nested-loops-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'WHILE 1 = 0 DO\r'
            'OD\r'
            'IF 1 = 0 THEN\r'
            'PrintE("A")\r'
            'PrintE("B")\r'
            'PrintE("C")\r'
            'PrintE("D")\r'
            'PrintE("E")\r'
            'PrintE("F")\r'
            'PrintE("G")\r'
            'PrintE("H")\r'
            'ELSE\r'
            'PrintE("I")\r'
            'PrintE("J")\r'
            'PrintE("K")\r'
            'PrintE("L")\r'
            'PrintE("M")\r'
            'PrintE("N")\r'
            'PrintE("O")\r'
            'PrintE("P")\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 133\n"
            "b ddp0p1qfxp2p3qhe0e1e2e3e4e5e6e7we8e9eAeBeCeDeEeFvp4p5qtor\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 167, 0, 0, 0, 1, 135, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 13, 0, 25, 0, 0, 17, 1, 0, 17, 0, 0, 22, 24,
                74, 0, 97, 135, 0, 73, 16, 255, 97, 137, 0, 73, 16, 255,
                97, 139, 0, 73, 16, 255, 97, 141, 0, 73, 16, 255, 97, 143,
                0, 73, 16, 255, 97, 145, 0, 73, 16, 255, 97, 147, 0, 73,
                16, 255, 97, 149, 0, 73, 16, 255, 25, 122, 0, 97, 151, 0,
                73, 16, 255, 97, 153, 0, 73, 16, 255, 97, 155, 0, 73, 16,
                255, 97, 157, 0, 73, 16, 255, 97, 159, 0, 73, 16, 255, 97,
                161, 0, 73, 16, 255, 97, 163, 0, 73, 16, 255, 97, 165, 0,
                73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0, 73, 32, 255,
                65, 0, 66, 0, 67, 0, 68, 0, 69, 0, 70, 0, 71, 0, 72, 0, 73,
                0, 74, 0, 75, 0, 76, 0, 77, 0, 78, 0, 79, 0, 80, 0,
            ]
        ),
        "expected_console": "I\nJ\nK\nL\nM\nN\nO\nP\n",
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
                12, 0, 20, 17, 10, 0, 29, 24, 51, 0, 69, 0, 0, 25, 54, 0,
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
                17, 12, 0, 20, 17, 10, 0, 29, 24, 37, 0, 69, 58, 0, 25, 43,
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
                97, 53, 0, 73, 16, 255, 25, 35, 0, 97, 58, 0, 73, 16, 255,
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
    "nested_do_until": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-do-until",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'PrintE("OUTER")\r'
            'DO\r'
            'PrintE("INNER")\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 39\n"
            "b de0de1p0p1qtop2p3qtoe2r\n"
            "s OUTER\n"
            "s INNER\n"
            "s DONE\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 58, 0, 0, 0, 1, 41, 0, 97, 41, 0, 73,
                16, 255, 97, 47, 0, 73, 16, 255, 17, 1, 0, 17, 1, 0, 22,
                24, 6, 0, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0, 97, 53, 0, 73,
                16, 255, 73, 32, 255, 79, 85, 84, 69, 82, 0, 73, 78, 78,
                69, 82, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "OUTER\nINNER\nDONE\n",
    },
    "nested_do_until_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-do-until-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'DO\r'
            'HELLO()\r'
            'DO\r'
            'W()\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 33\n"
            "b e0r\n"
            "b dc0du0p0p1qtop2p3qtoe1r\n"
            "u w\n"
            "s HELLO\n"
            "s DONE\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 71, 0, 7, 0, 1, 55, 0, 97, 55, 0, 73,
                16, 255, 72, 69, 0, 0, 69, 42, 0, 17, 1, 0, 17, 1, 0, 22,
                24, 10, 0, 17, 1, 0, 17, 1, 0, 22, 24, 7, 0, 97, 61, 0, 73,
                16, 255, 73, 32, 255, 97, 66, 0, 73, 0, 255, 17, 7, 0, 73,
                49, 255, 72, 72, 69, 76, 76, 79, 0, 68, 79, 78, 69, 0, 84,
                79, 79, 76, 0,
            ]
        ),
        "expected_console": "HELLO\nTOOL7\nDONE\n",
    },
    "nested_do_until_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-do-until-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'PrintE("OUTER")\r'
            'FI\r'
            'DO\r'
            'IF 1 = 1 THEN\r'
            'PrintE("INNER")\r'
            'ELSE\r'
            'PrintE("BAD")\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 72\n"
            "b dp0p1ap2ghe0vdp3p4qhe1we2vp5p6qtop7p8qtoe3r\n"
            "s OUTER\n"
            "s INNER\n"
            "s BAD\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 95, 0, 0, 0, 1, 74, 0, 17, 2, 0, 17,
                12, 0, 20, 17, 10, 0, 29, 24, 20, 0, 97, 74, 0, 73, 16,
                255, 17, 1, 0, 17, 1, 0, 22, 24, 39, 0, 97, 80, 0, 73, 16,
                255, 25, 45, 0, 97, 86, 0, 73, 16, 255, 17, 1, 0, 17, 1,
                0, 22, 24, 20, 0, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0, 97,
                90, 0, 73, 16, 255, 73, 32, 255, 79, 85, 84, 69, 82, 0,
                73, 78, 78, 69, 82, 0, 66, 65, 68, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "OUTER\nINNER\nDONE\n",
    },
    "nested_do_until_branch_mixed": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-do-until-branch-mixed",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'W()\r'
            'ELSE\r'
            'PrintE("BAD1")\r'
            'FI\r'
            'DO\r'
            'IF 1 = 1 THEN\r'
            'HELLO()\r'
            'ELSE\r'
            'PrintE("BAD2")\r'
            'FI\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 75\n"
            "b e0r\n"
            "b dp0p1ap2ghu0we1vdp3p4qhc0we2vp5p6qtop7p8qtoe3r\n"
            "u w\n"
            "s HELLO\n"
            "s BAD1\n"
            "s BAD2\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 123, 0, 7, 0, 1, 97, 0, 97, 97, 0, 73,
                16, 255, 72, 17, 2, 0, 17, 12, 0, 20, 17, 10, 0, 29, 24,
                27, 0, 69, 84, 0, 25, 33, 0, 97, 103, 0, 73, 16, 255, 17,
                1, 0, 17, 1, 0, 22, 24, 49, 0, 69, 0, 0, 25, 55, 0, 97,
                108, 0, 73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24, 33, 0,
                17, 1, 0, 17, 1, 0, 22, 24, 7, 0, 97, 113, 0, 73, 16, 255,
                73, 32, 255, 97, 118, 0, 73, 0, 255, 17, 7, 0, 73, 49,
                255, 72, 72, 69, 76, 76, 79, 0, 66, 65, 68, 49, 0, 66, 65,
                68, 50, 0, 68, 79, 78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "TOOL7\nHELLO\nDONE\n",
    },
    "while_blocks": {
        "out_fs_name": "harness-actc-alink-avmrun-while-blocks",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'PrintE("BAD")\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 26\n"
            "b dp0p1qfe0xe1r\n"
            "s BAD\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 37, 0, 0, 0, 1, 28, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 19, 0, 97, 28, 0, 73, 16, 255, 25, 0, 0,
                97, 32, 0, 73, 16, 255, 73, 32, 255, 66, 65, 68, 0, 68,
                79, 78, 69, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "while_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-while-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'HELLO()\r'
            'W()\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 26\n"
            "b e0r\n"
            "b dp0p1qfc0u0xe1r\n"
            "u w\n"
            "s HELLO\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 64, 0, 7, 0, 1, 48, 0, 97, 48, 0, 73,
                16, 255, 72, 17, 1, 0, 17, 0, 0, 22, 24, 26, 0, 69, 0,
                0, 69, 35, 0, 25, 7, 0, 97, 54, 0, 73, 16, 255, 73, 32,
                255, 97, 59, 0, 73, 0, 255, 17, 7, 0, 73, 49, 255, 72,
                72, 69, 76, 76, 79, 0, 68, 79, 78, 69, 0, 84, 79, 79, 76,
                0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "while_if_else": {
        "out_fs_name": "harness-actc-alink-avmrun-while-if-else",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'PrintE("BAD1")\r'
            'ELSE\r'
            'PrintE("BAD2")\r'
            'FI\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 49\n"
            "b dp0p1qfp2p3ap4ghe0we1vxe2r\n"
            "s BAD1\n"
            "s BAD2\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 66, 0, 0, 0, 1, 51, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 42, 0, 17, 2, 0, 17, 12, 0, 20, 17, 10, 0,
                29, 24, 33, 0, 97, 51, 0, 73, 16, 255, 25, 39, 0, 97, 56,
                0, 73, 16, 255, 25, 0, 0, 97, 61, 0, 73, 16, 255, 73, 32,
                255, 66, 65, 68, 49, 0, 66, 65, 68, 50, 0, 68, 79, 78, 69,
                0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "while_branch_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-while-branch-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC BYE()\r'
            'PrintE("BYE")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'HELLO()\r'
            'ELSE\r'
            'BYE()\r'
            'FI\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x bye 7 7\n"
            "x main 14 43\n"
            "b e0r\n"
            "b e1r\n"
            "b dp0p1qfp2p3ap4ghc0wc1vxe2r\n"
            "s HELLO\n"
            "s BYE\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 74, 0, 14, 0, 1, 59, 0, 97, 59, 0, 73,
                16, 255, 72, 97, 65, 0, 73, 16, 255, 72, 17, 1, 0, 17, 0,
                0, 22, 24, 50, 0, 17, 2, 0, 17, 12, 0, 20, 17, 10, 0, 29,
                24, 44, 0, 69, 0, 0, 25, 47, 0, 69, 7, 0, 25, 14, 0, 97,
                69, 0, 73, 16, 255, 73, 32, 255, 72, 69, 76, 76, 79, 0, 66,
                89, 69, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "while_branch_external": {
        "out_fs_name": "harness-actc-alink-avmrun-while-branch-external",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'W()\r'
            'ELSE\r'
            'PrintE("BAD")\r'
            'FI\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 46\n"
            "b dp0p1qfp2p3ap4ghu0we0vxe1r\n"
            "u w\n"
            "s BAD\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 75, 0, 0, 0, 1, 61, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 39, 0, 17, 2, 0, 17, 12, 0, 20, 17, 10, 0,
                29, 24, 30, 0, 69, 48, 0, 25, 36, 0, 97, 61, 0, 73, 16,
                255, 25, 0, 0, 97, 65, 0, 73, 16, 255, 73, 32, 255, 97,
                70, 0, 73, 0, 255, 17, 7, 0, 73, 49, 255, 72, 66, 65, 68,
                0, 68, 79, 78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "nested_while": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-while",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'PrintE("OUTER")\r'
            'WHILE 1 = 0 DO\r'
            'PrintE("INNER")\r'
            'OD\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 45\n"
            "b dp0p1qfe0dp2p3qfe1xxe2r\n"
            "s OUTER\n"
            "s INNER\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 64, 0, 0, 0, 1, 47, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 38, 0, 97, 47, 0, 73, 16, 255, 17, 1, 0,
                17, 0, 0, 22, 24, 35, 0, 97, 53, 0, 73, 16, 255, 25, 16,
                0, 25, 0, 0, 97, 59, 0, 73, 16, 255, 73, 32, 255, 79, 85,
                84, 69, 82, 0, 73, 78, 78, 69, 82, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "nested_while_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-while-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'HELLO()\r'
            'WHILE 1 = 0 DO\r'
            'W()\r'
            'OD\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 39\n"
            "b e0r\n"
            "b dp0p1qfc0dp2p3qfu0xxe1r\n"
            "u w\n"
            "s HELLO\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 77, 0, 7, 0, 1, 61, 0, 97, 61, 0, 73,
                16, 255, 72, 17, 1, 0, 17, 0, 0, 22, 24, 39, 0, 69, 0, 0,
                17, 1, 0, 17, 0, 0, 22, 24, 36, 0, 69, 48, 0, 25, 20, 0,
                25, 7, 0, 97, 67, 0, 73, 16, 255, 73, 32, 255, 97, 72, 0,
                73, 0, 255, 17, 7, 0, 73, 49, 255, 72, 72, 69, 76, 76, 79,
                0, 68, 79, 78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "nested_while_branch_mixed": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-while-branch-mixed",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'W()\r'
            'ELSE\r'
            'PrintE("BAD1")\r'
            'FI\r'
            'WHILE 1 = 0 DO\r'
            'IF 1 = 1 THEN\r'
            'HELLO()\r'
            'ELSE\r'
            'PrintE("BAD2")\r'
            'FI\r'
            'OD\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 81\n"
            "b e0r\n"
            "b dp0p1qfp2p3ap4ghu0we1vdp5p6qfp7p8qhc0we2vxxe3r\n"
            "u w\n"
            "s HELLO\n"
            "s BAD1\n"
            "s BAD2\n"
            "s DONE\n"
            "i 1\n"
            "i 0\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 129, 0, 7, 0, 1, 103, 0, 97, 103, 0,
                73, 16, 255, 72, 17, 1, 0, 17, 0, 0, 22, 24, 81, 0, 17,
                2, 0, 17, 12, 0, 20, 17, 10, 0, 29, 24, 37, 0, 69, 90, 0,
                25, 43, 0, 97, 109, 0, 73, 16, 255, 17, 1, 0, 17, 0, 0,
                22, 24, 78, 0, 17, 1, 0, 17, 1, 0, 22, 24, 69, 0, 69, 0,
                0, 25, 75, 0, 97, 114, 0, 73, 16, 255, 25, 43, 0, 25, 7,
                0, 97, 119, 0, 73, 16, 255, 73, 32, 255, 97, 124, 0, 73,
                0, 255, 17, 7, 0, 73, 49, 255, 72, 72, 69, 76, 76, 79, 0,
                66, 65, 68, 49, 0, 66, 65, 68, 50, 0, 68, 79, 78, 69, 0,
                84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "while_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-while-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'WHILE 1 = 0 DO\r'
                'W()\r'
                'Q()\r'
                'OD\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 26\n"
                "b dp0p1qfu0u1xe0r\n"
                "u w\n"
                "u q\n"
                "s DONE\n"
                "i 1\n"
                "i 0\n"
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
                65, 86, 77, 49, 2, 74, 0, 0, 0, 1, 55, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 19, 0, 69, 28, 0, 69, 38, 0, 25, 0, 0, 97,
                55, 0, 73, 16, 255, 73, 32, 255, 97, 60, 0, 73, 16, 255,
                69, 48, 0, 72, 97, 65, 0, 73, 16, 255, 69, 48, 0, 72, 97,
                70, 0, 73, 16, 255, 72, 68, 79, 78, 69, 0, 77, 73, 68, 49,
                0, 77, 73, 68, 50, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "do_until_nested_while": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-nested-while",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'DO\r'
            'PrintE("OUTER")\r'
            'WHILE 1 = 0 DO\r'
            'PrintE("INNER")\r'
            'OD\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 42\n"
            "b de0dp0p1qfe1xp2p3qtoe2r\n"
            "s OUTER\n"
            "s INNER\n"
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
                65, 86, 77, 49, 2, 61, 0, 0, 0, 1, 44, 0, 97, 44, 0, 73,
                16, 255, 17, 1, 0, 17, 0, 0, 22, 24, 25, 0, 97, 50, 0, 73,
                16, 255, 25, 6, 0, 17, 1, 0, 17, 1, 0, 22, 24, 6, 0, 97,
                56, 0, 73, 16, 255, 73, 32, 255, 79, 85, 84, 69, 82, 0,
                73, 78, 78, 69, 82, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "OUTER\nDONE\n",
    },
    "while_nested_do_until": {
        "out_fs_name": "harness-actc-alink-avmrun-while-nested-do-until",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'PrintE("OUTER")\r'
            'DO\r'
            'PrintE("INNER")\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 42\n"
            "b dp0p1qfe0de1p2p3qtoxe2r\n"
            "s OUTER\n"
            "s INNER\n"
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
                65, 86, 77, 49, 2, 61, 0, 0, 0, 1, 44, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 35, 0, 97, 44, 0, 73, 16, 255, 97, 50, 0,
                73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24, 16, 0, 25, 0, 0,
                97, 56, 0, 73, 16, 255, 73, 32, 255, 79, 85, 84, 69, 82,
                0, 73, 78, 78, 69, 82, 0, 68, 79, 78, 69, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "do_until_nested_while_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-nested-while-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'DO\r'
            'HELLO()\r'
            'WHILE 1 = 0 DO\r'
            'W()\r'
            'OD\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 36\n"
            "b e0r\n"
            "b dc0dp0p1qfu0xp2p3qtoe1r\n"
            "u w\n"
            "s HELLO\n"
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
                65, 86, 77, 49, 2, 74, 0, 7, 0, 1, 58, 0, 97, 58, 0, 73,
                16, 255, 72, 69, 0, 0, 17, 1, 0, 17, 0, 0, 22, 24, 26, 0,
                69, 45, 0, 25, 10, 0, 17, 1, 0, 17, 1, 0, 22, 24, 10, 0,
                97, 64, 0, 73, 16, 255, 73, 32, 255, 97, 69, 0, 73, 0, 255,
                17, 7, 0, 73, 49, 255, 72, 72, 69, 76, 76, 79, 0, 68, 79,
                78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "HELLO\nDONE\n",
    },
    "while_nested_do_until_calls": {
        "out_fs_name": "harness-actc-alink-avmrun-while-nested-do-until-calls",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'WHILE 1 = 0 DO\r'
            'HELLO()\r'
            'DO\r'
            'W()\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 36\n"
            "b e0r\n"
            "b dp0p1qfc0du0p2p3qtoxe1r\n"
            "u w\n"
            "s HELLO\n"
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
                65, 86, 77, 49, 2, 74, 0, 7, 0, 1, 58, 0, 97, 58, 0, 73,
                16, 255, 72, 17, 1, 0, 17, 0, 0, 22, 24, 36, 0, 69, 0, 0,
                69, 45, 0, 17, 1, 0, 17, 1, 0, 22, 24, 20, 0, 25, 7, 0,
                97, 64, 0, 73, 16, 255, 73, 32, 255, 97, 69, 0, 73, 0, 255,
                17, 7, 0, 73, 49, 255, 72, 72, 69, 76, 76, 79, 0, 68, 79,
                78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "DONE\n",
    },
    "do_until_nested_while_branch_mixed": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-nested-while-branch-mixed",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'DO\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'W()\r'
            'ELSE\r'
            'PrintE("BAD1")\r'
            'FI\r'
            'WHILE 1 = 0 DO\r'
            'IF 1 = 1 THEN\r'
            'HELLO()\r'
            'ELSE\r'
            'PrintE("BAD2")\r'
            'FI\r'
            'OD\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("DONE")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 78\n"
            "b e0r\n"
            "b dp0p1ap2ghu0we1vdp3p4qfp5p6qhc0we2vxp7p8qtoe3r\n"
            "u w\n"
            "s HELLO\n"
            "s BAD1\n"
            "s BAD2\n"
            "s DONE\n"
            "i 2\n"
            "i 12\n"
            "i 10\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 126, 0, 7, 0, 1, 100, 0, 97, 100, 0,
                73, 16, 255, 72, 17, 2, 0, 17, 12, 0, 20, 17, 10, 0, 29,
                24, 27, 0, 69, 87, 0, 25, 33, 0, 97, 106, 0, 73, 16, 255,
                17, 1, 0, 17, 0, 0, 22, 24, 68, 0, 17, 1, 0, 17, 1, 0, 22,
                24, 59, 0, 69, 0, 0, 25, 65, 0, 97, 111, 0, 73, 16, 255,
                25, 33, 0, 17, 1, 0, 17, 1, 0, 22, 24, 33, 0, 97, 116, 0,
                73, 16, 255, 73, 32, 255, 97, 121, 0, 73, 0, 255, 17, 7, 0,
                73, 49, 255, 72, 72, 69, 76, 76, 79, 0, 66, 65, 68, 49, 0,
                66, 65, 68, 50, 0, 68, 79, 78, 69, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "TOOL7\nDONE\n",
    },
    "while_nested_do_until_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-while-nested-do-until-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'WHILE 1 = 0 DO\r'
                'W()\r'
                'DO\r'
                'Q()\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'OD\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 36\n"
                "b dp0p1qfu0du1p2p3qtoxe0r\n"
                "u w\n"
                "u q\n"
                "s DONE\n"
                "i 1\n"
                "i 0\n"
                "i 1\n"
                "i 1\n"
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
                65, 86, 77, 49, 2, 84, 0, 0, 0, 1, 65, 0, 17, 1, 0, 17,
                0, 0, 22, 24, 29, 0, 69, 38, 0, 69, 48, 0, 17, 1, 0, 17,
                1, 0, 22, 24, 13, 0, 25, 0, 0, 97, 65, 0, 73, 16, 255, 73,
                32, 255, 97, 70, 0, 73, 16, 255, 69, 58, 0, 72, 97, 75, 0,
                73, 16, 255, 69, 58, 0, 72, 97, 80, 0, 73, 16, 255, 72, 68,
                79, 78, 69, 0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0, 69,
                78, 68, 0,
            ]
        ),
        "expected_console": "DONE\n",
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
    "if_early_return": {
        "out_fs_name": "harness-actc-alink-avmrun-if-early-return",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintE("START")\r'
            'IF 1 = 1 THEN\r'
            'PrintE("EARLY")\r'
            'RETURN\r'
            'FI\r'
            'PrintE("BAD")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 30\n"
            "b e0p0p1qhe1rve2r\n"
            "s START\n"
            "s EARLY\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 50, 0, 0, 0, 1, 34, 0, 97, 34, 0, 73,
                16, 255, 17, 1, 0, 17, 1, 0, 22, 24, 25, 0, 97, 40, 0, 73,
                16, 255, 25, 31, 0, 97, 46, 0, 73, 16, 255, 73, 32, 255, 83,
                84, 65, 82, 84, 0, 69, 65, 82, 76, 89, 0, 66, 65, 68, 0,
            ]
        ),
        "expected_console": "START\nEARLY\n",
    },
    "else_early_return": {
        "out_fs_name": "harness-actc-alink-avmrun-else-early-return",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'IF 1 = 0 THEN\r'
            'PrintE("BAD")\r'
            'ELSE\r'
            'PrintE("EARLY")\r'
            'RETURN\r'
            'FI\r'
            'PrintE("BAD2")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 33\n"
            "b p0p1qhe0we1rve2r\n"
            "s BAD\n"
            "s EARLY\n"
            "s BAD2\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 52, 0, 0, 0, 1, 37, 0, 17, 1, 0, 17, 0,
                0, 22, 24, 19, 0, 97, 37, 0, 73, 16, 255, 25, 28, 0, 97, 41,
                0, 73, 16, 255, 25, 34, 0, 97, 47, 0, 73, 16, 255, 73, 32,
                255, 66, 65, 68, 0, 69, 65, 82, 76, 89, 0, 66, 65, 68, 50, 0,
            ]
        ),
        "expected_console": "EARLY\n",
    },
    "do_until_early_return": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-early-return",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintE("START")\r'
            'DO\r'
            'PrintE("EARLY")\r'
            'RETURN\r'
            'UNTIL 1 = 1\r'
            'OD\r'
            'PrintE("BAD")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 30\n"
            "b e0de1rp0p1qtoe2r\n"
            "s START\n"
            "s EARLY\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 50, 0, 0, 0, 1, 34, 0, 97, 34, 0, 73, 16,
                255, 97, 40, 0, 73, 16, 255, 25, 31, 0, 17, 1, 0, 17, 1, 0,
                22, 24, 6, 0, 97, 46, 0, 73, 16, 255, 73, 32, 255, 83, 84,
                65, 82, 84, 0, 69, 65, 82, 76, 89, 0, 66, 65, 68, 0,
            ]
        ),
        "expected_console": "START\nEARLY\n",
    },
    "while_early_return": {
        "out_fs_name": "harness-actc-alink-avmrun-while-early-return",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintE("START")\r'
            'WHILE 1 = 1 DO\r'
            'PrintE("EARLY")\r'
            'RETURN\r'
            'OD\r'
            'PrintE("BAD")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 33\n"
            "b e0dp0p1qfe1rxe2r\n"
            "s START\n"
            "s EARLY\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 53, 0, 0, 0, 1, 37, 0, 97, 37, 0, 73, 16,
                255, 17, 1, 0, 17, 1, 0, 22, 24, 28, 0, 97, 43, 0, 73, 16,
                255, 25, 34, 0, 25, 6, 0, 97, 49, 0, 73, 16, 255, 73, 32,
                255, 83, 84, 65, 82, 84, 0, 69, 65, 82, 76, 89, 0, 66, 65,
                68, 0,
            ]
        ),
        "expected_console": "START\nEARLY\n",
    },
    "nested_if_early_return": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-if-early-return",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintE("START")\r'
            'IF 1 = 1 THEN\r'
            'IF 2 + 3 * 4 > 10 THEN\r'
            'PrintE("EARLY")\r'
            'RETURN\r'
            'ELSE\r'
            'PrintE("BAD1")\r'
            'FI\r'
            'ELSE\r'
            'PrintE("BAD2")\r'
            'FI\r'
            'PrintE("BAD3")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 62\n"
            "b e0p0p1qhp2p3ap4ghe1rwe2vwe3ve4r\n"
            "s START\n"
            "s EARLY\n"
            "s BAD1\n"
            "s BAD2\n"
            "s BAD3\n"
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
                65, 86, 77, 49, 2, 93, 0, 0, 0, 1, 66, 0, 97, 66, 0, 73, 16,
                255, 17, 1, 0, 17, 1, 0, 22, 24, 51, 0, 17, 2, 0, 17, 12, 0,
                20, 17, 10, 0, 29, 24, 42, 0, 97, 72, 0, 73, 16, 255, 25, 63,
                0, 25, 48, 0, 97, 78, 0, 73, 16, 255, 25, 57, 0, 97, 83, 0,
                73, 16, 255, 97, 88, 0, 73, 16, 255, 73, 32, 255, 83, 84, 65,
                82, 84, 0, 69, 65, 82, 76, 89, 0, 66, 65, 68, 49, 0, 66, 65,
                68, 50, 0, 66, 65, 68, 51, 0,
            ]
        ),
        "expected_console": "START\nEARLY\n",
    },
    "if_return_local": {
        "out_fs_name": "harness-actc-alink-avmrun-if-return-local",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("HELLO")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'PrintE("START")\r'
            'IF 1 = 1 THEN\r'
            'HELLO()\r'
            'RETURN\r'
            'FI\r'
            'PrintE("BAD")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 27\n"
            "b e0r\n"
            "b e1p0p1qhc0rve2r\n"
            "s HELLO\n"
            "s START\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 54, 0, 7, 0, 1, 38, 0, 97, 38, 0, 73, 16,
                255, 72, 97, 44, 0, 73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24,
                29, 0, 69, 0, 0, 25, 35, 0, 97, 50, 0, 73, 16, 255, 73, 32,
                255, 72, 69, 76, 76, 79, 0, 83, 84, 65, 82, 84, 0, 66, 65,
                68, 0,
            ]
        ),
        "expected_console": "START\nHELLO\n",
    },
    "if_return_external": {
        "out_fs_name": "harness-actc-alink-avmrun-if-return-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'IF 1 = 1 THEN\r'
                'W()\r'
                'RETURN\r'
                'FI\r'
                'PrintE("BAD")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("TOOL7")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 27\n"
                "b e0p0p1qhu0rve1r\n"
                "u w\n"
                "s START\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s TOOL7\n"
                "k 2\n"
                "n w\n"
            ),
        },
        "expected_avo": (
            "AVO1\n"
            "x main 0 27\n"
            "b e0p0p1qhu0rve1r\n"
            "u w\n"
            "s START\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 54, 0, 0, 0, 1, 38, 0, 97, 38, 0, 73, 16,
                255, 17, 1, 0, 17, 1, 0, 22, 24, 22, 0, 69, 31, 0, 25, 28,
                0, 97, 44, 0, 73, 16, 255, 73, 32, 255, 97, 48, 0, 73, 16,
                255, 72, 83, 84, 65, 82, 84, 0, 66, 65, 68, 0, 84, 79, 79,
                76, 55, 0,
            ]
        ),
        "expected_console": "START\nTOOL7\n",
    },
    "else_return_external": {
        "out_fs_name": "harness-actc-alink-avmrun-else-return-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'IF 1 = 0 THEN\r'
                'PrintE("BAD")\r'
                'ELSE\r'
                'W()\r'
                'RETURN\r'
                'FI\r'
                'PrintE("BAD2")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("TOOL7")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 30\n"
                "b p0p1qhe0wu0rve1r\n"
                "u w\n"
                "s BAD\n"
                "s BAD2\n"
                "i 1\n"
                "i 0\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s TOOL7\n"
                "k 2\n"
                "n w\n"
            ),
        },
        "expected_avo": (
            "AVO1\n"
            "x main 0 30\n"
            "b p0p1qhe0wu0rve1r\n"
            "u w\n"
            "s BAD\n"
            "s BAD2\n"
            "i 1\n"
            "i 0\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 56, 0, 0, 0, 1, 41, 0, 17, 1, 0, 17, 0,
                0, 22, 24, 19, 0, 97, 41, 0, 73, 16, 255, 25, 25, 0, 69, 34,
                0, 25, 31, 0, 97, 45, 0, 73, 16, 255, 73, 32, 255, 97, 50,
                0, 73, 16, 255, 72, 66, 65, 68, 0, 66, 65, 68, 50, 0, 84, 79,
                79, 76, 55, 0,
            ]
        ),
        "expected_console": "TOOL7\n",
    },
    "do_until_return_external": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-return-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'DO\r'
                'W()\r'
                'RETURN\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'PrintE("BAD")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("TOOL7")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 27\n"
                "b e0du0rp0p1qtoe1r\n"
                "u w\n"
                "s START\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s TOOL7\n"
                "k 2\n"
                "n w\n"
            ),
        },
        "expected_avo": (
            "AVO1\n"
            "x main 0 27\n"
            "b e0du0rp0p1qtoe1r\n"
            "u w\n"
            "s START\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 54, 0, 0, 0, 1, 38, 0, 97, 38, 0, 73, 16,
                255, 69, 31, 0, 25, 28, 0, 17, 1, 0, 17, 1, 0, 22, 24, 6,
                0, 97, 44, 0, 73, 16, 255, 73, 32, 255, 97, 48, 0, 73, 16,
                255, 72, 83, 84, 65, 82, 84, 0, 66, 65, 68, 0, 84, 79, 79,
                76, 55, 0,
            ]
        ),
        "expected_console": "START\nTOOL7\n",
    },
    "while_return_local_external": {
        "out_fs_name": "harness-actc-alink-avmrun-while-return-local-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC HELLO()\r'
                'PrintE("HELLO")\r'
                'RETURN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'WHILE 1 = 1 DO\r'
                'HELLO()\r'
                'W()\r'
                'RETURN\r'
                'OD\r'
                'PrintE("BAD")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("TOOL7")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x hello 0 7\n"
                "x main 7 33\n"
                "b e0r\n"
                "b e1dp0p1qfc0u0rxe2r\n"
                "u w\n"
                "s HELLO\n"
                "s START\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s TOOL7\n"
                "k 2\n"
                "n w\n"
            ),
        },
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 33\n"
            "b e0r\n"
            "b e1dp0p1qfc0u0rxe2r\n"
            "u w\n"
            "s HELLO\n"
            "s START\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 73, 0, 7, 0, 1, 51, 0, 97, 51, 0, 73, 16,
                255, 72, 97, 57, 0, 73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24,
                35, 0, 69, 0, 0, 69, 44, 0, 25, 41, 0, 25, 13, 0, 97, 63,
                0, 73, 16, 255, 73, 32, 255, 97, 67, 0, 73, 16, 255, 72, 72,
                69, 76, 76, 79, 0, 83, 84, 65, 82, 84, 0, 66, 65, 68, 0, 84,
                79, 79, 76, 55, 0,
            ]
        ),
        "expected_console": "START\nHELLO\nTOOL7\n",
    },
    "nested_if_return_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-if-return-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'IF 1 = 1 THEN\r'
                'IF 2 + 3 * 4 > 10 THEN\r'
                'W()\r'
                'RETURN\r'
                'ELSE\r'
                'PrintE("BAD1")\r'
                'FI\r'
                'ELSE\r'
                'PrintE("BAD2")\r'
                'FI\r'
                'PrintE("BAD3")\r'
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
                "x main 0 59\n"
                "b e0p0p1qhp2p3ap4ghu0rwe1vwe2ve3r\n"
                "u w\n"
                "s START\n"
                "s BAD1\n"
                "s BAD2\n"
                "s BAD3\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 59\n"
            "b e0p0p1qhp2p3ap4ghu0rwe1vwe2ve3r\n"
            "u w\n"
            "s START\n"
            "s BAD1\n"
            "s BAD2\n"
            "s BAD3\n"
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
                65, 86, 77, 49, 2, 109, 0, 0, 0, 1, 80, 0, 97, 80, 0, 73,
                16, 255, 17, 1, 0, 17, 1, 0, 22, 24, 48, 0, 17, 2, 0, 17,
                12, 0, 20, 17, 10, 0, 29, 24, 39, 0, 69, 63, 0, 25, 60, 0,
                25, 45, 0, 97, 86, 0, 73, 16, 255, 25, 54, 0, 97, 91, 0, 73,
                16, 255, 97, 96, 0, 73, 16, 255, 73, 32, 255, 97, 101, 0, 73,
                16, 255, 69, 73, 0, 72, 97, 105, 0, 73, 16, 255, 72, 83, 84,
                65, 82, 84, 0, 66, 65, 68, 49, 0, 66, 65, 68, 50, 0, 66, 65,
                68, 51, 0, 77, 73, 68, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "START\nMID\nEND\n",
    },
    "do_until_return_branch_mixed": {
        "out_fs_name": "harness-actc-alink-avmrun-do-until-return-branch-mixed",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC HELLO()\r'
                'PrintE("HELLO")\r'
                'RETURN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'DO\r'
                'IF 2 + 3 * 4 > 10 THEN\r'
                'W()\r'
                'ELSE\r'
                'HELLO()\r'
                'FI\r'
                'RETURN\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'PrintE("BAD")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("TOOL7")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x hello 0 7\n"
                "x main 7 47\n"
                "b e0r\n"
                "b e1dp0p1ap2ghu0wc0vrp3p4qtoe2r\n"
                "u w\n"
                "s HELLO\n"
                "s START\n"
                "s BAD\n"
                "i 2\n"
                "i 12\n"
                "i 10\n"
                "i 1\n"
                "i 1\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s TOOL7\n"
                "k 2\n"
                "n w\n"
            ),
        },
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 47\n"
            "b e0r\n"
            "b e1dp0p1ap2ghu0wc0vrp3p4qtoe2r\n"
            "u w\n"
            "s HELLO\n"
            "s START\n"
            "s BAD\n"
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
                65, 86, 77, 49, 2, 87, 0, 7, 0, 1, 65, 0, 97, 65, 0, 73, 16,
                255, 72, 97, 71, 0, 73, 16, 255, 17, 2, 0, 17, 12, 0, 20,
                17, 10, 0, 29, 24, 33, 0, 69, 58, 0, 25, 36, 0, 69, 0, 0,
                25, 55, 0, 17, 1, 0, 17, 1, 0, 22, 24, 13, 0, 97, 77, 0, 73,
                16, 255, 73, 32, 255, 97, 81, 0, 73, 16, 255, 72, 72, 69, 76,
                76, 79, 0, 83, 84, 65, 82, 84, 0, 66, 65, 68, 0, 84, 79, 79,
                76, 55, 0,
            ]
        ),
        "expected_console": "START\nTOOL7\n",
    },
    "nested_do_until_return_external": {
        "out_fs_name": "harness-actc-alink-avmrun-nested-do-until-return-external",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'DO\r'
                'DO\r'
                'W()\r'
                'RETURN\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'PrintE("BAD")\r'
                'RETURN\r'
            ),
            "W": (
                'MODULE W\r'
                'PROC W()\r'
                'PrintE("TOOL7")\r'
                'RETURN\r'
            ),
        },
        "compile_modules": ["W", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 37\n"
                "b e0ddu0rp0p1qtop2p3qtoe1r\n"
                "u w\n"
                "s START\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
                "k 2\n"
                "n main\n"
            ),
            "W": (
                "AVO1\n"
                "x w 0 7\n"
                "b e0r\n"
                "s TOOL7\n"
                "k 2\n"
                "n w\n"
            ),
        },
        "expected_avo": (
            "AVO1\n"
            "x main 0 37\n"
            "b e0ddu0rp0p1qtop2p3qtoe1r\n"
            "u w\n"
            "s START\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 64, 0, 0, 0, 1, 48, 0, 97, 48, 0, 73, 16,
                255, 69, 41, 0, 25, 38, 0, 17, 1, 0, 17, 1, 0, 22, 24, 6,
                0, 17, 1, 0, 17, 1, 0, 22, 24, 6, 0, 97, 54, 0, 73, 16, 255,
                73, 32, 255, 97, 58, 0, 73, 16, 255, 72, 83, 84, 65, 82, 84,
                0, 66, 65, 68, 0, 84, 79, 79, 76, 55, 0,
            ]
        ),
        "expected_console": "START\nTOOL7\n",
    },
    "while_return_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-while-return-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'WHILE 1 = 1 DO\r'
                'W()\r'
                'RETURN\r'
                'OD\r'
                'PrintE("BAD")\r'
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
                "x main 0 30\n"
                "b e0dp0p1qfu0rxe1r\n"
                "u w\n"
                "s START\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 30\n"
            "b e0dp0p1qfu0rxe1r\n"
            "u w\n"
            "s START\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 69, 0, 0, 0, 1, 51, 0, 97, 51, 0, 73, 16,
                255, 17, 1, 0, 17, 1, 0, 22, 24, 25, 0, 69, 34, 0, 25, 31,
                0, 25, 6, 0, 97, 57, 0, 73, 16, 255, 73, 32, 255, 97, 61, 0,
                73, 16, 255, 69, 44, 0, 72, 97, 65, 0, 73, 16, 255, 72, 83,
                84, 65, 82, 84, 0, 66, 65, 68, 0, 77, 73, 68, 0, 69, 78, 68,
                0,
            ]
        ),
        "expected_console": "START\nMID\nEND\n",
    },
    "while_nested_do_until_return_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-while-nested-do-until-return-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'PrintE("START")\r'
                'WHILE 1 = 1 DO\r'
                'DO\r'
                'W()\r'
                'RETURN\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'OD\r'
                'PrintE("BAD")\r'
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
                "x main 0 40\n"
                "b e0dp0p1qfdu0rp2p3qtoxe1r\n"
                "u w\n"
                "s START\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 40\n"
            "b e0dp0p1qfdu0rp2p3qtoxe1r\n"
            "u w\n"
            "s START\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 79, 0, 0, 0, 1, 61, 0, 97, 61, 0, 73, 16,
                255, 17, 1, 0, 17, 1, 0, 22, 24, 35, 0, 69, 44, 0, 25, 41,
                0, 17, 1, 0, 17, 1, 0, 22, 24, 16, 0, 25, 6, 0, 97, 67, 0,
                73, 16, 255, 73, 32, 255, 97, 71, 0, 73, 16, 255, 69, 54, 0,
                72, 97, 75, 0, 73, 16, 255, 72, 83, 84, 65, 82, 84, 0, 66,
                65, 68, 0, 77, 73, 68, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "START\nMID\nEND\n",
    },
    "dense_mixed_nested_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-dense-mixed-nested-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'DO\r'
                'WHILE 1 = 0 DO\r'
                'W()\r'
                'PrintE("BAD")\r'
                'OD\r'
                'Q()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'PrintE("K")\r'
                'PrintE("L")\r'
                'PrintE("M")\r'
                'PrintE("N")\r'
                'PrintE("O")\r'
                'PrintE("P")\r'
                'UNTIL 1 = 1\r'
                'OD\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 132\n"
                "b ddp0p1qfu0e0xu1e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFeGp2p3qtor\n"
                "u w\n"
                "u q\n"
                "s BAD\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "s K\n"
                "s L\n"
                "s M\n"
                "s N\n"
                "s O\n"
                "s P\n"
                "i 1\n"
                "i 0\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 132\n"
            "b ddp0p1qfu0e0xu1e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFeGp2p3qtor\n"
            "u w\n"
            "u q\n"
            "s BAD\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "i 1\n"
            "i 0\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 211, 0, 0, 0, 1, 161, 0, 17, 1, 0,
                17, 0, 0, 22, 24, 22, 0, 69, 134, 0, 97, 161, 0, 73, 16,
                255, 25, 0, 0, 69, 144, 0, 97, 165, 0, 73, 16, 255, 97,
                167, 0, 73, 16, 255, 97, 169, 0, 73, 16, 255, 97, 171, 0,
                73, 16, 255, 97, 173, 0, 73, 16, 255, 97, 175, 0, 73, 16,
                255, 97, 177, 0, 73, 16, 255, 97, 179, 0, 73, 16, 255, 97,
                181, 0, 73, 16, 255, 97, 183, 0, 73, 16, 255, 97, 185, 0,
                73, 16, 255, 97, 187, 0, 73, 16, 255, 97, 189, 0, 73, 16,
                255, 97, 191, 0, 73, 16, 255, 97, 193, 0, 73, 16, 255, 97,
                195, 0, 73, 16, 255, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0, 73,
                32, 255, 97, 197, 0, 73, 16, 255, 69, 154, 0, 72, 97, 202,
                0, 73, 16, 255, 69, 154, 0, 72, 97, 207, 0, 73, 16, 255,
                72, 66, 65, 68, 0, 65, 0, 66, 0, 67, 0, 68, 0, 69, 0, 70,
                0, 71, 0, 72, 0, 73, 0, 74, 0, 75, 0, 76, 0, 77, 0, 78,
                0, 79, 0, 80, 0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0, 69,
                78, 68, 0,
            ]
        ),
        "expected_console": "MID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n",
    },
    "dense_return_nested_mixed_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-dense-return-nested-mixed-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'DO\r'
                'WHILE 1 = 1 DO\r'
                'W()\r'
                'Q()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'PrintE("K")\r'
                'PrintE("L")\r'
                'PrintE("M")\r'
                'PrintE("N")\r'
                'PrintE("O")\r'
                'PrintE("P")\r'
                'RETURN\r'
                'OD\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'PrintE("BAD")\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 133\n"
                "b ddp0p1qfu0u1e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFrxp2p3qtoeGr\n"
                "u w\n"
                "u q\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "s K\n"
                "s L\n"
                "s M\n"
                "s N\n"
                "s O\n"
                "s P\n"
                "s BAD\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 133\n"
            "b ddp0p1qfu0u1e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFrxp2p3qtoeGr\n"
            "u w\n"
            "u q\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "s BAD\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 214, 0, 0, 0, 1, 164, 0, 17, 1, 0,
                17, 1, 0, 22, 24, 118, 0, 69, 137, 0, 69, 147, 0, 97,
                164, 0, 73, 16, 255, 97, 166, 0, 73, 16, 255, 97, 168,
                0, 73, 16, 255, 97, 170, 0, 73, 16, 255, 97, 172, 0, 73,
                16, 255, 97, 174, 0, 73, 16, 255, 97, 176, 0, 73, 16,
                255, 97, 178, 0, 73, 16, 255, 97, 180, 0, 73, 16, 255,
                97, 182, 0, 73, 16, 255, 97, 184, 0, 73, 16, 255, 97,
                186, 0, 73, 16, 255, 97, 188, 0, 73, 16, 255, 97, 190,
                0, 73, 16, 255, 97, 192, 0, 73, 16, 255, 97, 194, 0, 73,
                16, 255, 25, 134, 0, 25, 0, 0, 17, 1, 0, 17, 1, 0, 22,
                24, 0, 0, 97, 196, 0, 73, 16, 255, 73, 32, 255, 97, 200,
                0, 73, 16, 255, 69, 157, 0, 72, 97, 205, 0, 73, 16, 255,
                69, 157, 0, 72, 97, 210, 0, 73, 16, 255, 72, 65, 0, 66,
                0, 67, 0, 68, 0, 69, 0, 70, 0, 71, 0, 72, 0, 73, 0, 74,
                0, 75, 0, 76, 0, 77, 0, 78, 0, 79, 0, 80, 0, 66, 65, 68,
                0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0, 69, 78, 68, 0,
            ]
        ),
        "expected_console": "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n",
    },
    "dense_return_branch_nested_mixed_shared_transitive": {
        "out_fs_name": "harness-actc-alink-avmrun-dense-return-branch-nested-mixed-shared-transitive",
        "sources": {
            "MAIN": (
                'MODULE MAIN\r'
                'PROC MAIN()\r'
                'DO\r'
                'WHILE 1 = 1 DO\r'
                'IF 1 = 1 THEN\r'
                'W()\r'
                'Q()\r'
                'PrintE("A")\r'
                'PrintE("B")\r'
                'PrintE("C")\r'
                'PrintE("D")\r'
                'PrintE("E")\r'
                'PrintE("F")\r'
                'PrintE("G")\r'
                'PrintE("H")\r'
                'PrintE("I")\r'
                'PrintE("J")\r'
                'PrintE("K")\r'
                'PrintE("L")\r'
                'PrintE("M")\r'
                'PrintE("N")\r'
                'PrintE("O")\r'
                'PrintE("P")\r'
                'RETURN\r'
                'ELSE\r'
                'PrintE("BAD1")\r'
                'FI\r'
                'OD\r'
                'UNTIL 1 = 1\r'
                'OD\r'
                'PrintE("BAD2")\r'
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
        "compile_modules": ["Z", "W", "Q", "MAIN"],
        "expected_objects": {
            "MAIN": (
                "AVO1\n"
                "x main 0 152\n"
                "b ddp0p1qfp2p3qhu0u1e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFrweGvxp4p5qtoeHr\n"
                "u w\n"
                "u q\n"
                "s A\n"
                "s B\n"
                "s C\n"
                "s D\n"
                "s E\n"
                "s F\n"
                "s G\n"
                "s H\n"
                "s I\n"
                "s J\n"
                "s K\n"
                "s L\n"
                "s M\n"
                "s N\n"
                "s O\n"
                "s P\n"
                "s BAD1\n"
                "s BAD2\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
                "i 1\n"
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
        "expected_avo": (
            "AVO1\n"
            "x main 0 152\n"
            "b ddp0p1qfp2p3qhu0u1e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFrweGvxp4p5qtoeHr\n"
            "u w\n"
            "u q\n"
            "s A\n"
            "s B\n"
            "s C\n"
            "s D\n"
            "s E\n"
            "s F\n"
            "s G\n"
            "s H\n"
            "s I\n"
            "s J\n"
            "s K\n"
            "s L\n"
            "s M\n"
            "s N\n"
            "s O\n"
            "s P\n"
            "s BAD1\n"
            "s BAD2\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "i 1\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 239, 0, 0, 0, 1, 183, 0, 17, 1, 0,
                17, 1, 0, 22, 24, 137, 0, 17, 1, 0, 17, 1, 0, 22, 24, 128,
                0, 69, 156, 0, 69, 166, 0, 97, 183, 0, 73, 16, 255, 97,
                185, 0, 73, 16, 255, 97, 187, 0, 73, 16, 255, 97, 189, 0,
                73, 16, 255, 97, 191, 0, 73, 16, 255, 97, 193, 0, 73, 16,
                255, 97, 195, 0, 73, 16, 255, 97, 197, 0, 73, 16, 255, 97,
                199, 0, 73, 16, 255, 97, 201, 0, 73, 16, 255, 97, 203, 0,
                73, 16, 255, 97, 205, 0, 73, 16, 255, 97, 207, 0, 73, 16,
                255, 97, 209, 0, 73, 16, 255, 97, 211, 0, 73, 16, 255, 97,
                213, 0, 73, 16, 255, 25, 153, 0, 25, 134, 0, 97, 215, 0,
                73, 16, 255, 25, 0, 0, 17, 1, 0, 17, 1, 0, 22, 24, 0, 0,
                97, 220, 0, 73, 16, 255, 73, 32, 255, 97, 225, 0, 73, 16,
                255, 69, 176, 0, 72, 97, 230, 0, 73, 16, 255, 69, 176, 0,
                72, 97, 235, 0, 73, 16, 255, 72, 65, 0, 66, 0, 67, 0, 68,
                0, 69, 0, 70, 0, 71, 0, 72, 0, 73, 0, 74, 0, 75, 0, 76,
                0, 77, 0, 78, 0, 79, 0, 80, 0, 66, 65, 68, 49, 0, 66, 65,
                68, 50, 0, 77, 73, 68, 49, 0, 77, 73, 68, 50, 0, 69, 78,
                68, 0,
            ]
        ),
        "expected_console": "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n",
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
        "build_actc_harness_udos.sh",
        "build_alink_harness_udos.sh",
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
