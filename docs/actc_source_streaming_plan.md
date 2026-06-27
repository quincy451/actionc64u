# ACTC Source Streaming Plan

Date: 2026-04-22

## Goal

`ACTC.PRG` must eventually compile source files that are much larger than RAM,
up to the usable REU-backed workspace. The practical ceiling is the 16 MiB DNP
image size minus REU space already reserved by UDOS/runtime services, not an
arbitrary 256 KiB source cap.

The current compiler only partially does this. It stages source into REU and can
refill `source_buffer` through SourceReader-managed scans, so it can now compile a narrow
line-oriented proof where the `PROC MAIN` name, a `PrintE` string literal, or
long inline spaces before a `PrintIE` literal cross the first 20 KiB window
boundary. Small-window proofs also verify the declaration-count overlay can skip
a module header whose name crosses the window, collect a `PROC` export name
split across the window, collect module, parameter, and local variable names
split across the window, plus a moving-base `PrintE` string literal,
indexed-`Y` assignment spacing, and scan-pointer assignment symbols can cross
a REU source window with zero bounded lookahead, including legal long `PROC`
export, assignment, and procedure parameter/local symbols spanning multiple
tiny windows, and a statement line end as the first byte in the next source
window. The same small-window proof now covers fixed `PrintIE(` and `RETURN`
patterns crossing the window, plus page-aligned 256-byte zero-lookahead
`PrintIE(` and `RETURN 1` crossings. It also has the
first expression proof where a long `PrintIE(...)` expression and a long
variable symbol cross the same boundary, an assignment left-hand symbol crossing
the same boundary, zero-lookahead `THEN` and `DO` terminator keywords crossing
a small source window, page-aligned zero-lookahead `THEN` and `DO` terminator
keyword crossings, page-aligned zero-lookahead condition operators covering
`=`, `<`, `>`, `<=`, `>=`, and `<>`, boolean keyword proofs where `AND`, `OR`,
and `NOT` appear beyond an 8-bit `Y` wrap in print, assignment, return, local
declaration initializer,
procedure-call argument, procedure-call punctuation, page-aligned zero-lookahead
procedure-call `(`, `,`, and `)` punctuation, including page-aligned 256-byte
zero-lookahead assignment keyword, conversion keywords, builtin helper names,
helper-family builtin constants, semicolon comment-line, multi-window semicolon
comment-line, and CR/LF crossings,
constant-expression, and `IF`/`WHILE`/`UNTIL` control-flow condition paths, and
the first parameter-list punctuation proof where `(` appears at `Y=$FF`. It still
performs several full-source scans, and parts of the parser are still
character-driven rather than token-driven, but maintained resident source reads
now route through SourceReader peek/consume helpers. Long tokens and long lines
still need broader parser ownership before they are a fully general model.

## Required File ABI Work

The existing `svc_file_load_sc0` service is an all-or-limit loader. It can prove
larger contiguous loads, but it cannot stream a file in chunks or resume from an
offset. ACTC source streaming needs one of these UDOS/tool ABI additions:

- preferred: `svc_file_read_begin_sc0`, `svc_file_read_chunk_sc0`, and
  `svc_file_read_close_sc0`
- acceptable: an extended load service with explicit 32-bit file offset,
  destination pointer, and requested byte count

The chunk API is the better shape because it also maps cleanly to future linker
object streaming and runtime file I/O.

## Preferred Source Cache

The preferred large-source design is not repeated file I/O for every compiler
pass. ACTC should read each source file once through the chunked file-read ABI
and stage it into REU-backed source blocks. Later compiler passes should page
small windows from that REU cache into normal RAM.

This gives the compiler random or repeated sequential access to source text
without keeping the whole source in C64 RAM and without rereading a large file
from the filesystem for every pass.

The current production ACTC build uses `ACTC_REU_SOURCE_CACHE=1`. It stages
`SRC/<MODULE>.ACT` at REU base `$010000`, pages a 1280-byte default
`SOURCE_LIMIT` back into `source_buffer`, loads an additional
`SOURCE_LOOKAHEAD=255` bytes for bounded compatibility lookahead, and refills the
window when the scanner reaches the window end. The production window is kept
page-aligned to avoid per-byte boundary code in the resident tool window; larger
or smaller harness builds can still override `ACTC_SOURCE_WINDOW`. This is not
the final parser architecture yet. The production UDOS resident now exports the
matching REU stage/read service entries, while the automated proof uses the host
harness' simulated REU.

The current refill hook remains anchored to the legacy scanner pointer, while
SourceReader now owns source byte peeks, consumes, selected token buffers, and
window reloads. It is enough for the proven line-oriented cases and legal-length
symbols/literals that cross tiny zero-lookahead windows, but the next
correctness step is broader token ownership so parser decisions do not depend on
legacy scan pointer shape.

The first helper beyond raw pointer refill is
`source_reader_commit_256_from_scan_ptr`, used when 8-bit `Y` lookahead wraps.
`source_reader_peek_scan_y` and `source_reader_peek_scan_ptr` own the resident
source reads for indexed scans and moving-base `scan_ptr` scans.
`source_reader_consume_scan_y` and `source_reader_consume_scan_ptr` are now the
parser-visible byte-consume boundaries for both forms. `advance_scan_y` and
`advance_scan_ptr` remain only as low-level implementation details used by
consume helpers after a validated peek. That prevents long runs of spaces and the
current long-expression proof from silently wrapping to the beginning of the
same scan window. Boolean pre-scan wraps now intentionally route into the
boolean parser instead of continuing from `Y=0` in the same window, and
speculative expression pre-scans now mark and restore the active REU source
window before returning to the real parse. Failed boolean keyword probes use the
same mark/restore path, so speculative parsing cannot leave the reader pointed
at the wrong window before the normal expression parser resumes. Assignment
parsing preserves the `=` operator position across variable lookup and consumes
assignment punctuation through the SourceReader, so long inline spaces before
`=` can cross an 8-bit `Y` wrap without parsing the right-hand side from the
wrong offset. Procedure parameter parsing has the same first proof for an
opening `(` at `Y=$FF`. Runtime and constant group-speculation paths also keep
their own reader mark, so `(expr)` can be reparsed as a comparison left-hand side
after the speculative group parse crosses into another REU source window.
Line-ending and `THEN`/`DO` terminator helpers, module/local declaration
initializers, body-level return/assignment/local-call punctuation, call
arguments, expression comparisons, grouped expressions, decimal arithmetic,
positive-word arithmetic, real conversion/comparison paths, conversion keyword
open-paren parsing, resident declaration scans, body keyword scans, and
pattern-location scans now all share the same narrow SourceReader read/consume
primitives. Resident and body-collect overlay `THEN`/`DO` terminator probes now
consume keyword characters through shared expected-character helpers. Keyword
token pattern matching now routes each matched pattern
character and post-keyword token-boundary check through SourceReader helpers
that own the source peek, uppercase compare/classification, source consume, and
pattern-index advance. The central string-literal helper now delegates each
literal byte to a SourceReader helper that owns the peek, length check, store,
source consume, and post-consume token-target restore. Both resident symbol-copy
helpers now build tokens in a SourceReader-owned carry buffer before publishing
to the legacy resolver scratch name, while
preserving the existing returned-`Y` scanner ABI. The resident module-header
copy helper uses the same carry-buffer publish path for `declared_module_name`.
Parser-side symbol helpers now store and terminate token bytes through
SourceReader token helpers rather than writing the token buffer directly, and
resident streaming symbol-copy plus module-header copy loops now share one
SourceReader token-byte helper that peeks, classifies, stores, consumes, and
updates the scanner offset. Procedure export
name copies now use a matching non-consuming SourceReader token-byte helper so
the legacy returned-`Y` parameter-list ABI is preserved while token storage is
centralized before publishing to the export table. The source-header
overlay module-name comparator and declaration-count overlay var/export symbol
copies use the same local token-helper shape. Declaration initializer body
character checks also route through a local helper before falling back to
operator validation. This separates token construction
from compatibility storage. REU source-cache
builds now compile in streaming symbol-copy branches when bounded lookahead is
too small for a legal 24-byte symbol, even when the source window is
page-aligned, and `scan_y` consumes compile in loaded-window boundary checks
when the active source-window/lookahead shape requires them. A focused 256-byte
source-window, zero-lookahead assignment-symbol proof guards the case where a
token begins at byte 254 and continues in the next window. A matching boolean
keyword proof now guards `scan_keyword_token_from_scan_y` when `AND` begins at
byte 254 in the same page-aligned zero-lookahead shape, while the production
255-byte lookahead build keeps the compact resident path so `ACTC.PRG` remains
below the UDOS resident floor. Variable-name probes now restore their
SourceReader probe mark on lookup miss, so split builtin helper names across
the shipped GFX1, SIDSPR1, INPUT1, DBF1, and core MATH1 helper families can
still be reparsed as link-selected runtime calls after first being tried as
variables.
The same page-aligned zero-lookahead shape now covers shipped helper constants
such as joystick direction/button masks, mouse button masks, SID waveform/filter
masks, and sprite priority masks in both body expressions and module
declaration initializers.
The fixed-pattern match helpers now keep the
compact bounded-lookahead fast path while falling back to a moving-base
SourceReader probe when a fixed pattern or keyword delimiter crosses the loaded
window boundary; the slow-path pattern-character compare and consume sequence
and keyword-delimiter classification are centralized behind SourceReader
helpers. A matching page-aligned zero-lookahead `PrintIE(` proof covers
that fallback when the pattern starts at byte 254, and a matching `RETURN 1`
proof guards delimiter probing so the expression after a split keyword is not
lost to stale lookahead. Statement terminator keyword probes now also have a
page-aligned zero-lookahead `THEN`/`DO` proof for the existing
`scan_keyword_token_from_scan_y` mark/restore path. Runtime condition parsing
now has a page-aligned zero-lookahead operator matrix for `=`, `<`, `>`, `<=`,
`>=`, and `<>`, guarding both one-byte operator consumption and the second byte
of split two-byte operators. Procedure-call argument parsing now has matching
page-aligned zero-lookahead punctuation coverage for `(`, `,`, and `)`.
The resident module-header fallback and declaration-count overlay now have
small-window source cache coverage, including procedure export names plus
module, parameter, and local variable names copied by the declaration overlay.
The declaration-count overlay now stages those identifiers in an overlay-local
token buffer before publishing to the var/export table windows. Its inline-space
scanner is the first declaration-count overlay path routed through local source
peek/consume wrappers instead of raw pointer access, and declaration line-end
validation plus var/export-name symbol reads now use the same local source peek
path. Procedure parameter punctuation checks now also peek through that local
wrapper while preserving explicit scan advancement. Declaration-tail delimiter
checks use the same local peek path before initializer parsing. Declaration
keyword character and delimiter reads also route through that peek wrapper while
retaining the existing rewind behavior for failed probes. Declaration
initializer expression scans now peek through the same wrapper before consuming
characters. Declaration whitespace and line skipping now peek and consume
through the local wrappers, and mixed spaces, tabs, CR, and LF before module
declarations are covered across multiple tiny source windows with no lookahead.
Remaining raw declaration-overlay source reads are limited by test to the local
peek helper itself. The declaration-loop EOF probe now checks for an
already-loaded byte and uses the local peek helper without forcing a new
body-only source window into the declaration pass. The name-cache comparator
uses an explicit cache-pointer alias over the saved source scan slot, so it is
no longer treated as a source scan read. The source-header overlay now
centralizes its raw source reads behind a refill-aware local peek helper and has
small-window coverage for leading whitespace spanning multiple source windows,
including mixed spaces, tabs, CR, and LF, the `MODULE` keyword crossing a window
boundary, mixed space/tab module-name spacing spanning multiple source windows,
and long module names spanning multiple tiny source windows with no lookahead.
The body-collect overlay now routes source reads through the resident
SourceReader peek callback instead of reading the resident scan pointer
directly, with mixed spaces, tabs, CR, and LF before body statements covered
across multiple tiny source windows with no lookahead.
Payload-layout and emit-object scan reads are over compiler body/string payload
windows rather than source windows and remain centralized behind
`payload_layout_peek_payload_y` and `emit_object_peek_payload_y`; tests guard
those overlays against source-window context references.
Shared project-manifest line scans, entry matching, and mutation shifts now use
the same SourceReader peek/consume helpers. Body-collect overlay scan-advance
context entries also route through the SourceReader consume helpers instead of
exposing raw scanner advances to overlay code. Tiny source-window harness builds
also keep streamed object output from overflowing the reused source/output
buffer. These paths still keep their current bounded token-length behavior, so
the parser still needs the next architectural
step from character peek-at-window to true token ownership with carry buffers.

The source cache should track:

- source file identity and length
- 32-bit source offset
- REU base block/page for the file
- dirty flag, initially false because source text is read-only during compile
- small RAM page buffer and current cached offset

The first implementation can support one active source module. A later version
can cache multiple project modules so cross-module compile or whole-project
analysis does not repeatedly hit the filesystem.

## REU Service Shape

The current source-cache path uses two small service calls that match the
compiler's immediate need:

`svc_file_stage_reu_sc0`

- input: `X` points at a parameter block
- `+0/+1`: zero-terminated source path pointer
- `+2/+3/+4`: 24-bit REU destination base, little-endian
- output `+5`: `tool_file_status_*`
- output `+6/+7/+8`: 24-bit staged byte count

`svc_reu_read_sc0`

- input: `X` points at a parameter block
- `+0/+1/+2`: 24-bit REU source address, little-endian
- `+3/+4`: C64 destination pointer
- `+5/+6`: byte count
- output `+7`: `tool_file_status_*`

This is enough to prove one-time file staging plus RAM-window paging. Later
resident work can either keep this shape or replace staging with chunked file
read services that ACTC uses to fill REU blocks itself. A future
`svc_reu_write_sc0` is the matching primitive for moving compiler/linker table
payloads from RAM staging buffers into REU. ACTC now uses this path for
unresolved external names, procedure `body_ops`, string literals, variable
names, export names, integer literals, variable metadata, procedure metadata,
layout metadata, and string offsets.

## REU Lookup Tables

The same REU strategy should be used for compiler and linker lookup data once
source paging is proven.

ACTC candidates:

- symbol-name strings
- export/procedure tables
- variable metadata
- literal pools
- body-op streams
- source line index checkpoints for diagnostics and multi-pass seeking

Current ACTC table status:

- unresolved external names live in REU behind a 25-byte resident window
- procedure `body_ops` live in REU behind one `BODY_OPS_STRIDE` resident window
- string literals live in REU behind a 24-byte resident window
- variable names and export names live in REU behind 25-byte resident windows
- integer literals live in REU behind a 2-byte resident window
- variable metadata lives in REU behind a 3-byte resident window
- procedure parameter/local metadata lives in REU behind a 4-byte resident window
- procedure layout metadata lives in REU behind a 4-byte resident window
- string offsets live in REU behind a 1-byte resident window

Current ALINK table status:

- object/export/variable names and metadata live in REU-backed fixed-record
  tables behind small resident windows
- direct-PRG relocation records live in REU behind one `RELOC_RECORD_BYTES`
  resident window
- runtime-helper store queues live in REU behind one `RUNTIME_STORE_BYTES`
  resident window
- helper literal address queues live in REU behind one `LINKED_LITERAL_BYTES`
  resident window

ALINK candidates:

- loaded object directory
- external/pending symbol queues
- export lookup tables
- object body-op streams
- string and integer literal pools
- final map/debug records

The rule should be: keep hot fixed-width indexes and the current working set in
normal RAM, but place large variable-length data and cold lookup payloads in REU.
That avoids spending scarce C64 RAM on tables that are not touched every opcode
or parser step.

## Compiler Architecture Change

The replacement for `source_buffer` should be a `SourceReader` abstraction:

- fixed-size source window, initially 512 or 1024 bytes
- current pointer, remaining bytes, EOF flag, line number, and column number
- one-token lookahead for the parser
- carry buffer for tokens that cross a chunk boundary, especially identifiers,
  string literals, comments, and CR/LF pairs. Current focused tests cover
  identifiers, string literals, fixed keyword patterns, statement line ends, and
  semicolon comment lines crossing a REU source window with zero lookahead,
  semicolon comment lines, legal-length identifiers, string literals, and
  inline-space runs spanning multiple small REU windows, plus CR/LF line-ending
  pairs split across the window boundary.

The parser should stop walking raw memory directly. Instead it should ask the
reader for tokens. That makes source size independent of available contiguous
RAM.

## Pass Structure

A practical low-risk design is two streaming passes:

1. Pass 1 validates the module header, collects module variables, procedure
   headers, export names, parameter/local declarations, and enough metadata for
   calls and storage layout.
2. Pass 2 seeks within the REU source cache and emits body operations, literal
   tables, runtime imports, and object content.

Two passes avoid holding the full source in memory while preserving the current
compiler behavior, which depends on knowing procedure/export metadata before
final body emission.

## Object Output

Production ACTC no longer builds the complete object text in `content_buffer`.
With `STREAM_OUTPUT=1`, object emission mirrors production ALINK's streamed
output path:

- begin output for `OBJ/<MODULE>.OBJ`
- write header/import/export sections as they are finalized
- write body/literal sections from bounded staging buffers
- close output

The focused capacity proof emits an `OBJ/MAIN.OBJ` larger than the legacy
`640` byte object buffer through write begin/chunk/close services. Remaining
object-output capacity work is now about moving the compiler's source metadata,
literal pools, symbol tables, and body-op storage out of fixed normal-RAM arrays.
Most ACTC cold metadata has now moved to REU; the remaining capacity work is the
token-safe reader, the pass-overlay driver, and similar REU table pressure in
ALINK.

## Implementation Milestones

1. Raise the current production proof while there is still safe tool-window
   space. Current production `ACTC.PRG` uses `ACTC_REU_SOURCE_CACHE=1`,
   `SOURCE_LIMIT=1280`, and proves a `16646144` byte source compile with
   `PROC MAIN()` discovered after offset `16600000` through REU source staging.
2. Add and prove the tool ABI REU source-cache service shape under the harness.
   Current proof stages source beyond the first `20480` bytes into simulated REU
   and pages later windows back into RAM with a 255-byte lookahead guard.
3. Implement production resident-side REU staging, read, and write services.
   Current resident ABI exports `svc_file_stage_reu_sc0`, `svc_reu_read_sc0`,
   and `svc_reu_write_sc0`; `make -C udos vice-reu-services` now stress-proves
   target-side stage/read/write round-trips under VICE.
4. Add a REU source-cache loader that copies a source file into REU blocks once.
5. Add the first ACTC scanner refill hook that pages fixed RAM windows from the
   REU cache.
6. Move whitespace/comment scanning and symbol/string reading behind a
   token-boundary-safe source reader.
7. Convert module-header and declaration collection to REU-backed pass 1.
8. Convert body operation collection and runtime-import detection to REU-backed
   pass 2.
9. Convert object emission from `content_buffer` to chunked write services.
   Current production `ACTC.PRG` has this path with `STREAM_OUTPUT=1`,
   `CONTENT_BUFFER_SIZE=16`, and `OUTPUT_CHUNK_SIZE=128`.
10. Move large ACTC and ALINK lookup payloads into REU-backed tables. Most ACTC
    cold lookup payloads are now REU-backed; ALINK direct-PRG relocation and
    runtime-helper queues are now REU-backed.
11. Keep synthetic large-source proofs close to the 16 MiB-minus-reserved-REU
    ceiling as source-reader and metadata work changes.

## Current Status

The current production compiler now stages source through REU, refills the scan
window through SourceReader-managed peek/consume paths, keeps 255 bytes of
bounded compatibility lookahead, and streams object output. It is useful for
proving source, symbols, long inline
spaces, one long expression, fixed-pattern page-boundary return expressions,
page-boundary statement terminators, page-boundary comparison operators, boolean
operator wraps in print, assignment, and return paths, local declaration
initializer paths, constant-expression paths
plus procedure-call argument and page-boundary punctuation paths and
`IF`/`WHILE`/`UNTIL` control-flow conditions, one assignment operator wrap, one
procedure parameter delimiter wrap, conversion keyword parsing at a page-aligned
zero-lookahead source-window boundary, builtin helper-name parsing at the same
kind of boundary, builtin helper constants at the same kind of boundary,
group-speculation restore across the first 20 KiB boundary, and grouped-expression
punctuation at a page-aligned
zero-lookahead source-window boundary, plus semicolon comment skipping at and
across page-aligned zero-lookahead boundaries and CR/LF line-ending consumption
across the same boundary. The declaration-count overlay now
captures initializer text while it streams validation so module initializer
values are evaluated from contiguous text instead of stale pointers into an old
source window. The compiler also proves objects beyond the old RAM output
buffer and REU-backed compiler metadata tables, but it is not the final
architecture for large Action programs.
The next
compiler-capacity breakthrough is the parser refactor described here: make the
token-boundary safe `SourceReader` the parser's owner of token lookahead instead
of a compatibility layer under legacy scan-pointer parser code.
