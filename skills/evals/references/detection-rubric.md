# Detection-Engineering Rubric (100 pts)

Applied to the detection runbooks: `detection-as-code-agent-rules`, `detection-rule-tuning`,
`detection-coverage-evaluation`, `detection-rule-validation`. `rubric_type: DETECTION_ENGINEERING`.
Adapted from the source `detection_rubric.py`, re-expressed in our terms (pack `.rule.yaml` threat
rules evaluated by the `ThreatRuleEngine` over the built graph/events, weakness-registry/ATT&CK
coverage, `audit_id` citation).

Scored by `security-judge` over the run output (the authored/tuned rule + validation evidence) + the
engagement trace. **Pass ≥ 80**; a case may raise `min_passing_score`.

| # | Category | Pts | What earns the points |
|---|----------|-----|-----------------------|
| 1 | **Requirement Analysis** | 20 | The run named the detection target and scope — the `rule_id`/name, the agent weakness/TTP it must catch, and the gap it closes (traced to the weakness registry / a hunt finding) (20; partial scope = 10). |
| 2 | **Technical Implementation** | 30 | **Syntax (15):** the `.rule.yaml` compiles/loads cleanly in the `ThreatRuleEngine` — schema-valid, `rules.fetch`-compatible (15; unverified = 5). **Logic (15):** the rule's detection logic aligns with the agent behavior/attack path it targets — the right nodes/edges/events over the built graph (15; partial = 8). |
| 3 | **Validation & Testing** | 20 | The rule was evaluated against evidence — recorded events / historical graph / a canary-backed replay — and FP/FN (false-fire) rates computed (20; limited empirical testing = 10). |
| 4 | **Process Compliance** | 15 | An explicit, human-gated ship/tune decision recorded as a `decision` event — deploy / tune / reject — with its rationale and `audit_id` (15; missing explicit decision = 8). |
| 5 | **Operational Artifacts** | 15 | **Mermaid diagram (5):** the detection-engineering flow diagram (5/0). **Execution metadata (5):** run duration + metered `audit_id`s recorded (5/0). **Summary (5):** a concise validation/deployment summary (5/0). |

**Evidence check:** a "passed validation" claim must cite the replay/telemetry it was tested against. An
unverified syntax or logic claim scores at the partial tier for Technical Implementation.

**Scorecard fields:** `profile_name: DETECTION_ENGINEERING_RUBRIC`, `category_scores{…}`,
`feedback[…]`, `metadata{decision}`.
