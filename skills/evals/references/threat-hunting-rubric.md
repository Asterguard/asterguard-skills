# Threat-Hunting & Deep-Analysis Rubric (100 pts)

Applied to the hunting + deep-investigation runbooks: `indicator-threat-hunt`,
`hunt-agentic-ttp-credential-access`, `hunt-tool-abuse-lateral`, `proactive-pattern-campaign-hunt`,
`advanced-agent-threat-hunt`, `apt-agent-threat-hunt`, `hunt-over-privilege`,
`hunt-prompt-injection-exposure`, `hunt-exfil-paths`, `deep-dive-indicator-analysis`,
`correlate-finding-groups`. `rubric_type: THREAT_HUNTING`. Adapted from the source
`threat_hunting_rubric.py`, re-expressed in our terms (security-graph queries, gateway grounding,
`audit_id` citation, agent kill-chains).

Scored by `security-judge` over the run output + the engagement trace. **Pass ≥ 80**; a case may raise
`min_passing_score`.

| # | Category | Pts | What earns the points |
|---|----------|-----|-----------------------|
| 1 | **Scope & Query** | 25 | **Hunt scope (10):** a clear hypothesis + bounds — target agent/identity/component, lookback window, the TTP/weakness in play (10; partial = 5). **Query execution (15):** the hunt actually queried the evidence — the built security graph (`graph.enrich`/local graph), recorded egress/tool-call audit, `knowledge.query` patterns — and returned concrete hits (15; thin/empty results = 8). |
| 2 | **Data Analysis & Correlation** | 30 | **Analysis depth (15):** the returned telemetry was analyzed for anomalous agent behavior — over-privilege, untrusted-input→privileged-action, confidential→egress paths (15; shallow = 8). **Correlation (15):** host/tool/identity activity correlated with intel and mapped to ATT&CK/CAPEC/weakness refs across ≥2 evidence sources (15; partial = 10). |
| 3 | **Findings Classification** | 15 | Findings classified with a `verdict` event — true-positive agent threat vs benign — each citing its evidence span / canary hit; inconclusive recorded as right-censored, not forced binary (15; inconclusive disposition only = 8). |
| 4 | **Hunt Documentation** | 15 | `record-in-engagement` captured the hunt methodology, queries, and findings as substantive typed events (>30 chars) with `audit_id`s (15; brief = 10; none = 0). |
| 5 | **Operational Artifacts** | 15 | **Mermaid diagram (5):** the hunt flow/sequence diagram (5/0). **Execution metadata (5):** run duration + metered `audit_id`s recorded (5/0). **Summary (5):** an actionable hunt-lead / next-step summary — e.g. a detection gap to close via `detection-as-code-agent-rules` (5/0). |

**Evidence check:** a hunt that classifies a threat must cite the graph path / audit event / canary hit
that proves it. A "confirmed" finding with no out-of-band evidence is capped at the inconclusive tier
for Findings Classification (8).

**Scorecard fields:** `profile_name: THREAT_HUNTING_RUBRIC`, `category_scores{…}`, `feedback[…]`,
`metadata{findings}`.
