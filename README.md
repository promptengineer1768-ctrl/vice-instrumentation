# VICE 3.10 Instrumentation Extension

This branch contains a small, reviewable instrumentation layer on top of the
official VICE 3.10.0 source release. The pristine release is preserved in the
`upstream/v3.10.0` branch; changes live on `work/instrumentation`.

## Extensions

- Binary-monitor command `0x74` injects a physical keyboard matrix transition,
  including machine-specific RESTORE pseudo-cells. It requires monitor API v2
  and covers C64, C128, VIC-20, Plus/4, C16, PET, CBM-II, CBM 5x0, C64DTV,
  and SCPU64 targets.
- IEC observers receive resolved CPU and drive line masks on C64, C64DTV,
  Plus/4, and VIC-20. PET intentionally has no IEC observer hook.
- `c128_get_timing_sample()` exposes C128 clock, raster line/cycle, and VIC
  half-cycle timing.
- `vdc_get_timing_sample()` exposes VDC clock, raster position, internal memory
  counter, rendering state, and the exact emulated `busy_until` clock for VDC
  register/memory operations.

The APIs are deliberately additive and do not alter default emulation behavior.
Callbacks are optional and must copy state if they retain it.

## Building

Build VICE using the normal 3.10 prerequisites and platform instructions. The
source tree is a normal VICE checkout; run `./configure`, then `make` (or the
native Windows build procedure). The extension does not require the MCP server.

## Parallel instrumented sessions

`tools/vice_session.py` starts one emulator with an operating-system-assigned
loopback monitor port and a private configuration, log, stdout, stderr, and
session manifest directory. It records the exact child PID and terminates only
that child when interrupted; it never searches for or kills unrelated VICE
processes. Pass emulator arguments after the launcher options:

```text
python tools/vice_session.py --vice path/to/x64sc.exe --keep -- -warp game.d64
```

Use `--port` only when an external controller already owns a unique port. The
default `0` allocation is the safe choice for parallel workers. Successful
sessions are removed unless `--keep` is supplied; failures always retain their
logs and `session.json` evidence.

## Protocol reference

See [`doc/binary-monitor-keyboard-matrix.txt`](doc/binary-monitor-keyboard-matrix.txt)
for the `0x74` wire format. C headers documenting the native observer APIs are
in `src/iecbus.h`, `src/c128/c128.h`, `src/vdc/vdc.h`, and `src/vdc/vdc-mem.h`.

## Rebasing

Import each new upstream release as a new pristine branch, then replay the
focused instrumentation commits. Do not develop directly on the pristine
branch.

## License

This extension and its modifications are distributed under the GNU General
Public License, version 2 or any later version. VICE's existing files retain
their original copyright and license notices. See [`COPYING`](COPYING).
