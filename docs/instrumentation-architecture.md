# Instrumentation architecture

Instrumentation is intentionally additive to the VICE 3.10 core.

| Surface | Hook | Data exposed |
| --- | --- | --- |
| Keyboard | `monitor_binary.c`, command `0x74` | row, column, pressed; RESTORE pseudo-cells |
| IEC | `iecbus_observer` after machine port resolution | CPU and per-drive resolved masks |
| C128 | `c128_get_timing_sample()` | clock, raster line/cycle, VIC half-cycle |
| VDC | `vdc_get_timing_sample()` | clock, raster counters, busy deadline, draw state |

VICE remains the owner of emulation state. Observers are called synchronously
on VICE's emulation thread after state resolution. They must not mutate VICE
state, block, or call back into the monitor. Copy data into a bounded queue if
another thread needs to consume it. Registration should occur before emulation
starts and be removed after emulation stops; callback registration is not a
concurrent operation.

The pristine release is `upstream/v3.10.0`; instrumentation is replayable as
focused commits on `work/instrumentation`.
