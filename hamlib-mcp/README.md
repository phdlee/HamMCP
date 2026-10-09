# hamlib-mcp

MCP server that lets Cursor and other MCP clients control amateur radios and wideband receivers through [Hamlib](https://github.com/Hamlib/Hamlib) `rigctl`.

Designed so an AI agent can operate the radio **from MCP metadata alone** (server instructions, tool docs, resources, and prompts) without a separate human briefing.

**Language:** Python 3.10+  
**Default radio:** Yaesu FT-817 — Hamlib model `1020`, serial `COM5`, `9600` baud, `2` stop bits (overridable).

## Agent discoverability

This package exposes:

| Surface | Purpose |
|---------|---------|
| MCP `instructions` | Workflow, units, defaults, env vars, safety |
| Tool docstrings + parameter `Field` descriptions | How to call each tool |
| Resource `hamlib://agent-guide` | Longer English operating guide |
| Prompts `radio_status_check`, `qsy` | Ready-made agent workflows |

## Requirements

1. Python 3.10+
2. A CAT-capable radio (tested: Yaesu FT-817)

### Hamlib `rigctl` (included on Windows)

| OS | What you need |
|----|----------------|
| **Windows** | Nothing extra — **Hamlib 4.7.2 x64 is bundled** under `vendor/hamlib-w64-4.7.2/`. `which_rigctl` should resolve to `rigctl.exe` in that tree after `git clone`. |
| Linux | Install distro `rigctl` (e.g. `libhamlib-utils`) or set `HAMLIB_RIGCTL`. |
| macOS | `brew install hamlib` or set `HAMLIB_RIGCTL`. |

Override with `HAMLIB_RIGCTL` if you want a different build. The server only falls back to WSJT-X `rigctl-wsjtx.exe` when bundled `rigctl` and `PATH` are both missing.

License: see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Setup

```bash
git clone https://github.com/phdlee/HamMCP.git
cd HamMCP/hamlib-mcp
uv sync
```

Quick CAT check (without MCP):

```bash
uv run python -c "from hamlib_mcp.rig import SESSION; print(SESSION.connect()); print(SESSION.snapshot())"
```

## Cursor MCP registration

```json
{
  "mcpServers": {
    "hamlib": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "PATH_TO_CLONE/HamMCP/hamlib-mcp",
        "python",
        "-m",
        "hamlib_mcp"
      ],
      "env": {
        "HAMLIB_MODEL": "1020",
        "HAMLIB_PORT": "COM5",
        "HAMLIB_BAUD": "9600",
        "HAMLIB_STOP_BITS": "2"
      }
    }
  }
}
```

On Linux/macOS set `HAMLIB_PORT` (e.g. `/dev/ttyUSB0`). Optionally set `HAMLIB_RIGCTL` to an absolute `rigctl` path.

## MCP tools

| Tool | Purpose |
|------|---------|
| `rig_connect` / `rig_disconnect` / `rig_status` | Session lifecycle |
| `get_frequency` / `set_frequency` | VFO Hz |
| `get_mode` / `set_mode` | Mode + passband |
| `get_ptt` / `set_ptt` | RX/TX keying (use carefully) |
| `get_vfo` / `set_vfo` | VFO select |
| `get_level` / `set_level` | S-meter, SWR, power, … |
| `get_rig_snapshot` | Frequency + mode + PTT (+ VFO/S-meter) |
| `rigctl_command` | Raw Hamlib command |
| `list_serial_ports` / `list_rig_models` / `which_rigctl` | Discovery |

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `HAMLIB_MODEL` | `1020` | Hamlib model number |
| `HAMLIB_PORT` | `COM5` / `/dev/ttyUSB0` | Serial device |
| `HAMLIB_BAUD` | `9600` | Baud rate |
| `HAMLIB_STOP_BITS` | `2` | Stop bits (FT-817 needs 2) |
| `HAMLIB_RIGCTL` | auto | Path to `rigctl` |
| `HAMLIB_SET_CONF` | empty | Extra `-C key=value` pairs, comma-separated |

## How it talks to the radio

The server uses **one-shot `rigctl`**: each Hamlib command spawns a short-lived process. A single `get_rig_snapshot` may start `rigctl` up to five times (`f`, `m`, `t`, `v`, `l STRENGTH`). Agents that poll every 1–2 seconds will keep spawning processes and may contend with WSJT-X on the same COM port.

Pin the binary with `HAMLIB_RIGCTL` if you do not want the WSJT-X fallback (`rigctl-wsjtx.exe`).

## Safety

- `set_ptt(true)` keys the transmitter. Confirm antenna and power first.
- Close WSJT-X / other CAT clients before connecting — serial ports are exclusive.
- Prefer `get_*` tools for monitoring; use TX tools intentionally.
- Only `set_frequency` / `rigctl_command` (`F ...`) change the VFO; if the radio jumps to ~7 MHz while you work elsewhere, look for a polling agent or WSJT-X CAT, not read-only tools.
