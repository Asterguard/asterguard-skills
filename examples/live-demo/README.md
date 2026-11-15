# Live demo — Claude Code ↔ AsterVault MCP

Stand up the AsterVault gateway locally and drive the security skills from Claude Code over a real MCP
connection. No IdP, no cloud, no Postgres — a dev RSA key + a dev policy + env. **Verified working.**

## Run it

```bash
cd examples/live-demo
ASTERVAULT_DIR=~/Nexcraft/astervault ./setup-dev-gateway.sh   # prints the serve cmd + .mcp.json
```

Then: start the gateway (step 1 it prints), paste the `.mcp.json` block into your project, and in
Claude Code run `/mcp` — the `astervault` server appears with **26 tools** (18 in the security
surface). Ask your agent to run the pipeline.

## What it proves (captured from a real MCP client, same protocol Claude Code speaks)

```
CONNECTED. 26 tools exposed; security surface (18): [canary.mint, canary.plant, canary.scan,
  canary.verify, controls.map, graph.enrich, knowledge.graph, knowledge.patterns, knowledge.query,
  memory.capture, memory.promote, memory.recall, policy.apply, registry.list, registry.resolve,
  risk.score, scan.plan, testgen.patterns]
registry.resolve → weakness_id: llm_cfg_egress_no_dlp   (critical, data_exfiltration, LLM02/LLM06)
canary.mint     → value: sk-canary-livedemo-…
memory.capture  → mem_… captured, scope {tenant: demo, team: sec}
memory.recall   → recalled it back (warm)
```

Every call goes through the real gateway: the RS256 JWT is verified, the policy allows it, the
tenant/team **scope is taken from the token** (not the caller), and each call is written to the
append-only audit. Generation (`asterguard-remediation`) → enforcement (`policy.apply`) runs the same
way (see the in-repo `e2e` evidence).

## Transport note

AsterVault identity rides an `Authorization` bearer header, so the demo uses **streamable-HTTP** (stdio
carries no headers). For production the harness runs the OAuth 2.1 flow instead of a static dev token;
the default `.mcp.json` at the repo root points at the real gateway (`ASTERVAULT_MCP_URL`).

## Security

The generated key, policy, and JWT are **dev-only**: localhost, 8-hour token, a permissive policy, and
`default_backend=none`. They live under `.astervault-dev/` (gitignored). Never use them beyond a local
demo.
