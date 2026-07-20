# `ACTEDIT` Source Editor Roadmap

Current as of `2026-07-14`.

This document defines the intended UDOS-native source editor for Action
projects.

The editor is not a minor convenience. It is a core development tool, and it
must be designed around:

- large source files
- REU-backed storage
- 40-column screen limits
- integration with compile/build/debug flows

## Goal

Provide a real full-screen source editor for Action project files with:

- vertical scrolling
- horizontal scrolling
- insert/delete editing
- mark/copy/cut/paste/delete block operations
- load/save
- goto line
- find/replace
- project integration

Planned tool:

- `ACTEDIT.PRG`
- `ACTEDIT_OVL1.BIN` native mutation overlay

## Current Baseline

Today the repo has:

- `ACTSRC.PRG` for manifest/source listing
- `ACTFILE.PRG` for source viewing/printing
- `ACTMON.PRG` for project-front-end dispatch
- `ACTEDIT.PRG` as a first REU-backed full-screen editor bootstrap slice

So today the project can inspect and make narrow interactive edits to sources
in a real full-screen tool, but it is still well short of the intended final
editor.

Current `ACTEDIT` bootstrap behavior:

- accepts `ACTEDIT <NAME>` and resolves `SRC/<NAME>.ACT`
- accepts `ACTEDIT SRC/<NAME>.ACT`
- accepts `ACTEDIT <NAME-OR-PATH>:<LINE>` and opens that exact 1-based line;
  malformed, zero, out-of-range, and overflowing locations fail explicitly
- stages the source file into REU and addresses immutable source bytes with
  24-bit offsets through a small resident cache, including files larger than
  64 KiB
- keeps immutable source at REU bank `$07` and above, clear of the editor's
  fixed undo, redo, metadata, and add-buffer workspaces in banks `$03-$06`
- builds a batched 24-bit source-line index immediately after the staged file,
  so line lookup and streamed save no longer rescan immutable source from byte
  zero
- builds a persistent edited-document line index in REU banks `$00-$02`; each
  three-byte entry names a derived piece plus its 16-bit line offset, so normal
  navigation and save use direct logical-line lookup after the index is built
- rewrites only the affected logical-index suffix after direct patch, insert,
  delete, split, join, and paste mutations, while retaining full rebuilds for
  initial derivation, undo/redo restore, and fallback; all 65,535 logical line
  numbers remain clear of undo/redo storage in banks `$03-$04`
- directly replaces a clean source-line piece with source/patch/source spans and
  persists that updated piece table without reconstructing descriptors
- directly inserts new INSERT pieces for both source-line and inserted-line
  splits, removes source/PATCH/INSERT pieces for join and multiline delete, and
  keeps general multiline paste on those direct primitives
- updates text in an existing INSERT slot without invalidating an otherwise
  unchanged piece table or logical index
- loads the bounded `AEOV` native mutation overlay once into RAM under BASIC
  ROM at `$A000`; missing, oversized, or malformed overlays leave direct
  mutation disabled and preserve correctness through the descriptor rebuild
  path
- renders a full-screen source view
- supports cursor-up/cursor-down line browsing
- uses left/right as an edit cursor with horizontal scroll
- supports typed character insertion on the current line
- supports delete-left editing on the current line
- supports `RETURN` line split and delete-at-column-0 line join
- supports logical-line mark/copy/cut/paste/delete with:
  - `F3` mark anchor
  - `F5` copy selection
  - `F6` cut selection
  - `F7` paste clipboard
  - `DELETE` delete selection without replacing the clipboard
- supports search/navigation helpers:
  - `F2` find next current token or current-line marked selection
  - `F4` find previous current token or current-line marked selection
- supports prompt-driven helpers:
  - `Ctrl-G` goto line
  - `Ctrl-R` replace next match for the current token or current-line marked
    selection
  - `Ctrl-A` replace every literal match in the document as one undoable edit
- supports non-text navigation helpers:
  - `HOME` line home, then file top when already at column `0`
  - `INS` line end, then file bottom when already at line end
  - `CLR/HOME` page up
  - `F8` page down
- supports a small REU-backed undo/redo journal:
  - `Ctrl-U` walks backward through the last few mutating edit states
  - `Ctrl-Y` walks forward through the currently redoable edit states
  - current depth is `32`
- keeps dirty state
- preserves edited lines plus limited inserted/deleted line structure through a
  logical-line model whose patch/insert/delete descriptor tables live in
  REU-backed metadata windows, whose patch/insert line payload text lives in
  an append-only REU add buffer behind a shared resident edit-text window, and
  whose visible line loads now rebuild through a small resident piece window
  over that REU-backed state
- supports up to `64` active patch, insert, and delete descriptors and a
  `255`-entry derived piece window; navigation preserves requested line numbers
  while a dirty piece table is rebuilt
- saves back to the source file with `F1` through streamed UDOS writes
- saves and hands off through direct-program workflow keys:
  - `Ctrl-O` queues `ACTC <MODULE>;` to compile the current module and return
    to the failing source line on a compiler error
  - `Ctrl-B` queues `ACTC <MODULE>,`; ACTC then queues ALINK after a successful
    object write
  - `Ctrl-D` queues `ACTC <MODULE>:`; ACTC queues ALINK and ALINK queues ACTDBG
    only after each preceding output succeeds
- derives the shared uppercase module name from both `NAME` and
  `SRC/NAME.ACT` editor entry forms
- accepts ACTDBG's compact source-path/line handoff and positions the editor at
  the debugger's currently browsed linked source location
- supports clean quit back to UDOS with `RUN/STOP`, clearing the full-screen
  canvas before the shell redraws its prompt

Current `ACTEDIT` bootstrap footprint:

- `ACTEDIT.PRG`: `16243`
- resident span: `$0900-$4870`
- resident `CODE`: `$3F71`
- resident `ZPTEMP`: `$001E`
- mutation overlay: `1758` bytes at `$A000-$A6DD`
- free resident margin below the `$4AFE` UDOS floor: `653` bytes

Current `ACTEDIT` bootstrap limits:

- clean source-line patches, source/insert splits, source/PATCH/INSERT removals,
  joins, and multiline paste now mutate and persist the derived piece table
  directly; dirty-cache, undo/redo restore, capacity, and I/O fallback paths
  still rebuild from the metadata-authoritative descriptor model
- the full `255`-entry piece cache remains resident rather than using a small
  working window over an unconstrained REU descriptor stream
- the edited-document line index is persistent and direct mutations rewrite
  only the affected suffix; initial derivation and fallback still rebuild it
  from the resident piece window
- undo/redo remains a bounded `32`-entry snapshot journal rather than compact
  piece transactions

## Core Decision

The editor must be REU-backed from the start.

A plain in-RAM whole-file editor will fail too early and then force a rewrite.
That is the wrong path.

The editor should treat normal RAM as:

- screen/view state
- cursor state
- command state
- small working caches

And treat REU as:

- original file store
- appended edit store
- piece descriptors
- copy/paste buffer
- optional undo records

## Buffer Model

Planned document model: REU-backed piece table.

Why this is the right fit:

- original file stays immutable in REU
- inserted text appends to a second REU region
- the visible document is a sequence of pieces
- cut/copy/paste become descriptor edits instead of whole-file shifts
- save is a streaming walk over the piece list
- large-file support becomes practical

Planned REU regions:

- original file data
- add buffer
- piece descriptor table
- copy buffer
- optional undo journal

Planned resident RAM data:

- current piece/cache window
- current line index cache
- viewport render buffer
- status line state
- key-command state

## View Model

The editor is full-screen, not line-at-a-time shell editing.

Planned screen use on a 40x25 display:

- top status row
  - file/module name
  - dirty flag
  - mode
  - line/column
  - left-column offset
- main text viewport
  - the visible source window
- bottom command/message row
  - prompts
  - errors
  - search/replace input

Horizontal scrolling is required, not optional.

That means the editor tracks:

- current line
- current column
- top visible line
- left visible column

## Command Surface

The exact key map can change later. The command set should not.

Required first-class operations:

- cursor up/down/left/right
- page up/page down
- line home/end
- file home/end
- scroll left/right
- insert character
- delete character
- backspace
- split line
- join line
- mark start/end
- copy block
- cut block
- delete block
- paste block
- save
- quit
- goto line
- find
- replace

Useful later additions:

- single-line undo, then multi-step undo
- duplicate line/block
- comment/uncomment block
- compile/build/debug current module

## File Model

The editor should work directly with project source files:

- `SRC/<NAME>.ACT`

Planned entry paths:

- `ACTEDIT <NAME>`
- `ACTEDIT SRC/<NAME>.ACT`
- `ACTMON EDIT <NAME>`

Save should stream directly through the existing UDOS file-save services.

This should reuse the project/file helper layer already used by:

- `ACT2SAVE`
- `ACTFILE`
- `ACTSRC`
- `ACTMON`

## Large File Direction

The editor must not assume source files fit in plain C64 RAM.

Current large-file foundation:

- load the file into REU
- address immutable source with 24-bit offsets and a 255-byte resident window
- count and render source across 64 KiB REU bank boundaries
- build a batched, persistent 24-bit index for immutable source-line starts
- build a separate persistent logical-line index over source, patch, and insert
  pieces in REU banks `$00-$02`
- use those indexes for direct line lookup and linear streamed save

Remaining large-file strategy:

- keep only a small render/index working set resident
- scroll, edit, and save by walking indexed piece spans

This is consistent with the compiler direction already chosen:

- large source and metadata live in REU
- resident RAM holds only the active working window

## Copy Buffer

Block operations require a real copy buffer, not only line delete/paste.

Planned copy buffer behavior:

- block copy writes into REU-backed copy storage
- block cut edits the piece table and also fills that copy storage
- paste inserts a new piece sequence referencing copy-buffer data

This avoids repeated whole-document moves.

## Search / Replace

Search and replace should also be REU-aware.

Current bootstrap behavior:

- literal ASCII search
- forward and backward search
- replace next and whole-document replace all
- replace-all advances past inserted replacement text, so replacements that
  contain the search text terminate correctly
- replace-all is recorded as one undo operation

Regex-style search is not a goal.

## Integration With Compiler And Debugger

The editor should become the place where project work starts.

Current integration:

- compile, build, and debug commands save the current module and use the fixed
  UDOS program-chain service
- ACTC queues ALINK only after successful object output
- ALINK queues ACTDBG only after successful direct-PRG and debug-sidecar output
- all stages use the same derived module name and ordinary direct PRGs
- ACTDBG `E` queues `ACTEDIT <SOURCE-PATH>:<LINE>` for the currently browsed
  linked source record; commands that cannot fit UDOS's 31-byte chain ABI are
  rejected rather than truncated
- ACTC's compile-only `;`, build `,`, and debug `:` modes queue
  `ACTEDIT <MODULE>:<LINE>` after a source diagnostic; plain `ACTC <MODULE>`
  retains its nonzero failure return without an editor handoff
- failure handoffs use the same strict 31-byte chain bound and do not truncate
  long module commands

That means `ACTEDIT`, `ACTC`, `ALINK`, and `ACTDBG` should share the same
module/path conventions.

## Relationship To The Old ACTION! Editor

The old ACTION! editor is a useful behavioral reference, not a strict
compatibility target.

Good features worth keeping in spirit:

- horizontal scrolling
- block copy/delete/paste
- goto file top/end
- find/replace
- monitor/editor handoff

What matters is matching the capability set, not reproducing every historic
key binding exactly.

## Planned Phases

### Phase 1

- `ACTEDIT.PRG` exists
- load one source file
- cursor movement
- vertical scrolling
- horizontal scrolling
- quit cleanly back to UDOS
- REU-backed source staging
- 24-bit immutable-source addressing across REU banks
- insert/delete/backspace
- dirty-state tracking
- streamed save
- split/join line

### Phase 2

- mark/copy/cut/delete/paste block operations
- goto line
- find
- replace current
- simple copy buffer persistence during one session

### Phase 3

- multi-step undo is available through the current `32`-entry journal
- replace all is available as one undoable operation
- compile/build hooks are available through `Ctrl-O` and `Ctrl-B`
- debugger handoff is available through `Ctrl-D`
- debugger-to-editor source-location return is available through ACTDBG `E`
- project-aware open/create flows through `ACTMON`

## Practical Next Implementation Steps

1. replace full-state undo snapshots with compact piece transactions so history
   is not constrained by the current `32`-entry rings
2. replace the full resident `255`-piece cache with a paged REU descriptor
   working set
3. add richer project-aware open/create handoff through `ACTMON`
