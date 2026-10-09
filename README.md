# HamMCP

Collection of **Model Context Protocol (MCP)** servers for amateur radio and related RF tooling.

Each subdirectory is an independent MCP package you can register in Cursor (or any MCP client). New servers will be added here over time.

## Packages

| Directory | Status | Description |
|-----------|--------|-------------|
| [`hamlib-mcp/`](hamlib-mcp/) | Active | Control CAT radios and wideband receivers through [Hamlib](https://github.com/Hamlib/Hamlib) (`rigctl`) |

## Language policy

All documentation, README files, MCP tool descriptions, prompts, resources, and code comments in this repository are written in **English only**.

## Quick start (hamlib-mcp)

```bash
cd hamlib-mcp
uv sync
```

Register in Cursor user MCP config (`~/.cursor/mcp.json` / `%USERPROFILE%\.cursor\mcp.json`):

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

Windows clones include Hamlib `rigctl` under `hamlib-mcp/vendor/` (no separate Hamlib install).
See [`hamlib-mcp/README.md`](hamlib-mcp/README.md) for tools, safety, and Linux/macOS notes.

## Repository layout

```
HamMCP/
  README.md           # this file — overview of all MCP packages
  hamlib-mcp/         # Hamlib radio control MCP server
  <future-mcp>/       # additional MCP servers go here
```

## License

Unless noted otherwise in a subdirectory, code in this repository is provided for personal / amateur-radio use. Third-party binaries (e.g. Hamlib) remain under their own licenses and are not redistributed by default.
