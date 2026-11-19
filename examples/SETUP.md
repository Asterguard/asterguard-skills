# Setup — install the AsterGuard skills in your harness

Every example in this folder runs the same way: the skills are the method (plain Markdown), your harness
runs them, and the **AsterVault MCP gateway** is an optional shared brain. Install once, then run any
example. This is the shared setup each example links to; the authoritative matrix is the
[repo Install section](../README.md#install).

---

## Claude Code (plugin)

Run these two commands in the Claude Code prompt:

```text
/plugin marketplace add Asterguard/asterguard-skills
/plugin install asterguard-security@asterguard-marketplace
```

This registers every skill as a **slash command** — `/local-scan`, `/sca-graph`, `/agent-profiling`,
`/security-engineer`, … — and ships `.mcp.json`, which wires the skills to the gateway. An example that
writes `/local-scan .` means *type that in Claude Code*.

## Cursor

The skill bodies are platform-agnostic Markdown. Build the bundle once, then load it as project rules:

```bash
git clone git@github.com:Asterguard/asterguard-skills.git
cd asterguard-skills
scripts/build-codex.sh          # emits ./dist/codex/ — AGENTS.md + skills/
```

Then, in your project:
- copy the server block from this repo's [`mcp.json`](../mcp.json) into `.cursor/mcp.json`, and
- drop the bundle's `skills/` bodies in as Cursor **project rules** (and/or load its `AGENTS.md`).

In Cursor the skills are **not** slash commands — invoke one by asking the agent by name, e.g.
*"run the local-scan skill on `.`"* (wherever an example shows `/local-scan .`).

## Codex · OpenCode · DeepSeek · any other MCP harness

Same bundle (`scripts/build-codex.sh` → `AGENTS.md` + `skills/`). Register `mcp.json` as an MCP server and
load `AGENTS.md`; invoke skills by name as in Cursor.

---

## Scanners (optional)

The skills shell out to open-source collectors. `local-scan` **auto-installs** any that are missing; to
pre-install on macOS:

```bash
brew install syft grype trufflehog semgrep          # SBOM · CVE · secrets · SAST
pipx install checkov                                 # IaC
```

## Offline vs connected

- **Offline (default)** — leave `ASTERVAULT_MCP_URL` unset. The skills detect the missing gateway and run
  fully local; nothing leaves the box. You get raw findings, graphs, generated tests and reports.
- **Connected** — set `ASTERVAULT_MCP_URL` and attach a per-org **ARS token** for grounded weakness IDs,
  the independent canary verifier, enforcement and shared memory. See
  [`docs/MCP_WIRING.md`](../docs/MCP_WIRING.md); tokens are provisioned per organization on request.

Each example labels which numbers come from which mode.
