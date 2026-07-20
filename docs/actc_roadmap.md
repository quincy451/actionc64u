# ACTC Roadmap

Current target: widen `ACTC.PRG` object emission while keeping the direct
`ACTC.PRG -> ALINK.PRG -> BIN/MAIN.PRG` path green under UDOS/VICE.

Near-term work:

- keep source parsing and object emission deterministic
- continue moving large source and lookup data toward REU-backed streaming
- preserve object records needed by ALINK for dead-strip and helper selection
- continue moving supported body lowering into ACTC-emitted native machine and
  relocation records instead of adding shape-specific linker compilers
- generalize the proven pass-K function and bounded
  `FSign`/`FMin`/`FMax`/`FClamp` paths into reusable REAL expression,
  control-flow, call, and return lowering for dependency-sized MATH1 modules
- avoid adding launch-time runtime responsibilities to ACTC
- keep focused UDOS VICE gates green after each compiler widening step

Proof gates:

- `make -C ../udos vice-action-actc`
- `make -C ../udos vice-action-actc-alink-launch`
- `make -C ../udos vice-action-actc-alink-launch-runtime-matrices`
- shape-specific launch gates such as the print/math direct PRG probes
