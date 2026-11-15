# Weakness resolution & control mapping — via AsterVault MCP

This skill does **not** carry the weakness registry or the control crosswalk — that proprietary
knowledge lives in the AsterVault MCP gateway (run by AsterGuard). The skill builds the structural
weakness graph locally and calls these MCP tools to resolve and map:

## `registry.resolve`

Resolve a structural finding to its canonical weakness.

```jsonc
// request
{ "finding": { "lane": "sca|iac|secrets|sast|agentic", "rule_id": "...", "cwe": "CWE-200",
               "cve_id": "CVE-…", "title": "…", "component": "…" } }
// response
{ "weakness_id": "llm_cfg_egress_no_dlp", "name": "…", "category": "data_exfiltration",
  "base_severity": "critical", "owasp_llm_refs": ["LLM02","LLM06"], "cwe_refs": ["CWE-200"],
  "kill_chain_role": "sink", "severity_modifiers": ["external_facing","data_sensitivity"] }
```

Attach `weakness_id` to the `weakness` node; add `manifests` edges to the affected components.

## `controls.map`

Map a weakness (or a behavioral break family) to the control clauses it violates.

```jsonc
// request
{ "weakness_id": "llm_cfg_egress_no_dlp" }           // or { "break_family": "exfil" }
// response
{ "controls": [ { "framework": "soc2", "id": "CC6.1", "text": "…" },
                { "framework": "gdpr", "id": "Art-32", "text": "…" } ] }
```

Set `meta.controls` on the weakness node from the response. Frameworks: soc2, hipaa, pci-dss, gdpr,
nist-ai-rmf, iso-27001.

## Guidelines

- Never cache or re-ship the responses as a bundled dataset — resolution is a per-finding MCP call so
  the knowledge stays server-side and current.
- If the MCP gateway is unreachable, degrade: keep the structural weakness node with its CWE/OWASP
  (public) and mark `meta.controls = "unresolved"` — never invent a control citation.

See [OWASP-LLM mapping](./owasp-llm.md) (public) for the one rollup that is safe to keep client-side.
