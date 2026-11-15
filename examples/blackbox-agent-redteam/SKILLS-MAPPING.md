# Skills Mapping — black-box agent red-team

Which skill (and which AsterVault MCP tool) informs each decision in the example.

| Stage | Skill | AsterVault MCP tool | Decision it drives |
|---|---|---|---|
| Recon | proxy-recon | (gateway proxy + audit) | route the agent through the gateway; recon = audit trail |
| Profile | agent-profiling | — (local) | AI-BOM + authority boundaries from tool-calls |
| Data | data-flow | — (local) | where regulated data lives and how it moves |
| Flows | information-flow | — (local) | integrity/confidentiality violations + missing controls |
| Weakness | weakness-graph | `registry.resolve`, `controls.map` | canonical weakness ids + control clauses |
| Static surface | sca-graph | — (local) | dependency tree + CVE roll-up (if any image/deps) |
| Dynamic tests | dast-generation | `testgen.patterns` | grounded probes per endpoint/tool/flow |
| Behavioral | behavioral-redteam | `testgen.patterns` | multi-turn attacks per violating flow |
| Verdict | security-judge | `controls.map` | broke/held + findings + control mapping |
| Report | risk-report | `graph.enrich`, `risk.score` | attack-surface facets + ARS, as an Artifact |

## Substrate (context-engineering collection)

- `multi-agent-patterns` — parallel lane agents under the `security-engineer` orchestrator
- `advanced-evaluation` — the LLM-as-judge in `security-judge`
- `context-optimization` — keep large graphs/transcripts out of the window (reference by path)
- `memory-systems` — the graph as file/graph memory across stages
- `tool-design` — the AsterVault MCP tools return token-efficient, contextual results

## Client/server boundary (the invariant)

Everything in the "Skill" column runs in the client harness; everything in the "AsterVault MCP tool"
column runs server-side. Knowledge never crosses to the client — only per-call answers do.
