# Agent guide (hamlib-mcp)

Same content is also available at runtime as MCP resource `hamlib://agent-guide`.

You are controlling an amateur radio or wideband receiver through Hamlib (`rigctl`).

## Recommended workflow

1. Call `which_rigctl` or `rig_status` if something fails early.
2. Optionally call `list_serial_ports` and `list_rig_models` to discover hardware.
3. Call `rig_connect` (or any get/set tool; get tools auto-connect).
4. Prefer `get_rig_snapshot` for a quick status read.
5. Use get/set frequency, mode, VFO, levels as needed.
6. Call `rig_disconnect` when finished. Avoid polling in a 1–2 second loop.

## One-shot rigctl behavior

- One Hamlib command = one `rigctl` subprocess (serial open → command → exit).
- `get_rig_snapshot` ≈ five subprocesses per call.
- Idle flashing every 1–2 s means something is still calling MCP tools or another app is using CAT on the same COM port.
- Unexpected QSY to ~7 MHz is almost always `set_frequency` / `F` or WSJT-X — not `get_*` reads.

## Units and formats

- Frequencies are always in integer Hz (example: `14074000` = 14.074 MHz).
- Modes use Hamlib names: `USB`, `LSB`, `CW`, `CWR`, `AM`, `FM`, `PKTUSB`, `PKTLSB`, `RTTY`, etc.
- Passband is in Hz; use `0` for the radio default.
- Levels use Hamlib names such as `STRENGTH`, `SWR`, `ALC`, `RFPOWER`, `RFPOWER_METER_WATTS`.

## Defaults (overridable)

- Model: `1020` (Yaesu FT-817)
- Port: `COM5` on Windows, `/dev/ttyUSB0` elsewhere
- Baud: `9600`
- Stop bits: `2` (required for FT-817)

## Safety

- `set_ptt(true)` keys the transmitter.
- Serial ports are exclusive.
- Prefer receive-side tools unless the user explicitly requests transmit.

## Responses

Tools return JSON strings. Failures look like:

```json
{"ok": false, "error": "...", "type": "RigError"}
```
