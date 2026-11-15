# MCP wiring — one gateway, every harness

The skills are thin; all knowledge, analysis, and memory live behind the **AsterVault MCP gateway**.
Installing the plugin ships the MCP config so the skills auto-connect to that gateway — no manual
setup, and the same gateway across Claude Code, Cursor, Codex, and other harnesses.

## What ships

- **`.mcp.json`** (repo root) — Claude Code auto-discovers this and registers the `astervault` server.
- **`mcp.json`** — the generic copy for harnesses that read `mcp.json`.

Both declare one Streamable-HTTP server:

```json
{ "mcpServers": { "astervault": { "type": "http", "url": "${ASTERVAULT_MCP_URL:-https://astervault.local/mcp}" } } }
```

## Configure

Point it at your gateway (defaults to `https://astervault.local/mcp`):

```bash
export ASTERVAULT_MCP_URL="https://<your-astervault-host>/mcp"
```

AsterVault is an OAuth 2.1 Resource Server (MCP Authorization spec, RFC 9728/8707); the harness runs
the OAuth flow on first use and binds the token to the gateway's audience. No secrets live in this
repo — the gateway issues and scopes everything.

## Per-harness

- **Claude Code** — `.mcp.json` is picked up automatically when the plugin is installed.
- **Cursor** — copy the block into `.cursor/mcp.json` (or point Cursor's MCP settings at `mcp.json`).
- **Codex / others** — `scripts/build-codex.sh` carries `mcp.json` into the emitted bundle; point the
  harness's MCP config at it.

## Why it matters (cross-harness, like the memory it serves)

Because every harness connects to the **same** gateway, the knowledge and memory compound across tools:
a decision captured from a Cursor session is recalled in a Codex session, and the approved patterns are
the same everywhere. The skills are the method; the gateway is the shared brain.
