"""Static English guide text exposed to MCP clients / AI agents."""

AGENT_INSTRUCTIONS = """
You are controlling an amateur radio or wideband receiver through Hamlib (rigctl).

## Recommended workflow
1. Call `which_rigctl` or `rig_status` if something fails early.
2. Optionally call `list_serial_ports` and `list_rig_models` to discover hardware.
3. Call `rig_connect` (or any get/set tool; get tools auto-connect).
4. Prefer `get_rig_snapshot` for a quick status read.
5. Use get/set frequency, mode, VFO, levels as needed.
6. Call `rig_disconnect` when finished so other apps (e.g. WSJT-X) can use the port.

## Units and formats
- Frequencies are always in integer Hz (example: 14074000 = 14.074 MHz).
- Modes use Hamlib names: USB, LSB, CW, CWR, AM, FM, PKTUSB, PKTLSB, RTTY, etc.
- Passband is in Hz; use 0 for the radio default.
- Levels use Hamlib names such as STRENGTH, SWR, ALC, RFPOWER, RFPOWER_METER_WATTS.

## Defaults (overridable via tool args or environment)
- Model: 1020 (Yaesu FT-817)
- Port: COM5 on Windows, /dev/ttyUSB0 elsewhere
- Baud: 9600
- Stop bits: 2 (required for FT-817)

## Environment variables
HAMLIB_MODEL, HAMLIB_PORT, HAMLIB_BAUD, HAMLIB_STOP_BITS, HAMLIB_DATA_BITS,
HAMLIB_PARITY, HAMLIB_HANDSHAKE, HAMLIB_TIMEOUT_MS, HAMLIB_RETRY,
HAMLIB_CIVADDR, HAMLIB_RIGCTL, HAMLIB_SET_CONF (comma-separated key=value).

## Safety
- `set_ptt(true)` keys the transmitter. Confirm antenna, power, and band legality first.
- Serial ports are exclusive: close WSJT-X / other CAT clients before connecting.
- Prefer receive-side tools for exploration; transmit only when the user intends TX.
- On errors, read the JSON `error` field, then try `rig_status`, `which_rigctl`,
  or reconnect after freeing the port.

## Responses
All tools return JSON strings. Success payloads vary by tool; failures look like:
{"ok": false, "error": "...", "type": "RigError"}
""".strip()

AGENT_GUIDE_MARKDOWN = """
# Hamlib MCP — Agent Guide

This MCP server wraps Hamlib `rigctl` so an AI agent can control CAT-capable
radios and wideband receivers without writing serial code.

## Tools (summary)

| Tool | When to use |
|------|-------------|
| `rig_connect` | Open CAT with optional model/port/baud/stop_bits |
| `rig_disconnect` | Release the serial port |
| `rig_status` | Connection + config (+ snapshot if connected) |
| `get_rig_snapshot` | Frequency, mode, PTT, VFO, S-meter |
| `get_frequency` / `set_frequency` | VFO in Hz |
| `get_mode` / `set_mode` | Mode + passband |
| `get_ptt` / `set_ptt` | RX/TX keying (dangerous) |
| `get_vfo` / `set_vfo` | VFOA/VFOB/... |
| `get_level` / `set_level` | Meters / writable levels |
| `rigctl_command` | Escape hatch for raw Hamlib commands |
| `list_serial_ports` | Enumerate COM / tty devices |
| `list_rig_models` | Search Hamlib model table |
| `which_rigctl` | Resolve the `rigctl` binary in use |

## Example: read then QSY

1. `rig_connect`
2. `get_rig_snapshot`
3. `set_frequency` with `frequency_hz=7074000`
4. `set_mode` with `mode=USB`, `passband_hz=0`
5. `rig_disconnect`

## Example: find FT-817 model id

`list_rig_models` with `filter=FT-817` → model number 1020.
""".strip()
