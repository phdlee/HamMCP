"""Hamlib MCP server — expose CAT control tools to Cursor / other MCP clients."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from hamlib_mcp import __version__
from hamlib_mcp.agent_guide import AGENT_GUIDE_MARKDOWN, AGENT_INSTRUCTIONS
from hamlib_mcp.rig import SESSION, RigError, find_rigctl

mcp = MCPServer(
    "hamlib",
    version=__version__,
    instructions=AGENT_INSTRUCTIONS,
)


def _ok(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _err(exc: Exception) -> str:
    return _ok({"ok": False, "error": str(exc), "type": type(exc).__name__})


@mcp.resource(
    "hamlib://agent-guide",
    name="Agent guide",
    description="English operating guide for AI agents using this Hamlib MCP server.",
    mime_type="text/markdown",
)
def agent_guide_resource() -> str:
    return AGENT_GUIDE_MARKDOWN


@mcp.prompt(
    name="radio_status_check",
    description="Connect (if needed) and report frequency, mode, PTT, VFO, and S-meter.",
)
def prompt_radio_status_check() -> str:
    return (
        "Use the Hamlib MCP tools to check the radio.\n"
        "1. Call rig_status or rig_connect.\n"
        "2. Call get_rig_snapshot.\n"
        "3. Summarize frequency (Hz and MHz), mode, PTT, VFO, and strength.\n"
        "4. Do not key the transmitter."
    )


@mcp.prompt(
    name="qsy",
    description="Tune to a frequency and mode safely (receive only unless asked).",
)
def prompt_qsy(
    frequency_hz: Annotated[int, Field(description="Target frequency in integer Hz")],
    mode: Annotated[str, Field(description="Hamlib mode name, e.g. USB")] = "USB",
) -> str:
    return (
        f"QSY the radio to {frequency_hz} Hz in {mode}.\n"
        "1. Call rig_connect if not connected.\n"
        f"2. Call set_frequency with frequency_hz={frequency_hz}.\n"
        f"3. Call set_mode with mode={mode} and passband_hz=0.\n"
        "4. Call get_rig_snapshot and confirm.\n"
        "5. Do not set PTT unless the user explicitly requests transmit."
    )


@mcp.tool()
def rig_status() -> str:
    """Show connection state, active serial/config settings, and platform."""
    try:
        status = SESSION.status()
        try:
            status["rigctl"] = find_rigctl(SESSION.config.rigctl_path)
        except RigError as exc:
            status["rigctl"] = None
            status["rigctl_error"] = str(exc)
        if SESSION.connected:
            status["snapshot"] = SESSION.snapshot()
        return _ok(status)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def rig_connect(
    model: Annotated[
        int | None,
        Field(description="Hamlib model number (1020 = Yaesu FT-817). Null = keep config."),
    ] = None,
    port: Annotated[
        str | None,
        Field(description="Serial device, e.g. COM5 or /dev/ttyUSB0. Null = keep config."),
    ] = None,
    baud: Annotated[
        int | None,
        Field(description="Serial baud rate. Null = keep config."),
    ] = None,
    stop_bits: Annotated[
        int | None,
        Field(description="Serial stop bits (FT-817 needs 2). Null = keep config."),
    ] = None,
    rigctl_path: Annotated[
        str | None,
        Field(description="Absolute path to rigctl binary. Null = auto-detect."),
    ] = None,
) -> str:
    """Open CAT connection to the radio (defaults: FT-817 model 1020, COM5, 9600, 2 stop bits)."""
    try:
        overrides = {
            "model": model,
            "port": port,
            "baud": baud,
            "stop_bits": stop_bits,
            "rigctl_path": rigctl_path,
        }
        result = SESSION.connect(**{k: v for k, v in overrides.items() if v is not None})
        return _ok(result)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def rig_disconnect() -> str:
    """Close the CAT session and release the serial port."""
    try:
        return _ok(SESSION.disconnect())
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def get_frequency() -> str:
    """Read VFO frequency in Hz."""
    try:
        hz = SESSION.get_frequency()
        return _ok({"frequency_hz": hz, "frequency_mhz": round(hz / 1_000_000, 6)})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def set_frequency(
    frequency_hz: Annotated[
        float,
        Field(description="Target VFO frequency in integer Hz (e.g. 14074000 for 14.074 MHz)."),
    ],
) -> str:
    """Tune the radio to frequency_hz (integer Hz, e.g. 14074000 for 14.074 MHz)."""
    try:
        hz = SESSION.set_frequency(frequency_hz)
        return _ok({"frequency_hz": hz, "frequency_mhz": round(hz / 1_000_000, 6)})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def get_mode() -> str:
    """Read operating mode and passband width."""
    try:
        return _ok(SESSION.get_mode())
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def set_mode(
    mode: Annotated[str, Field(description="Hamlib mode name: USB, LSB, CW, AM, FM, ...")],
    passband_hz: Annotated[
        int,
        Field(description="Passband width in Hz; 0 means radio default."),
    ] = 0,
) -> str:
    """Set mode (USB/LSB/CW/AM/FM/...). passband_hz 0 = rig default."""
    try:
        return _ok(SESSION.set_mode(mode, passband_hz))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def get_ptt() -> str:
    """Read PTT state (true = transmitting)."""
    try:
        tx = SESSION.get_ptt()
        return _ok({"ptt": tx, "state": "TX" if tx else "RX"})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def set_ptt(
    transmit: Annotated[
        bool,
        Field(description="True keys the transmitter (PTT on). False returns to receive."),
    ],
) -> str:
    """Key or unkey the transmitter. transmit=true keys PTT — use with care."""
    try:
        tx = SESSION.set_ptt(transmit)
        return _ok({"ptt": tx, "state": "TX" if tx else "RX"})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def get_vfo() -> str:
    """Read active VFO (VFOA/VFOB/MEM/...)."""
    try:
        return _ok({"vfo": SESSION.get_vfo()})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def set_vfo(
    vfo: Annotated[str, Field(description="VFO name such as VFOA or VFOB")],
) -> str:
    """Select VFO (e.g. VFOA, VFOB)."""
    try:
        return _ok({"vfo": SESSION.set_vfo(vfo)})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def get_level(
    level: Annotated[
        str,
        Field(description="Hamlib level name, e.g. STRENGTH, SWR, ALC, RFPOWER"),
    ] = "STRENGTH",
) -> str:
    """Read a Hamlib level meter (STRENGTH, SWR, ALC, RFPOWER, RFPOWER_METER_WATTS, ...)."""
    try:
        value = SESSION.get_level(level)
        return _ok({"level": level, "value": value})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def set_level(
    level: Annotated[str, Field(description="Writable Hamlib level name")],
    value: Annotated[float, Field(description="New level value")],
) -> str:
    """Set a writable Hamlib level (model-dependent; FT-817 supports limited levels)."""
    try:
        result = SESSION.set_level(level, value)
        return _ok({"level": level, "value": result})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def get_rig_snapshot() -> str:
    """One-shot read of frequency, mode, PTT, VFO, and S-meter when available."""
    try:
        return _ok(SESSION.snapshot())
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def rigctl_command(
    command: Annotated[
        str,
        Field(description="Raw rigctl command tokens, e.g. 'f' or 'F 7047500' or 'M USB 0'"),
    ],
) -> str:
    """Send a raw interactive rigctl command (e.g. 'f', 'F 7047500', 'M USB 0')."""
    try:
        reply = SESSION.command(command)
        return _ok({"command": command, "reply": reply})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def list_serial_ports() -> str:
    """List serial ports visible on this machine (best-effort, cross-platform)."""
    ports: list[str] = []
    try:
        from serial.tools import list_ports  # type: ignore

        ports = [p.device for p in list_ports.comports()]
    except Exception:
        if platform.system() == "Windows":
            try:
                completed = subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "[System.IO.Ports.SerialPort]::GetPortNames()",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                    check=False,
                )
                ports = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
            except Exception as exc:  # noqa: BLE001
                return _err(exc)
        else:
            import glob

            ports = sorted(
                glob.glob("/dev/ttyUSB*")
                + glob.glob("/dev/ttyACM*")
                + glob.glob("/dev/cu.*")
                + glob.glob("/dev/tty.usb*")
            )
    return _ok({"ports": ports, "platform": platform.system()})


@mcp.tool()
def list_rig_models(
    filter: Annotated[
        str,
        Field(description="Case-insensitive substring match against manufacturer/model text"),
    ] = "FT-817",
) -> str:
    """Search Hamlib model list (uses `rigctl -l`). filter matches manufacturer/model text."""
    try:
        rigctl = find_rigctl(SESSION.config.rigctl_path)
        completed = subprocess.run(
            [rigctl, "-l"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise RigError(completed.stderr.strip() or "rigctl -l failed")
        needle = (filter or "").lower()
        matches: list[str] = []
        for line in completed.stdout.splitlines():
            if not needle or needle in line.lower():
                matches.append(line.rstrip())
        return _ok({"filter": filter, "count": len(matches), "models": matches[:200]})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def which_rigctl() -> str:
    """Resolve which rigctl binary will be used."""
    try:
        path = find_rigctl(SESSION.config.rigctl_path)
        path_on_path = shutil.which("rigctl")
        return _ok(
            {
                "resolved": path,
                "path_rigctl": path_on_path,
                "configured": SESSION.config.rigctl_path,
                "platform": platform.system(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


def main() -> None:
    # Auto-connect is intentionally off — serial ports should be claimed explicitly.
    # Agents should call rig_connect (or get_* which auto-connects via ensure_connected).
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
