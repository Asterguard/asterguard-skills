# Skills Mapping — scan → red team

Which skill (and MCP tool) drives each step of the end-to-end flow.

| Step | Skill | AsterVault MCP tool(s) | Produces |
|---|---|---|---|
| Recall + scope | `security-engineer` + `knowledge-recall` | `memory.recall`, `knowledge.patterns` | the brief + prior breaks/patterns |
| Scan (local) | `local-scan` | — (grype/checkov/trufflehog) | raw SCA/IaC/secrets/AI-BOM |
| SCA graph | `sca-graph` | — (local) | dep tree + deduped CVEs |
| Data + info flow | `data-flow`, `information-flow` | — (local) | the flows + violations |
| Agent profile | `agent-profiling` | `knowledge.graph` | AI-BOM + authority boundaries |
| Weakness/control | `weakness-graph` | `registry.resolve`, `controls.map` | weakness ids + control clauses |
| Pick targets | `information-flow` + `risk-context` | `graph.enrich`, `risk.score` | the trifecta paths, prioritized |
| Red team | `behavioral-redteam` → `attacker`/`defender`/`judge` | `testgen.patterns`, `canary.*`, proxy | an adaptive episode + verdicts |
| Prove | `canary-testing` + `judge` | `canary.scan/verify` | proven break (egress hit) |
| Remediate | `remediation` | `policy.apply` (+ `asterguard-remediation` `to_pr`) | a policy PR, enforced on merge |
| Report | `risk-report` | `graph.enrich`, `risk.score` | the proven attack-path Artifact |
| Capture | `memory-capture` | `memory.capture`, `memory.promote` | memory + a grown attack corpus |

## The loop invariant

Everything in the "Skill" column runs in the client harness; everything in the MCP column is the one
standardized source behind the gateway. **Recall seeds the front, capture compounds the back** — the
proven breaks from this run become `testgen.patterns` seeds for the next, so the flow is self-improving.

## Reusability

The red-team middle (`attacker` / `defender` / `judge`) is the same reusable triad used in evals and
continuous testing — here it's composed by `behavioral-redteam` and fed by the scan→graph front end. Add
a new view or a new step as a skill; the standardized schema keeps it all consistent.
