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

## Metering & entitlement — the ARS token

The gateway Bearer JWT proves *who* is calling. Running a scan also draws on an **organization's**
entitlement, so connected scan/run/review calls carry a second, per-org credential — the **ARS token**,
sent as the **`X-ARS-Token`** header (an `asg_…` service credential, scope `scan:run`). Every call it
carries is metered to the org and returns an `audit_id`.

```bash
# set from your secret store (CI) — never commit it; the ars-token skill reads, attaches, and renews it
export ASTERGUARD_ARS_TOKEN="asg_…"
```

A signed-in member can instead let the `ars-token` skill mint-or-fetch the org's *Default* scan token on
first use. **Offline mode needs no ARS token** — local runs draw no quota. The `ars-token` capability skill
owns this end to end (resolve → attach alongside the Bearer JWT → renew on `401 invalid or missing
X-ARS-Token`); the raw value never lands in this repo or in `./.asterguard/`.

## Privileged offensive tier — the offensive token

Offensive **execution** changes a live agent's runtime behavior, so it runs on a **separate, higher-trust
credential**, not the scan token. A third header gates it — the **offensive token** (`asg_off_…`, scope
**`offensive:run`**), sent as **`X-ARS-Offensive-Token`**:

```bash
# set from your secret store (CI) — a privileged grant, provisioned-on-request, separately rotated
export ASTERGUARD_OFFENSIVE_TOKEN="asg_off_…"
```

The gateway PDP **enforces** it: a behavior-changing attack (the attacker↔target proxy exchange,
`exploit-chain`, live canary planting, a non-default attacker model, the forge engine) without
`offensive:run` is blocked — **`403 offensive privilege required`**. This draws the privilege line between
**plan** and **execute**: `recon` / `attack-planner` *plan* an attack on the scan token (`scan:run`);
nothing *executes* one without the offensive token. The `offensive-token` capability skill owns it
(require authorization → attach alongside `X-ARS-Token` + the Bearer JWT → renew on `403`; never persist
the raw value, never downgrade to the scan token for execution). *(The PDP enforcement + the
forge-behind-MCP engine the token unlocks + the token minting are the server side — an astervault
follow-up.)*

## The shared brain's store — SQLite or Postgres

The gateway *is* the shared brain: the `knowledge.*` corpus and the `memory.*` records (what
`knowledge-recall` reads and `memory-capture` writes) persist behind it. That persistence is a
**pluggable, gateway-side backend** — the skills call the same tools no matter which is wired:

| Backend | When | Set on the gateway |
| --- | --- | --- |
| **Postgres** | Team-shared, durable, multi-node — the source of truth, and it also backs the audit log. Pick this to share memory across teammates, harnesses, and boxes. | `ASTERVAULT_DATABASE_URL=postgresql://…/astervault` |
| **SQLite** | One box, a pilot, or an air-gapped install — durable memory that survives restarts without standing up Postgres. | `ASTERVAULT_MEMORY_DB=/var/astervault/knowledge.db` |
| *In-memory* | Nothing wired — ephemeral, for tests and throwaway runs. | *(default)* |

Selection order is **Postgres → SQLite → in-memory**: set `ASTERVAULT_DATABASE_URL` and the gateway uses
Postgres (the same store also backs audit); otherwise set `ASTERVAULT_MEMORY_DB` for a durable single
file; set neither and memory is process-local. Both durable backends honor the same scope isolation and
the same three-method contract, so **start on SQLite and move to Postgres when the team grows** — nothing
in the skills changes.

This is the *shared* store. Engagement stays **local-first** regardless (`./.asterguard/` files, no store
at all); the backend above only decides how the structural state it syncs is shared and persisted.

## Per-harness

- **Claude Code** — `.mcp.json` is picked up automatically when the plugin is installed.
- **Cursor** — copy the block into `.cursor/mcp.json` (or point Cursor's MCP settings at `mcp.json`).
- **Codex** — `scripts/build-codex.sh` carries `mcp.json` into the emitted bundle; point Codex's MCP
  config at it.
- **OpenCode** — register `mcp.json` as an MCP server; load the bundle's `AGENTS.md` + `skills/`.
- **DeepSeek harness / any other** — the bundle is model-agnostic; point the harness's MCP config at
  `mcp.json` (or set `ASTERVAULT_MCP_URL`). Offline mode needs no gateway at all.

## Why it matters (cross-harness, like the memory it serves)

Because every harness connects to the **same** gateway, the knowledge and memory compound across tools:
a decision captured from a Cursor session is recalled in a Codex session, and the approved patterns are
the same everywhere. The skills are the method; the gateway is the shared brain.
