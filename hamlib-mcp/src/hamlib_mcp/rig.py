"""Cross-platform Hamlib backend via one-shot `rigctl` invocations."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class RigError(RuntimeError):
    """Raised when a Hamlib / rigctl operation fails."""


@dataclass
class RigConfig:
    model: int = 1020  # Yaesu FT-817
    port: str = "COM5"
    baud: int = 9600
    stop_bits: int = 2
    data_bits: int = 8
    parity: str = "None"
    handshake: str = "None"
    timeout_ms: int = 2000
    retry: int = 3
    civaddr: str | None = None
    rigctl_path: str | None = None
    extra_set_conf: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> RigConfig:
        extra: dict[str, str] = {}
        raw_extra = os.environ.get("HAMLIB_SET_CONF", "").strip()
        if raw_extra:
            for item in raw_extra.split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    extra[key.strip()] = value.strip()

        return cls(
            model=int(os.environ.get("HAMLIB_MODEL", "1020")),
            port=os.environ.get("HAMLIB_PORT", _default_port()),
            baud=int(os.environ.get("HAMLIB_BAUD", "9600")),
            stop_bits=int(os.environ.get("HAMLIB_STOP_BITS", "2")),
            data_bits=int(os.environ.get("HAMLIB_DATA_BITS", "8")),
            parity=os.environ.get("HAMLIB_PARITY", "None"),
            handshake=os.environ.get("HAMLIB_HANDSHAKE", "None"),
            timeout_ms=int(os.environ.get("HAMLIB_TIMEOUT_MS", "2000")),
            retry=int(os.environ.get("HAMLIB_RETRY", "3")),
            civaddr=os.environ.get("HAMLIB_CIVADDR") or None,
            rigctl_path=os.environ.get("HAMLIB_RIGCTL") or None,
            extra_set_conf=extra,
        )


def _default_port() -> str:
    return "COM5" if platform.system() == "Windows" else "/dev/ttyUSB0"


def _vendor_rigctl() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    candidates = list(root.glob("vendor/**/bin/rigctl.exe")) + list(
        root.glob("vendor/**/bin/rigctl")
    )
    return candidates[0] if candidates else None


def find_rigctl(explicit: str | None = None) -> str:
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return str(path)
        raise RigError(f"rigctl not found at HAMLIB_RIGCTL={explicit}")

    vendor = _vendor_rigctl()
    if vendor and vendor.is_file():
        return str(vendor)

    which = shutil.which("rigctl")
    if which:
        return which

    if platform.system() == "Windows":
        for candidate in (
            Path(r"C:\WSJT\wsjtx\bin\rigctl-wsjtx.exe"),
            Path(r"C:\Program Files\WSJT-X\bin\rigctl-wsjtx.exe"),
            Path(r"C:\Program Files (x86)\WSJT-X\bin\rigctl-wsjtx.exe"),
        ):
            if candidate.is_file():
                return str(candidate)

    raise RigError(
        "rigctl not found. Install Hamlib and put rigctl on PATH, "
        "or set HAMLIB_RIGCTL to the full path."
    )


class RigSession:
    """Hamlib CAT session using one-shot rigctl (reliable across OSes)."""

    def __init__(self, config: RigConfig | None = None) -> None:
        self.config = config or RigConfig.from_env()
        self._lock = threading.RLock()
        self._connected = False
        self._last_rigctl: str | None = None

    @property
    def connected(self) -> bool:
        return self._connected

    def status(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "connected": self.connected,
            "config": asdict(self.config),
            "platform": platform.system(),
        }
        try:
            info["rigctl"] = find_rigctl(self.config.rigctl_path)
        except RigError as exc:
            info["rigctl"] = None
            info["rigctl_error"] = str(exc)
        return info

    def connect(self, **overrides: Any) -> dict[str, Any]:
        with self._lock:
            for key, value in overrides.items():
                if value is None or not hasattr(self.config, key):
                    continue
                if key in {"model", "baud", "stop_bits", "data_bits", "timeout_ms", "retry"}:
                    value = int(value)
                setattr(self.config, key, value)

            self._last_rigctl = find_rigctl(self.config.rigctl_path)
            freq = self._run(["f"])
            self._connected = True
            hz = int(freq.splitlines()[0].strip())
            return {
                "ok": True,
                "frequency_hz": hz,
                "config": asdict(self.config),
                "rigctl": self._last_rigctl,
            }

    def disconnect(self) -> dict[str, Any]:
        with self._lock:
            was = self._connected
            self._connected = False
            return {
                "ok": True,
                "message": "disconnected" if was else "already disconnected",
            }

    def ensure_connected(self) -> None:
        if not self._connected:
            self.connect()

    def _base_args(self) -> list[str]:
        rigctl = self._last_rigctl or find_rigctl(self.config.rigctl_path)
        self._last_rigctl = rigctl
        # Note: rigctl -t is send-cmd terminator, -o is VFO mode — not timeout/retry.
        # Timeouts/retries are Hamlib conf tokens.
        args = [
            rigctl,
            "-m",
            str(self.config.model),
            "-r",
            self.config.port,
            "-s",
            str(self.config.baud),
            "-C",
            f"stop_bits={self.config.stop_bits}",
            "-C",
            f"data_bits={self.config.data_bits}",
            "-C",
            f"serial_parity={self.config.parity}",
            "-C",
            f"serial_handshake={self.config.handshake}",
            "-C",
            f"timeout={self.config.timeout_ms}",
            "-C",
            f"retry={self.config.retry}",
        ]
        if self.config.civaddr:
            args.extend(["-c", self.config.civaddr])
        for key, value in self.config.extra_set_conf.items():
            args.extend(["-C", f"{key}={value}"])
        return args

    def _run(self, tokens: list[str]) -> str:
        cmd = self._base_args() + tokens
        creationflags = 0
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(self.config.timeout_ms / 1000.0, 1.0) + 10.0,
            check=False,
            creationflags=creationflags,
        )
        if completed.returncode != 0:
            err = (completed.stderr or completed.stdout or "").strip()
            raise RigError(
                f"rigctl failed ({completed.returncode}) for {' '.join(tokens)}: {err}"
            )
        out = (completed.stdout or "").strip()
        if not out and completed.stderr.strip():
            # Some builds print RPRT only
            err = completed.stderr.strip()
            if err.startswith("RPRT ") and not err.endswith(" 0"):
                raise RigError(err)
        return out

    def command(self, cmd: str) -> str:
        with self._lock:
            self.ensure_connected()
            tokens = cmd.strip().split()
            if not tokens:
                raise RigError("empty command")
            return self._run(tokens)

    def get_frequency(self) -> int:
        return int(self.command("f").splitlines()[0])

    def set_frequency(self, hz: int | float) -> int:
        hz_i = int(hz)
        self.command(f"F {hz_i}")
        return self.get_frequency()

    def get_mode(self) -> dict[str, Any]:
        lines = self.command("m").splitlines()
        return {
            "mode": lines[0],
            "passband_hz": int(lines[1]) if len(lines) > 1 else None,
        }

    def set_mode(self, mode: str, passband_hz: int = 0) -> dict[str, Any]:
        self.command(f"M {mode.upper()} {int(passband_hz)}")
        return self.get_mode()

    def get_ptt(self) -> bool:
        return self.command("t").splitlines()[0].strip() not in {"0", "OFF", "off"}

    def set_ptt(self, transmit: bool) -> bool:
        self.command(f"T {1 if transmit else 0}")
        return self.get_ptt()

    def get_vfo(self) -> str:
        return self.command("v").splitlines()[0]

    def set_vfo(self, vfo: str) -> str:
        self.command(f"V {vfo.upper()}")
        return self.get_vfo()

    def get_level(self, level: str) -> str:
        return self.command(f"l {level}").splitlines()[0]

    def set_level(self, level: str, value: float | int | str) -> str:
        self.command(f"L {level} {value}")
        return self.get_level(level)

    def snapshot(self) -> dict[str, Any]:
        self.ensure_connected()
        data: dict[str, Any] = {
            "frequency_hz": self.get_frequency(),
            "mode": self.get_mode(),
            "ptt": self.get_ptt(),
        }
        try:
            data["vfo"] = self.get_vfo()
        except RigError:
            data["vfo"] = None
        try:
            data["strength"] = self.get_level("STRENGTH")
        except RigError:
            data["strength"] = None
        return data


SESSION = RigSession()
