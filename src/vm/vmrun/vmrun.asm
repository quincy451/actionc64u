; Staged vm.com runner source for ActionC64U.
;
; Planned behavior:
;   1. pick filename from cpm_fcb, or default to MAIN    AVM
;   2. open/read the file through BDOS into cpm_default_dma / a buffer
;   3. validate the 10-byte AVM1 header
;   4. enter AcheronVM at payload + entry_offset
;   5. provide a native helper callable via calln for demo payloads
;
; This source is staged while the AcheronVM + CP/M-65 link recipe is still
; blocked on the external toolchain setup documented in docs/blockers.md.

.export start

start:
    rts
