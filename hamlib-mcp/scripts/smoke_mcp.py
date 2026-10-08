"""stdio smoke test: list tools and call get_rig_snapshot against the live radio."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def main() -> int:
    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", str(ROOT), "python", "-m", "hamlib_mcp"],
        env={
            "HAMLIB_MODEL": "1020",
            "HAMLIB_PORT": "COM5",
            "HAMLIB_BAUD": "9600",
            "HAMLIB_STOP_BITS": "2",
        },
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", ", ".join(t.name for t in tools.tools))

            connect = await session.call_tool("rig_connect", {})
            print("CONNECT:", _text(connect))

            snap = await session.call_tool("get_rig_snapshot", {})
            print("SNAPSHOT:", _text(snap))

            freq = await session.call_tool("set_frequency", {"frequency_hz": 7_074_000})
            print("SET:", _text(freq))
            restore = await session.call_tool("set_frequency", {"frequency_hz": 7_047_500})
            print("RESTORE:", _text(restore))

            await session.call_tool("rig_disconnect", {})
            return 0


def _text(result) -> str:
    parts = []
    for block in result.content:
        text = getattr(block, "text", None)
        if text is not None:
            parts.append(text)
    raw = "\n".join(parts) if parts else str(result)
    try:
        return json.dumps(json.loads(raw), ensure_ascii=False)
    except Exception:
        return raw


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}", file=sys.stderr)
        raise
