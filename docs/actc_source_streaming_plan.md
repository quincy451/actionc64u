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
long inline spaces before a `PrintIE` literal cross REU source offset `$005000`.
Small-window proofs also verify the declaration-count overlay can skip
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
or smaller harness builds can still override `ACTC_SOURCE_WINDOW`, provided the
linked resident image remains below the overlay scratch base at `$8000`. The
linker enforces that invariant. This is not the final parser architecture yet.
The production UDOS resident now exports the
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
same scan window. Fixed-pattern pointer consumes now revalidate each byte
through the pattern-character SourceReader helper before advancing, while
preserving the caller's pattern-index scratch byte through SourceReader
save/restore helpers. Boolean pre-scan wraps now
intentionally route into the
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
primitives. Resident scan-pointer whitespace, blank-line, line-skip, and
pattern-search advances now route through semantic SourceReader helpers instead
of parser-side generic consumes. Shared project-manifest line skipping, line
copying, and removal shifting also route through `project_reader_*` helpers
instead of open-coded raw scan-pointer consumes. Resident, body-collect overlay, and body-preallocate overlay
`THEN`/`DO` terminator probes now consume keyword characters through shared
expected-character helpers. Keyword
token pattern matching now routes each matched pattern
character and post-keyword token-boundary check through SourceReader helpers
that own pattern-index setup, keyword-probe/open scan offset setup, the source
peek, uppercase compare/classification, source consume, and pattern-index advance. The central
string-literal helper now delegates
token-target setup to a SourceReader begin helper, delegates each literal byte
to a SourceReader helper that owns the peek, length check, store, source consume,
and post-consume token-target restore, and delegates literal termination plus
closing-quote consumption to a matching SourceReader finish helper. Both
resident symbol-copy
helpers now delegate stream-offset setup to SourceReader begin helpers and build
tokens in a SourceReader-owned carry buffer before publishing to the legacy
resolver scratch name, while
preserving the existing returned-`Y` scanner ABI. The resident module-header
copy helper uses the same carry-buffer publish path for `declared_module_name`.
Preallocation call-argument `(`, `,`, `)`, and string quote delimiters now route
through a generic SourceReader expected-character helper while leaving broader
scan loops as byte consumers; the resident plain-call argument separator/close
path now selects `,` and `)` by attempting exact SourceReader consumes rather
than by parser-owned compares. The plain and flat call-argument scanners also
classify wrapper-owned comma/close delimiters through non-consuming SourceReader
matches before their existing consume paths handle owned bytes. Runtime
call-argument separator/close handling now uses the same exact consume-attempt
pattern after `(` and after each emitted argument.
Preallocation call-argument string content bytes now route through a SourceReader
string-byte helper that rejects line ends and closing quotes before consuming.
Preallocation plain-call argument fallback bytes now route through a SourceReader
scan-byte helper that rejects argument delimiters before consuming.
Preallocation line-call scan fallback bytes now route through a SourceReader
scan-byte helper that rejects line ends and string delimiters before consuming.
Preallocation flat call-argument scan fallback bytes now route through a
SourceReader scan-byte helper that rejects flat argument terminators before
consuming.
Inline source spaces and tabs now route through a SourceReader whitespace
consume helper instead of direct scanner-side generic byte consumes.
Declared real/word assignment `=` preallocation uses the same helper so the
delimiter consume remains bound to the SourceReader boundary.
Resident module variable initializer `=`, `[`, and `]` delimiters now consume
complete punctuation tokens through the expected-token helper; the required
`]` closer relies on the helper carry result rather than a parser-side
peek/compare.
Procedure body assignment `=`, optional second `=`, and local int `[ ]`
delimiters use the helper after matching, with the required `]` closer using the
helper as the only closer check.
Resident preallocation conversion/operator `)` delimiters also use the exact
helper rather than open-coded peek/cmp/consume sequences.
Preallocation REAL unary print close parens now consume through SourceReader
and fall back on its carry result. Preallocation and runtime REAL binary
assignment/print operator probes now route through a SourceReader `+`/`-`/`*`/`/`
match helper before the matched byte is consumed by the existing exact-character
path; binary print verifies the wrapper-owned close paren through a
non-consuming SourceReader match helper.
Preallocation condition comparison operators use the helper for matched `=`,
`<`, `>`, `<>`, `<=`, and `>=` bytes. Preallocation boolean primary grouping
keeps the speculative `(` branch in parser code, but the closing `)` now
consumes through SourceReader and falls back on its carry result.
Preallocation print statement wrappers keep their speculative `(` branch in
parser code, but their closing `)` delimiters now consume through SourceReader
and fall back on its carry result while their inner argument scanners remain
byte-scan loops.
Signed word prefix preallocation now uses the exact helper for the literal `0`
and `-` tokens.
Runtime grouped value term `(` and `)` delimiters now use the same exact helper,
keeping group punctuation ownership with SourceReader.
Runtime boolean primary grouping keeps the speculative `(` branch in parser
code, but the closing `)` now consumes through the helper and falls back on its
carry result.
Runtime call-argument `(`, `,`, and `)` delimiters also route through exact
SourceReader consume attempts, leaving only the expression emitters as the
argument scanners.
Runtime value optional `=`, group-open `[`, and group-close `]` delimiters
consume complete punctuation tokens through the expected-token helper.
Runtime sum `+` and `-` operators use the same helper after the operator branch
has selected the matched token.
Small value parser optional `=`, group-open `[`, and group-close `]` delimiters
also consume complete punctuation tokens through the expected-token helper.
Small constant-sum terminator validation now classifies caller-owned `,`, `)`,
and `]` delimiters through the non-consuming SourceReader match helper.
Small boolean primary grouping follows the same shape: parser code still
recognizes the speculative `(` branch, while SourceReader owns the closing `)`
consume and fallback result.
Small condition-clause comparison operators `=`, `<`, `>`, `<=`, `>=`, and `<>`
route each matched operator byte through the helper.
Common non-consuming `=`, `<`, and `>` probes that only decide whether a
comparison follows now route through a SourceReader comparison-operator helper.
Initial resident comparison dispatches in runtime/small-expression parsers now
use that helper and classify the returned operator byte only after a match.
Resident preallocation comparison dispatches use the same helper, and dispatches
that already proved a comparison byte now branch to the remaining `>` case
instead of rechecking for an impossible miss.
Post-`<` optional `=`/`>` suffix probes in resident preallocation, runtime, and
small-expression comparison parsers now route through a SourceReader suffix-match
helper before the matched suffix is consumed by the existing operator-specific
path.
Resident line-end/EOF probes in statement terminator, return-expression, and
small constant-sum paths now route through a SourceReader line-end match helper.
Common non-consuming `(` probes that only select a grouped/call parse path now
route through a SourceReader open-paren match helper that does not clobber the
generic `compare_char` scratch byte.
Common non-consuming `=` probes that only select assignment/value parse paths now
route through the generic SourceReader exact-character match helper.
Post-`>` optional `=` suffix probes in resident comparison parsers now use that
same exact-character match helper before consuming the suffix.
Required `]` closers in runtime and small value-expression groups now rely on
the SourceReader exact-character consume result instead of a parser-side
peek/compare before the consume.
Small decimal-expression comparison operators use the same per-byte helper for
the matching operator forms.
Small decimal arithmetic operators `+`, `-`, `*`, and `/` use the helper after
their operator branches have matched.
Small decimal and positive-word sum parsers classify caller-owned `,`, `)`,
`]`, `=`, `<`, and `>` terminators through a non-consuming SourceReader numeric
sum stop helper before dispatching owned arithmetic operators.
Small decimal grouping keeps the speculative `(` branch in parser code, but the
closing `)` now consumes through SourceReader and falls back on its carry result.
Small, plain-word, and positive-word decimal parsers now consume matched digit
bytes through a SourceReader decimal-digit helper instead of generic parser-side
Scan-Y consumes.
Speculative top-level arithmetic and boolean scanner punctuation classifies
caller-owned `,`, `]`, `)`, and `(` through non-consuming SourceReader matches,
then consumes owned punctuation through the exact-character helper in the
selected labels. Generic consumes remain only for the arbitrary-byte scan-loop
bodies in those routines.
Speculative top-level arithmetic and boolean arbitrary-byte scan-loop bodies now
route through SourceReader scan-byte helpers, with the boolean helpers preserving
the prior-symbol tracking used by keyword-boundary detection through a
SourceReader classifier helper. Boolean scan initialization and punctuation
consumes now reset that prior-symbol state through SourceReader helpers instead
of parser-side direct state stores.
Preallocation positive-word arithmetic operators `+`, `-`, `*`, and `/` use the
same helper after their operator branches have matched.
Preallocation positive-word grouping follows the same close-delimiter ownership
in both factor and optional grouped-sum parsing.
Runtime `REAL(` opener matching uses uppercase expected-character helpers for
the keyword bytes and the normal expected-character helper for the open paren.
Runtime `REAL(var)` bridge close-paren matching uses the normal
expected-character helper after the bridge argument has matched.
Runtime explicit `REAL(...)` value parsing uses the helper for close parens and
the signed `0-` prefix bytes.
Runtime REAL assignment binary operators `+`, `-`, `*`, and `/`, plus unary
`FABS(...)`/`FSQRT(...)` close parens, use the same helper after their matched
bytes have been selected.
Runtime `PRINTR`/`PRINTRE` REAL print close parens consume through the same
helper and fall back on its carry result.
Runtime `PRINTI`/`PRINTIE` expression close parens also consume through the
same helper and fall back on its carry result.
Runtime explicit REAL assignment parsing also uses the helper for bridge and
numeric close parens plus signed `0-` prefixes.
Runtime REAL condition comparison operators `=`, `<`, `>`, `<>`, `<=`, and
`>=` use the expected-character helper for each matched byte.
Runtime integer condition comparison operators use the same helper for their
matched `=`, `<`, `>`, `<>`, `<=`, and `>=` bytes.
Procedure export parameter-list open parens, comma separators, and closing
parens consume through exact SourceReader attempts.
Shared keyword-open parsing now consumes the matched `(` through the same helper
after keyword-pattern matching succeeds.
The body-collect overlay's local keyword-open scanner now delegates pattern
setup and per-byte pattern consumes to overlay-local SourceReader helpers, so
the local reader offset and pattern-index scratch are not mutated by parser-side
keyword code; its matched open-paren probe also uses the local exact-character
match helper before the existing consume path.
Parser-side symbol helpers now store and terminate token bytes through
SourceReader token helpers rather than writing the token buffer directly, and
resident streaming symbol-copy plus module-header copy loops now share one
SourceReader token-byte helper that peeks, classifies, stores, consumes, and
updates the scanner offset. Procedure export name copies now use a matching
non-consuming SourceReader token-byte helper so the legacy returned-`Y`
parameter-list ABI is preserved while token storage is centralized, and a
SourceReader finish helper now saves the returned source offset while
terminating and publishing to the export table. The source-header
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
scanner now consumes through a local SourceReader helper instead of open-coded
peek/consume loops, its full whitespace skipper now delegates CR/LF-inclusive
classification and consumption to a matching helper, and declaration line-end
validation now uses a local line-end match helper. Declaration line skipping now
delegates source-window availability, EOF, CR/LF detection, optional LF
consumption, and byte advance to a local helper. Var/export-name symbol-copy
loops now delegate each candidate token byte to local helpers that own source
peeking, delimiter classification, symbol validation, token-window storage, and
source consumption.
Procedure parameter punctuation checks now use local exact-character
match/consume helpers. Declaration-tail delimiter checks use the same
exact-character helpers before initializer parsing. Declaration keyword
character matching routes through the local peek/consume wrapper, and keyword
delimiter matching now delegates the source peek plus delimiter classification
to a local helper while retaining the existing rewind behavior for failed
probes. The delimiter classification and failed keyword-match rewind are now
centralized behind local declaration-overlay SourceReader helpers instead of
being open-coded in the keyword dispatcher. Declaration initializer expression wrapper delimiters
(`[`, `]`) plus line-end probes now route through the same local match/consume
helpers, while arbitrary initializer body characters route through a local
body-byte helper that owns source peek, capture, validation, and consume.
Declaration whitespace and line skipping now peek and consume
through the local wrappers, and mixed spaces, tabs, CR, and LF before module
declarations are covered across multiple tiny source windows with no lookahead.
Remaining raw declaration-overlay source reads are limited by test to the local
peek helper itself. The declaration-loop EOF probe now checks for an
already-loaded byte and uses the local peek helper without forcing a new
body-only source window into the declaration pass. The name-cache comparator
uses an explicit cache-pointer alias over the saved source scan slot, so it is
no longer treated as a source scan read. The source-header overlay now
centralizes its raw source reads behind a refill-aware local peek helper.
Leading-whitespace and inline module-spacing skips now delegate accepted-byte
classification and consumption to local SourceReader helpers. Its
module-keyword character consumes now route through a local SourceReader helper
that owns the peek, uppercase compare, and consume sequence. Requested
module-name character matching also routes through a local helper that owns the
source peek, token validation, requested-name compare, and consume sequence while
preserving the existing token-end distinction. The overlay has small-window
coverage for leading whitespace spanning multiple source windows, including
mixed spaces, tabs, CR, and LF, the `MODULE` keyword crossing a window boundary,
mixed space/tab module-name spacing spanning multiple source windows, and long
module names spanning multiple tiny source windows with no lookahead.
The body-collect overlay now routes source reads through the resident
SourceReader peek callback instead of reading the resident scan pointer
directly, with mixed spaces, tabs, CR, and LF before body statements covered
across multiple tiny source windows with no lookahead. Its assignment,
local-call, and runtime real-condition suffix delimiter probes now use a local
non-consuming SourceReader match helper before existing exact consumes advance
the source. Its binary REAL assignment and runtime REAL expression operator
probes now also select `+`, `-`, `*`, and `/` through that helper before
consuming the matched operator. Body-collect exact runtime REAL close-delimiter
and signed-prefix probes now use the same non-consuming helper before their
existing consumes. Runtime REAL condition operator dispatch now also probes
`=`, `<`, and `>` through the helper before reaching the existing consume
labels. Positive-word parser sum-loop terminators, sum operators, term
operators, and grouped-expression punctuation now use the same helper for exact
probes before existing consumes, while positive-word decimal digit reads and
REAL assignment small-int dispatch now use a local non-consuming decimal-digit
peek helper. Body-collect `THEN`/`DO` terminator checks now centralize EOF, LF,
and CR probes behind a local non-consuming line-end matcher.
The runtime expression print/value close-paren probe now also uses the
non-consuming match helper. Statement dispatch and return-without-value line-end
checks now use the local line-end matcher before falling through to assignment
or runtime expression parsing.
The body-preallocate overlay mirrors that real-condition suffix
ownership for link-selected runtime import discovery: initial `=`, `<`, and
`>` comparison dispatch plus optional `<`/`>` comparison suffix probes no longer
read source bytes directly in parser code.
Its top-level post-symbol call/assignment dispatch now uses the same
non-consuming match helper before the existing exact delimiter consumes. Its
binary REAL print and assignment operator probes also select `+`, `-`, `*`, and
`/` through that helper before consuming the matched operator. Nested-call
open-paren probes in body-preallocate call-argument scanners now use the same
non-consuming helper before the existing scanner-specific follow-up. Their
loop-level EOF, line-end, quote, open-paren, and close-paren classifiers also
route through exact non-consuming matches before arbitrary-byte fallback
consumes advance the source.
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
- selected machine-code body records live in REU bank `$04`, separate from the
  closure and metadata tables in bank `$03`
- direct-PRG relocation records live in REU behind one `RELOC_RECORD_BYTES`
  resident window
- external closure names and placement metadata live in REU-backed tables
- no runtime-helper store or literal-address queues remain; ACTC emits machine
  records and ordinary relocations, and helper code arrives through selected
  `RT_*.OBJ` modules

ALINK candidates:

- loaded object directory
- reachable external closure queue and placement metadata
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
   Current proof stages source beyond offset `20480` into simulated REU and
   pages 1280-byte windows back into RAM with a 255-byte lookahead guard.
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
    cold lookup payloads are now REU-backed; ALINK direct-PRG relocation,
    machine-body, and object-closure tables are now REU-backed. The former
    runtime-helper synthesis queues have been removed rather than relocated.
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
body-resident runtime fallback condition operators and conversion close
punctuation through exact-character SourceReader consumes,
group-speculation restore across REU source offset `$005000`, and grouped-expression
punctuation at a page-aligned
zero-lookahead source-window boundary, plus semicolon comment skipping at and
across page-aligned zero-lookahead boundaries and CR/LF line-ending consumption
across the same boundary. Decimal parsers and real-assignment digit dispatch now
ask SourceReader for digit values instead of owning digit range classification
in parser loops, and signed real literal sentinels now consume exact bytes
through SourceReader instead of peeking and comparing in parser code. Explicit
real/int conversion close delimiters now do the same exact-byte SourceReader
consume, leaving fallback decisions on the helper carry result. The
declaration-count overlay now
captures initializer text while it streams validation so module initializer
values are evaluated from contiguous text instead of stale pointers into an old
source window. The compiler also proves objects beyond the old RAM output
buffer and REU-backed compiler metadata tables, but it is not the final
architecture for large Action programs.
The first complete parser path now uses cached SourceReader token lookahead:
positive-word expressions consume whole decimal and symbol tokens plus
single- and double-byte comparison/operator tokens. Resident SourceReader owns
the cache and cross-window scans, while body collection and preallocation share
one overlay-owned token parser through ABI v2 token callbacks. This avoids both
a resident-capacity regression and separate byte-oriented overlay parsers.
A 256-byte, zero-lookahead proof splits decimal tokens, builtin-symbol tokens,
operators, nested grouped expressions, and grouped signed expressions across
the source-window boundary.
The small byte-valued decimal factor parser now also consumes one complete
SourceReader decimal token and rejects values with a nonzero high byte. Its
body-callback proof begins `255` at offset 254 in a 256-byte, zero-lookahead
window, so the token crosses the refill boundary while retaining the byte-range
contract.
The two resident byte-valued comparison paths now share one token-driven tail.
It consumes all six comparison forms as complete tokens and preserves the
operator and left operand on the machine stack while parsing the right operand,
so nested grouped comparisons cannot corrupt outer parser state. A focused
target-executed proof independently detects corruption of either saved value.
The declaration-count overlay now applies the same stack-safe left-operand rule
to captured initializer expressions; module initializers such as `2>(1=1)` and
`0<(2=2)` retain their outer comparison state through nested factors.
The resident byte-valued sum, term, and grouped-factor paths now dispatch and
consume arithmetic punctuation as complete tokens. Sum and term accumulators
are preserved on the machine stack across recursive grouped operands, fixing
incorrect results such as `2+(3+4)`, `2*(3+4)`, and `8/(2+2)` while retaining
the non-consuming `AND`/`OR` handoff to the boolean parser.
The resident byte-valued boolean parser now consumes `AND`, `OR`, and `NOT` as
complete symbol tokens and grouped punctuation as complete punctuation tokens.
Its `AND` and `OR` paths preserve each left operand on the machine stack while
recursively parsing the right operand, fixing flat and nested expressions such
as `1 OR 0`, `1 OR (0 AND 0)`, and `0 AND (1 OR 1)`. A 256-byte,
zero-lookahead proof starts `OR` at offset 255 so keyword recognition crosses a
source-window boundary without a compatibility character scan.
The resident runtime boolean parser now uses the same complete symbol tokens for
`AND`, `OR`, and `NOT`, consumes grouped parentheses as complete punctuation
tokens, and dispatches all six integer comparison forms from one complete
comparison token. Existing 256-byte, zero-lookahead target proofs split each
comparison form and both runtime group delimiters at offset 255. Consolidating
the comparison suffix branches also recovered 26 resident bytes, leaving 271
bytes below the UDOS floor in the production layout.
The supported dynamic integer runtime sum operators, `+` and `-`, and grouped
runtime terms now also use complete punctuation tokens. A variable-expression
proof places each sum operator at offset 255 in a 256-byte, zero-lookahead
window and verifies the right operand is read from the next page. The resulting
production layout retains 252 bytes below the UDOS floor.
The resident runtime REAL condition parser now dispatches `=`, `<`, `>`, `<=`,
`>=`, and `<>` from one complete comparison token and consumes that token once.
Its target proof starts every operator at offset 255 in a 256-byte,
zero-lookahead window, verifies the exact existing `rt_f_cmp` body-op lowering,
and checks that the next source page supplies either the two-byte suffix or the
right operand. Removing the character/suffix dispatch recovered 76 resident
bytes, so the production layout now retains 328 bytes below the UDOS floor.
Runtime call-argument open, separator, empty-close, and final-close punctuation
now use a shared SourceReader expected-token consume helper. Existing target
proofs place `(`, `,`, and `)` independently at offset 255 in a 256-byte,
zero-lookahead source window and preserve the exact local-call object bodies.
The reusable helper costs 16 resident bytes, leaving 312 bytes below the UDOS
floor while avoiding repeated token validation in each punctuation path.
The shared `INT`/`REAL`/`FABS`/`FSQRT` keyword-open consumer now validates one
complete symbol token and one complete `(` token rather than replaying a fixed
pattern byte by byte. The resident runtime REAL fallback uses that helper and
also consumes conversion close delimiters and the signed conversion `-` as
complete punctuation tokens. Its 256-byte, zero-lookahead target proof places
`REAL` at offset 254 and each delimiter independently at offset 255 while
preserving the exact `rt_i_to_f` plus `rt_f_cmp` object stream. Consolidating
the keyword consumer and removing the duplicate runtime spelling shrinks the
resident layout by 26 bytes: production BSS now ends at `$49AB`, leaving 338
free byte addresses before the `$4AFE` UDOS floor.
The signed REAL conversion's leading sentinel now consumes exactly one decimal
zero token. A target regression places that zero at offset 255, verifies the
next page begins with `-`, and rejects a two-byte `00` token split over the same
boundary. The regression also exposed and fixed two resident-fallback state
bugs: conversion lowering now preserves the live source cursor before using
`Y` as a literal high byte, and REAL comparison lowering preserves its control
literal across RHS conversion arithmetic. The latter production-path fix uses
10 resident bytes, so production BSS now ends at `$49B5`, leaving 328 free byte
addresses before the UDOS floor.
Optional small-value `=`, `[`, and `]` delimiters in module initializers,
constant expressions, runtime values, and the resident `PrintI`/`PrintIE`
fallback now consume complete punctuation tokens. The print fallback also
centralizes its optional `]` and required `)` close tokens. A nine-case target
matrix places each delimiter independently at offset 255 in a 256-byte,
zero-lookahead window across module, constant-print, and variable-print paths
while checking the next-page byte and exact object output. A separate
production-overlay proof exercises the same failed constant probe and runtime
fallback through `ACTC_OVL6`. Those tests exposed two state defects: a failed
constant-expression probe now restores a dedicated SourceReader window mark
and invalidates stale token lookahead before runtime fallback, and the legacy
print fallback now accepts the same optional wrapper syntax as the shared
runtime-value parser. Production BSS ends at `$49EA`, leaving 275 free byte
addresses before the `$4AFE` UDOS floor.
Dynamic integer `*` and `/` now use the same complete-token product parser as
the existing runtime sum path and preserves normal product-before-sum
precedence and grouping. The emit overlay validates the compact parser result,
then writes ordinary native OBJ1 `m` code, nested `__idata`/`__iptr` exports,
and generic named/import relocations. ALINK no longer analyzes or compiles this
integer body shape; it resolves the resulting object and appends only the
selected `rt_i_mul`, `rt_i_div`, and `rt_print_i` modules. The focused matrix
covers precedence, assignment/store/readback, unsigned division, division by
zero returning zero, malformed legacy bodies, and missing helpers. At that
milestone production ACTC BSS ended at `$4ACD`, retaining 49 bytes below the
`$4AFE` UDOS resident floor; the body-collect overlay retained 184 bytes and the
emit overlay retained 1,006 bytes in their `$A000-$BFFF` windows.
Later overlay-ABI growth brought the production BSS end to `$4AF6`, exactly the
old eight-byte minimum margin. Production now omits seventeen scratch bytes
owned exclusively by disabled resident body-preallocation, body-collection,
layout, positive-word-parser, and object-emitter fallbacks. BSS therefore ends
at `$4AE5`, leaving 25 bytes before the UDOS floor, and the enforced minimum is
24 bytes. Explicit fallback builds retain their state; focused build coverage
also keeps their long layout branches and shared hardware-symbol table valid.
Overlay ABI v3 removed 28 legacy context bytes that no shipped pass reads, plus
35 bytes of resident code that initialized three of those retired entry groups.
ABI v4 added fixed-address routine metadata, and ABI v5 adds the resident
binary32 `REAL CONST` evaluator callback. The current context is 231 contiguous
bytes and also includes resident decimal-word and uppercase-hex-byte formatter
callbacks shared by object emitters. Production CODE ends at `$674E`, and BSS
ends at `$6BC1`. Current UDOS swaps the low resident during tool execution and
preserves its callable island from `$9800`, leaving 11,327 bytes below that
boundary.
Capacity coverage derives the preserved floor from UDOS labels and structural ABI coverage
rejects holes or any reintroduction of the retired context exports.
Inline assembly remains outside resident memory: pass 4 writes each assembled
block to one 256-byte page at reserved REU bank `$FF`, addresses
`$FF0000-$FF0EFF`. Body/debug records occupy `$FF1000-$FF3FCF`, and fixed names
and metadata occupy `$FFF000-$FFF27F`, so the source cache can use banks
`$01-$FE` without collision. Pass 9/H reuses the `$8000` page buffer, `$8100`
label index, and `$8110+` overlay-only scratch while converting those pages into
ordinary machine and relocation records. The body stream carries only a private
base-36 block selector, so source text does not expand `body_ops` and cannot
create false runtime imports.
Remaining raw Scan-Y byte consumes in `ACTC` are now restricted by test to token
helpers and SourceReader helper internals. Remaining raw Scan-PTR byte consumes
in `ACTC` are now restricted by test to token, string, pattern, and semantic
SourceReader helper internals.

One-argument byte-in-A and word-in-X/Y runtime calls inside compiler-owned
integer control now run in base-36 pass G, `ACTC_OVLG.BIN`, instead of expanding
resident ACTC or returning compact code to ALINK. The pass consumes one complete
word expression, emits ABI-specific relocatable argument setup and a helper
import, and declines wider or unknown helper ABIs. Its 6,645-byte image leaves
1,547 bytes free under a 512-byte capacity reserve in the 8 KiB emitter
window.

Units that combine those runtime calls with ASMBLOCK, `=*(...)`, or numeric
absolute-address declarations use base-36 pass H, `ACTC_OVLH.BIN`. Compact
fixed-address-only units first use pass J; on a not-applicable result, pass H
emits one ordinary machine OBJ with the required symbol relocations and
link-selected runtime imports. Pass H's 8,064-byte image leaves exactly 128 bytes
under its reserve in `$A000-$BFFF`; pass J's 7,901-byte image leaves 291 bytes
under its 256-byte reserve. A direct ACTC/ALINK/VICE probe returns 42 through the word function
ABI, stores trace value 41, and observes SID volume 8. A second probe calls
KERNAL CHROUT at numeric address `$FFD2` without selecting a library object.

Pass A's bounded two-REAL-parameter identity function now keeps the captured
return storage separate from caller argument storage. Its generic 157-byte OBJ
can therefore bind two reordered arguments by value and return either named
parameter through A/X without changing ALINK. The second-return direct PRG
stores 2.0 after checking both caller values and both reverse-bound parameter
copies. `ACTC_OVLA.BIN` is 7,418 bytes with 774 bytes free under its enforced
768-byte reserve.

The first bounded REAL control-flow function runs in base-36 pass K,
`ACTC_OVLK.BIN`. It recognizes the exact two-REAL-parameter finite
comparison/select body and a bounded four-REAL `FClamp` assignment/print root,
plus a bounded single-return selected-binary expression over two REAL
parameters. It emits ordinary machine OBJ records, and declines other forms before opening
output. The clamp root captures each named storage use instead of assuming
fixed declaration order. The finite function similarly captures caller,
parameter-bind, comparison, and return roles while retaining its bounded body
shape. Its 5,877-byte image leaves 2,315 bytes in
`$A000-$BFFF`. The focused release
probe links only integer conversion, comparison, and comparison's transitive
special-value support; its direct PRG verifies 2.0/1.0 parameter copies and a
1.0 result in VICE. Additional direct PRGs permute all clamp storage roles and
the finite function's module/parameter naming; they produce 5.0 and 1.0,
respectively. General REAL expression/control lowering remains the next compiler
dependency.

Base-36 pass L, `ACTC_OVLL.BIN`, now turns the bounded child-first stream into
ordinary executable OBJ1 for a straight-line module-REAL subset. It retains
native line offsets, emits `__idata`-anchored source-variable debug records,
allocates private four-byte temporaries, and supports 16-bit export and
relocation offsets. It also lowers up to two nonrecursive two-REAL-parameter
functions: caller-pushed pointers
are reverse-bound to per-function static parameter cells, A/X returns the
selected result pointer, and bounded all-REAL locals use ordinary static OBJ1
storage plus DBG1 local records. `MAIN` may call either function; either
declaration direction may assign the other function's result, use the call
directly as an operand in a supported intrinsic return tree, or pass bounded
calls as arguments to another call while the graph remains acyclic. Every
function-to-function edge saves caller parameters, locals, and live temporaries
on the hardware stack, stages the A/X result, and restores the caller cells.
Self and mutual cycles are rejected before generic emission. Nested expression,
local-storage, two-callee, backward/forward call-chain, nested
local-call-expression, and nested user-call-argument PRGs pass ACTC, ALINK, DBG
validation, and VICE execution while loading only reachable runtime modules.
Its 6,124-byte image leaves 2,068 bytes in `$A000-$BFFF`.

Base-36 pass M, `ACTC_OVLM.BIN`, is the control-capable build of that shared
emitter. It claims only a supported REAL function containing one nonnested
`IF`/`ELSE`, maps all six relations through `rt_f_cmp`, and emits absolute long
branches to internal `__rfN` and `__reN` OBJ1 code exports. Both arms may contain
the supported REAL expression operations and converge on one terminal return.
Its 6,998-byte image leaves 1,194 bytes under a 1 KiB reserve without consuming
pass L's 2 KiB margin.

Base-36 pass N, `ACTC_OVLN.BIN`, separately claims the same bounded function
form when at least one function contains a second conditional. It supports at
most two conditionals per function, either sequentially or nested to depth two,
with a distinct false/end export pair per control. Its 7,120-byte image leaves
1,072 bytes under the same 1 KiB reserve while passes L and M remain
byte-identical.

Base-36 pass O, `ACTC_OVLO.BIN`, separately claims the third conditional and
supports at most four controls per function, either sequentially or nested to
depth four. Its four-slot label indexing remains ordinary OBJ1 metadata. The
7,123-byte image leaves 1,069 bytes under the 1 KiB reserve while passes L, M,
and N remain byte-identical. Recursive/reentrant local frames, loops, early
returns, more than four controls, deeper control nesting, unrestricted
user-call argument trees and nested call expressions, mixed types, arbitrary
signatures, and recursion remained the next compiler dependency at that
checkpoint.

Base-36 pass P, `ACTC_OVLP.BIN`, claims a supported REAL function only when a
`RETURN(expr)` occurs inside an open bounded `IF`/`ELSE`. The emitted pointer
return ends the live path immediately, while compilation continues through the
remaining body operations to close internal labels and verify a required
terminal fallback return. One-control and depth-four fixtures exercise early
true, early else, and fallback paths. The 7,147-byte image leaves 1,045 bytes
under the 1 KiB reserve while passes L through O remain byte-identical. Loops,
controls beyond four, deeper nesting, unrestricted call trees, mixed types,
arbitrary signatures, and recursive/reentrant frames remain pending.
