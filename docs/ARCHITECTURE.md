# Architecture — thin client skills over the AsterVault MCP gateway

Two sides. The client runs the **workflow**; AsterVault (run by us) holds the **knowledge** and does
the privileged work. No proprietary data context is shipped in the plugin.

```
Client agent harness (Claude Code / Codex)
  + asterguard-skills  ── thin: workflow METHOD + MCP tool calls, NO proprietary data
        │  MCP (OAuth 2.1 / audience-bound JWT, per the MCP Authorization spec)
        ▼
AsterVault MCP gateway (run by AsterGuard)
  ├─ existing: AuthN · guardrail · policy PDP/PEP · credential broker · tool proxy · append-only audit
  └─ security-analysis surface (the extension):
       registry.resolve · controls.map · graph.enrich · risk.score · testgen.patterns · scan.plan
     (the 578-weakness registry, the control crosswalk, and the scoring models live HERE)
```

## What runs where

| Concern | Client plugin (skills) | AsterVault MCP (ours) |
|---|---|---|
| Run collectors (grype/checkov/trufflehog) | ✅ local, on the client's box | — |
| Record live agent traffic | ✅ via AsterVault **broker/proxy** (audit trail) | ✅ it *is* the proxy |
| Build the **structural** graph (schema shapes) | ✅ local (`docs/graph-schema.md` is format, not data) | — |
| Resolve a finding → **weakness id / severity / OWASP / CWE** | calls `registry.resolve` | ✅ owns the registry |
| Map weakness/break → **control clauses** | calls `controls.map` | ✅ owns the crosswalk |
| **Enrich / score** the graph (ARS, attack-surface) | calls `graph.enrich` / `risk.score` | ✅ owns the models |
| **Attack patterns** for a weakness (test-gen corpus) | calls `testgen.patterns` | ✅ owns the corpus |
| Report (HTML Artifact) | ✅ local render of enriched graph | — |

**Data-shipping rule:** the client's *structural* findings (ids, package==version, graph shape) go to
AsterVault for enrichment; **our** knowledge never goes to the client. The client's raw code/traffic
stays local — only what a specific MCP tool needs is sent, and AsterVault's modes (B / B+) can broker
and tokenize so regulated data is masked.

## AsterVault is also the proxy

`proxy-recon` does not ship a separate daemon: the agent connects through AsterVault's MCP
broker, which already authenticates, guard-checks (prompt-injection / egress), brokers the tool
call, and writes an append-only audit trail. **Recon = the AsterVault audit log.** The same gateway
that enforces at runtime is the one that observes for assessment.

## Why this shape

- **No IP leaves the server** — resolves "no data context from our side is shipped."
- **One thing run by us** — a single MCP gateway is the whole backend; skills are thin and open.
- **Licensing & tenancy for free** — AsterVault already does OAuth2.1/JWT, policy, quotas, audit.
- **Runtime + assessment unified** — the proxy that guards in production is the recon sensor.

## The extension (in the `astervault` repo, not here)

Add a security-analysis MCP toolset to AsterVault, reusing its PDP/PEP/audit. Tools:
`registry.resolve`, `controls.map`, `graph.enrich`, `risk.score`, `testgen.patterns`, `scan.plan`.
See the astervault repo's design doc for the surface and wiring.
