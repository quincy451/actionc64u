# Tool ABI Harness

Current local harness for UDOS-native tools:

- source: [tool_abi_harness.c](/mnt/c/test/action/actionc64u/tools/tool_abi_harness.c)
- build: [build_tool_abi_harness.sh](/mnt/c/test/action/actionc64u/tools/build_tool_abi_harness.sh)
- harness-sized tool builds:
  - [build_actc_harness_udos.sh](/mnt/c/test/action/actionc64u/tools/build_actc_harness_udos.sh)
  - [build_alink_harness_udos.sh](/mnt/c/test/action/actionc64u/tools/build_alink_harness_udos.sh)

## Purpose

This harness runs a tool `.PRG` under a deterministic host-side 6502 CPU core and
intercepts only the narrow UDOS tool-service ABI.

It is intentionally not a full C64 or UDOS shell emulator.

Current intercepted services:

- `svc_program_get_cmdline_ptr`
- `svc_program_get_cmdline_len`
- `svc_console_write_sc0`
- `svc_console_newline`
- `svc_file_load_sc0`
- `svc_file_save_sc0`
- `svc_program_exit`

That makes it useful for separating:

- tool logic
- tool/service-call parameter setup

from:

- resident shell state
- VICE timing / prompt / mount noise

The harness also now hooks the file-related KERNAL entry points used by the
resident path:

- `READST`
- `SETLFS`
- `SETNAM`
- `OPEN`
- `CLOSE`
- `CHKIN`
- `CHKOUT`
- `CLRCHN`
- `CHRIN`
- `CHROUT`

## Current Usage

Build:

```sh
cd /mnt/c/test/action/actionc64u
./tools/build_tool_abi_harness.sh
```

The harness pipeline currently builds `ACTC` and `ALINK` with harness-specific
linker configs so widening work can continue without the real UDOS tool-size
ceiling blocking every new control-flow slice.

Current harness build widening knobs:

- `ACTC`: `SOURCE_LIMIT=511`
- `ACTC`: `STRING_LITERAL_MAX=32`
- `ALINK`: `STRING_LITERAL_MAX=32`

Recent harness-proven widening additions now covered by named scenarios:

- `external_args_multi`: unresolved-external multi-arg calls like `PrintIE(W(2,3))`
- `nested_call_arg`: nested call results reused as later call arguments like `PrintIE(W(INC(2+3)))`
- `if_local_args`: local arg-bearing calls under `IF ... THEN ... ELSE ... FI`
- `while_external_args`: external arg-bearing calls under `WHILE ... DO ... OD`
- `bool_compound_args`: compound boolean predicates using external arg calls
- `bool_local_external_args`: compound boolean predicates mixing local and external arg calls

Use any one of them with:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario <name> --keep-workspace
```

Run the current additive widening proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --keep-workspace
```

Run the current precedence/parentheses proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario precedence --keep-workspace
```

Run the current arithmetic+comparisons proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario comparisons --keep-workspace
```

Run the current direct comparison-operator print proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario comparison_ops --keep-workspace
```

Run the current high string-index proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_indices --keep-workspace
```

Run the current high string-index `IF/ELSE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_if_else --keep-workspace
```

Run the current high string-index `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_do_until --keep-workspace
```

Run the current high string-index `DO ... UNTIL ... OD` with `IF/ELSE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_do_until_if_else --keep-workspace
```

Run the current high integer-index proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_int_indices --keep-workspace
```

Run the current high integer-index `IF/ELSE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_int_if_else --keep-workspace
```

Run the current high integer-index `DO ... UNTIL ... OD` with `IF/ELSE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_int_do_until_if_else --keep-workspace
```

Run the current direct comparison-operator branch proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario comparison_ops_if_else --keep-workspace
```

Run the current direct comparison-operator loop proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario comparison_ops_loops --keep-workspace
```

Run the current arithmetic+comparison `IF/ELSE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario comparison_else --keep-workspace
```

Run the current direct comparison-operator branch-call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario comparison_ops_branch_calls --keep-workspace
```

Run the current high string-index branch-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_branch_external --keep-workspace
```

Run the current high string-index transitive branch-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_branch_transitive --keep-workspace
```

Run the current high string-index shared-transitive branch proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_branch_shared_transitive --keep-workspace
```

Run the current 17-root-string shared-transitive branch proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string17_branch_shared_transitive --keep-workspace
```

Run the current dense shared-transitive branch + early-return proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario dense_return_branch_shared_transitive --keep-workspace
```

Run the current high string-index shared-transitive `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_do_until_shared_transitive --keep-workspace
```

Run the current high string-index nested shared-transitive branch proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_nested_branch_shared_transitive --keep-workspace
```

Run the current high string-index nested-loop external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_nested_loops_external --keep-workspace
```

Run the current full high int-index nested-loop `IF/ELSE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_int_nested_loops_if_else --keep-workspace
```

Run the current high string-index nested-loop `IF/ELSE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario many_string_nested_loops_if_else --keep-workspace
```

Run the current dense mixed nested-loop shared-transitive proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario dense_mixed_nested_shared_transitive --keep-workspace
```

Run the current dense early-return nested mixed-loop shared-transitive proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario dense_return_nested_mixed_shared_transitive --keep-workspace
```

Run the current dense branch-gated early-return nested mixed-loop shared-transitive proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario dense_return_branch_nested_mixed_shared_transitive --keep-workspace
```

Run the current branch-local procedure-call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario branch_calls --keep-workspace
```

Run the current arithmetic/comparison branch-local procedure-call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario comparison_branch_calls --keep-workspace
```

Run the current nested branch-local procedure-call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_branch_calls --keep-workspace
```

Run the current branch-local unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario branch_external --keep-workspace
```

Run the current nested branch-local unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_branch_external --keep-workspace
```

Run the current transitive unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario transitive_external --keep-workspace
```

Run the current transitive unresolved-external branch proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario transitive_branch_external --keep-workspace
```

Run the current sibling unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario sibling_externals --keep-workspace
```

Run the current child-sibling unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario child_sibling_externals --keep-workspace
```

Run the current branch-local plus transitive unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario branch_transitive_local --keep-workspace
```

Run the current repeated-root unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario repeated_root_externals --keep-workspace
```

Run the current shared-transitive unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario shared_transitive_external --keep-workspace
```

Run the current branch-sibling unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario branch_sibling_externals --keep-workspace
```

Run the current branch-shared-transitive unresolved-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario branch_shared_transitive --keep-workspace
```

Run the current local-procedure-call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario procedures --keep-workspace
```

Run the current `IF` control-flow proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario if_blocks --keep-workspace
```

Run the current `ELSE` control-flow proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario else_blocks --keep-workspace
```

Run the current nested-`IF` control-flow proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_if --keep-workspace
```

Run the current nested-`ELSE` control-flow proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_else --keep-workspace
```

Run the current early-return `IF` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario if_early_return --keep-workspace
```

Run the current early-return `ELSE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario else_early_return --keep-workspace
```

Run the current early-return `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_early_return --keep-workspace
```

Run the current early-return `WHILE ... DO ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_early_return --keep-workspace
```

Run the current nested early-return `IF` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_if_early_return --keep-workspace
```

Run the current early-return local/external call proofs end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario if_return_external --keep-workspace
./tools/run_tool_abi_additive_pipeline.py --scenario while_return_local_external --keep-workspace
```

Run the current nested early-return transitive-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_if_return_transitive --keep-workspace
```

Run the current mixed early-return loop proofs end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_return_branch_mixed --keep-workspace
./tools/run_tool_abi_additive_pipeline.py --scenario while_return_transitive --keep-workspace
```

Run the current `DO ... UNTIL ... OD` loop proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until --keep-workspace
```

Run the current local-call plus unresolved-external `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_calls --keep-workspace
```

Run the current branch-controlled `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_if_else --keep-workspace
```

Run the current branch-local-call `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_branch_calls --keep-workspace
```

Run the current branch-external `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_branch_external --keep-workspace
```

Run the current nested `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_do_until --keep-workspace
```

Run the current nested loop + local/external call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_do_until_calls --keep-workspace
```

Run the current nested loop + nested branch proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_do_until_if_else --keep-workspace
```

Run the current nested loop + mixed branch local/external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_do_until_branch_mixed --keep-workspace
```

Run the current `WHILE ... DO ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_blocks --keep-workspace
```

Run the current `WHILE` + local/external call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_calls --keep-workspace
```

Run the current `WHILE` + branch proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_if_else --keep-workspace
```

Run the current `WHILE` + branch-local-call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_branch_calls --keep-workspace
```

Run the current `WHILE` + branch-external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_branch_external --keep-workspace
```

Run the current nested `WHILE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_while --keep-workspace
```

Run the current nested `WHILE` + local/external call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_while_calls --keep-workspace
```

Run the current nested `WHILE` + mixed branch proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario nested_while_branch_mixed --keep-workspace
```

Run the current `WHILE` + shared-transitive external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_shared_transitive --keep-workspace
```

Run the current `DO ... UNTIL ... OD` containing nested `WHILE` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_nested_while --keep-workspace
```

Run the current `WHILE ... DO ... OD` containing nested `DO ... UNTIL ... OD` proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_nested_do_until --keep-workspace
```

Run the current `DO` + nested `WHILE` + local/external call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_nested_while_calls --keep-workspace
```

Run the current `WHILE` + nested `DO` + local/external call proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_nested_do_until_calls --keep-workspace
```

Run the current mixed `DO`/`WHILE` + branch local/external proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario do_until_nested_while_branch_mixed --keep-workspace
```

Run the current `WHILE` + nested `DO` + shared-transitive proof end to end:

```sh
cd /mnt/c/test/action/actionc64u
./tools/run_tool_abi_additive_pipeline.py --scenario while_nested_do_until_shared_transitive --keep-workspace
```

That script:

- clones a clean harness workspace from the current manual-pipeline fs tree
- writes the selected scenario source set and `ACTION.PROJ` manifest
- runs `ACTC`, `ALINK`, and `AVMRUN` under the harness
- verifies:
  - exact `OBJ/<NAME>.AVO` text for every compiled module in the scenario
  - exact `BIN/MAIN.AVM` bytes
  - exact runtime console output

Run a tool:

```sh
cd /mnt/c/test/action
actionc64u/build/udos_tools/tool_abi_harness \
  --prg actionc64u/build/udos_tools/ALINK.PRG \
  --workspace udos/build/udos-release-fs-manual-pipeline-44/IMAGES/ACTION.DNP/PROJ3 \
  --cmdline MAIN \
  --services-inc actionc64u/build/udos_tools/udos_services.inc \
  --labels actionc64u/build/udos_tools/alink.current.labels \
  --dump-cstr target_path:40 \
  --dump-cstr binary_target_path:40 \
  --dump-cstr module_name:16 \
  --dump source_buffer:16 \
  --dump content_buffer:16 \
  --dump file_params:9 \
  --op-dump-cstr target_path:40 \
  --op-dump-cstr binary_target_path:40 \
  --op-dump-cstr module_name:16 \
  --op-dump file_params:9 \
  --op-dump source_buffer:16 \
  --op-dump content_buffer:16
```

Synthetic service-entry frames can also be injected to stress stack/context
assumptions without going back to VICE:

```sh
actionc64u/build/udos_tools/tool_abi_harness \
  ... \
  --extra-load-frames 4 \
  --extra-save-frames 4
```

Direct entry-by-label is supported for deterministic resident work:

```sh
actionc64u/build/udos_tools/tool_abi_harness \
  --prg udos/build/release/udos-resident.prg \
  --workspace udos/build/udos-release-fs-manual-pipeline-44/IMAGES/ACTION.DNP/PROJ3 \
  --services-inc actionc64u/build/udos_tools/udos_services.inc \
  --labels udos/build/release/udos-resident.labels \
  --entry-label vice_open_read_from_ptr \
  --poke-cstr '50450=/IMAGES/ACTION.DNP/PROJ3/OBJ/MAIN.AVO,S,R' \
  --poke-word '251=50450' \
  --poke-byte '38334=1' \
  --poke-byte '38486=5' \
  --poke-byte '38487=2'
```

Useful control options for this mode:

- `--entry-label NAME`
- `--entry-addr ADDR`
- `--stop-pc ADDR`
- `--trace-pc-range START:END`
- `--reg-a N`
- `--reg-x N`
- `--reg-y N`
- `--reg-sp N`
- `--poke-byte NAME=VALUE`
- `--poke-word NAME=VALUE`
- `--poke-cstr NAME=TEXT`
- `--poke-scstr NAME=TEXT`
- `--extra-entry-frames N`

Poke and dump targets can be either:

- ld65 symbol names
- raw numeric addresses like `251` or `0x00FB`

`--poke-scstr` writes uppercase letters in Commodore screen-code form
(`A`..`Z` become `$01`..`$1A`) and leaves punctuation untouched. That is useful
for resident buffers like `mount_path_b`, `path_name_buffer`, and other path
state that the resident later converts back through `screen_code_to_ascii`.

`--entry-addr` is useful when a local label does not exist at the exact
continuation you want to test. It lets the harness jump directly into the live
instruction stream, which is how the current resident load wrapper was split at
`0x891D` versus `0x8925`.

`--stop-pc` stops execution just before the CPU executes a specific address.
That is useful when the interesting state exists at a call boundary and later
behavior would otherwise overwrite the stack or zero page before the harness
returns.

`--trace-pc-range` records instruction-level execution only within a narrow PC
window. That keeps the JSON trace small enough to use for wrapper-return
debugging.

## Current Output

The harness prints JSON containing:

- final CPU registers
- tool console output
- ordered file-service trace records
  - kind
  - resolved path
  - caller stack context
  - raw parameter bytes
  - first bytes loaded/saved
  - stack-window bytes at service entry
  - optional per-operation symbol snapshots
- ordered KERNAL call trace for resident-entry work
  - `SETLFS`
  - `SETNAM`
  - `OPEN`
  - `CHKIN`
  - `CHKOUT`
  - `CLRCHN`
  - `CHRIN`
  - `CHROUT`
  - `READST`
- optional symbol-based dumps from ld65 labels
- optional narrow PC trace for wrapper/callsite debugging

## Most Important Current Result

On the real widened manual-pipeline object workspace, the harness proves:

- `ACTC` loads `ACTION.PROJ`
- loads `SRC/MAIN.ACT`
- saves `OBJ/MAIN.AVO`
- `ALINK` loads `ACTION.PROJ`
- loads `OBJ/MAIN.AVO`
- loads `OBJ/W.AVO`
- saves `BIN/MAIN.AVM`
- `AVMRUN` loads `BIN/MAIN.AVM`
- runtime output is `HELLO`, `TOOL7`, `5459`
- exits cleanly

So the current widened `ACTC -> ALINK -> AVMRUN` slice is working under the
harness when the resident/VICE service path is removed from the equation.

That now includes a widening set of stable scenarios:

- additive chains with an external call:
  `HELLO`, `TOOL7`, `5459`
- mixed precedence and parentheses:
  `145`
- arithmetic + comparisons + external call:
  `14`, `5`, `1`, `1`, `TOOL7`
- module-scope integer variable read/assignment:
  `0`, `1`
- module-scope integer variable state through `DO ... UNTIL ... OD`:
  `0`, `1`, `DONE`
- module-scope integer variable branch control:
  `YES`, `DONE`
- module-scope integer variable `WHILE` control:
  `0`, `1`, `DONE`
- module-scope integer variable branch-driven local/external calls:
  `HELLO`, `TOOL7`
- module-scope integer variable `WHILE` + external call:
  `TOOL7`, `DONE`
- multiple module-scope integer vars in one module:
  `0`, `2`, `3`
- multiple module-scope integer vars under `WHILE` control:
  `0`, `1`, `2`
- multiple module-scope integer vars driving local/external branch calls:
  `HELLO`, `TOOL7`
- multiple module-scope integer vars driving shared-transitive externals under branch control:
  `MID1`, `END`, `MID2`, `END`, `DONE`
- multiple module-scope integer vars driving shared-transitive externals under `WHILE` control:
  `MID1`, `END`, `MID2`, `END`, `DONE`
- variable-to-variable arithmetic assignment:
  `3`
- local zero-arg integer return:
  `2`
- local zero-arg integer returns inside arithmetic:
  `5`
- unresolved-external zero-arg integer return:
  `7`
- returned values used in assignment:
  `1`
- returned values used in conditions:
  `OK`
- unresolved-external zero-arg integer returns inside arithmetic:
  `8`
- local procedure argument passing with expression-valued args:
  `6`
- multiple local procedure args:
  `5`
- unresolved-external procedure args:
  `7`
- composed boolean conditions with `AND` / `OR` and external returns:
  `OK`
- composed boolean conditions with `NOT` and external returns:
  `OK`
- arithmetic/comparison condition with `IF/ELSE`:
  `YES`, `DONE`
- branch-local procedure call:
  `HELLO`, `DONE`
- arithmetic/comparison branch-local procedure call:
  `HELLO`, `DONE`
- nested branch-local procedure call:
  `HELLO`, `DONE`
- branch-local unresolved-external call:
  `TOOL7`, `DONE`
- nested branch-local unresolved-external call:
  `TOOL7`, `DONE`
- transitive unresolved-external closure across modules:
  `START`, `MID`, `END`, `DONE`
- nested `DO ... UNTIL ... OD`:
  `OUTER`, `INNER`, `DONE`
- nested loop + local/external calls:
  `HELLO`, `TOOL7`, `DONE`
- nested loop + nested branch control flow:
  `OUTER`, `INNER`, `DONE`
- nested loop + mixed branch local/external calls:
  `TOOL7`, `HELLO`, `DONE`
- top-tested `WHILE ... DO ... OD`:
  `DONE`
- `WHILE` + local/external call:
  `DONE`
- `WHILE` + branch control flow:
  `DONE`
- `WHILE` + branch-local call:
  `DONE`
- `WHILE` + branch-external call:
  `DONE`
- nested `WHILE`:
  `DONE`
- nested `WHILE` + local/external call:
  `DONE`
- `DO ... UNTIL ... OD` containing nested `WHILE`:
  `OUTER`, `DONE`
- `WHILE ... DO ... OD` containing nested `DO ... UNTIL ... OD`:
  `DONE`
- `DO` + nested `WHILE` + local/external call:
  `HELLO`, `DONE`
- `WHILE` + nested `DO` + local/external call:
  `DONE`
- mixed `DO`/`WHILE` + branch local/external call:
  `TOOL7`, `DONE`
- `WHILE` + nested `DO` + shared-transitive externals:
  `DONE`
- nested `WHILE` + mixed branch local/external content:
  `DONE`
- `WHILE` + shared-transitive external reuse:
  `DONE`
- transitive unresolved-external closure inside branch control flow:
  `START`, `MID`, `END`, `DONE`
- sibling unresolved-external calls from the root:
  `START`, `MID1`, `MID2`, `DONE`
- sibling unresolved-external calls from a child module:
  `START`, `MID`, `END1`, `END2`, `DONE`
- local call plus transitive unresolved-external branch:
  `LOCAL`, `MID`, `END`, `DONE`
- repeated root unresolved-external reuse:
  `START`, `MID1`, `MID2`, `MID1`, `DONE`
- shared transitive unresolved-external reuse:
  `START`, `MID1`, `END`, `MID2`, `END`, `DONE`
- sibling unresolved-external calls inside branch control flow:
  `MID1`, `MID2`, `DONE`
- shared transitive unresolved-external calls inside branch control flow:
  `MID1`, `END`, `MID2`, `END`, `DONE`
- local user procedure call:
  `ONE`, `TWO`
- single-branch `IF` control flow:
  `YES`, `DONE`
- `ELSE` control flow:
  `GOOD`, `DONE`
- nested `IF` control flow:
  `INNERDONE`, `OUTERDONE`
- nested `ELSE` control flow:
  `GOOD1`, `DONE`

## Current Debug Value

Current per-operation trace lets us see the exact green `ALINK` contexts:

- root object load at `sp = 249`
- child object loads at `sp = 241`
- final save at `sp = 251`
- final save path is `BIN/MAIN.AVM`
- final output buffer begins with valid `AVM1`

Current save-modeling result:

- zero-length `svc_file_save_sc0` now models the current tool convention as a
  zero-terminated text save
- that is required for `ACTC` object saves under the harness

Current synthetic-frame result:

- `ACT2SAVE` stays green with `--extra-load-frames 4`
- `ALINK` stays green with `--extra-load-frames 4 --extra-save-frames 4`

That means extra service-entry stack depth by itself is not enough to reproduce
the resident/VICE failure. The live blocker is narrower than simple call-depth
at the service ABI boundary.

Resident-entry status:

- direct resident `vice_open_read_from_ptr` is now executable under the harness
- resident direct-call debugging is now good enough to split exact wrapper
  boundaries without VICE
- current sharpest split:
  - direct `0x8925` in `tool_abi_file_load_sc0` reaches the KERNAL open path cleanly
  - direct `0x891D` does not
  - so the live resident load bug is now narrowed to the `jsr tool_abi_build_open_path`
    callsite / return boundary, not the later open/read helper body
