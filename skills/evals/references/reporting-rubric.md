# Reporting Rubric (100 pts)

Applied to the reporting runbooks: `agent-alert-report`, `agent-incident-report`, `detection-report`
(and any investigation write-up via `generate-report-file`). `rubric_type: REPORTING`. Adapted from the
source `reporting_rubric.py`, re-expressed in our terms (engagement events, gateway grounding,
`audit_id` citation, canary evidence).

Scored by `security-judge` over the produced artifact (`./.asterguard/reports/*.md` or the HTML
Artifact) plus the engagement trace. **Pass ≥ 80**; a case may raise `min_passing_score`.

| # | Category | Pts | What earns the points |
|---|----------|-----|-----------------------|
| 1 | **Data Collection** | 25 | The write-up is backed by collected evidence: the indicators/entities (`weakness_id`, `component`, `identity`, `egress`, `finding_id`) **and** the telemetry (timeline, grounded enrichment, canary/egress evidence, recorded `audit_id`s) are present (25; details but thin entity attribution = 20; minimal telemetry = 10). |
| 2 | **Generation** | 30 | **Formatting (15):** a properly structured Markdown/HTML body of real substance (>50 chars; 15 / thin = 8 / missing = 0). **Required sections (15):** the standard sections present — exec summary, findings/analysis, affected entities, recommendations/actions (≥3 of them = 15; 1–2 = 10; none = 5). |
| 3 | **Quality & Clarity** | 15 | Coherent, technically accurate, professional, no error text, enough content density to be useful to the reader (15; readable with gaps = 10; low quality/empty = 5). |
| 4 | **Delivery** | 15 | The artifact was actually delivered — written to `./.asterguard/reports/` and/or appended to the engagement via `record-in-engagement`, with a resolvable path/event id (15; not delivered = 0). |
| 5 | **Operational Artifacts** | 15 | **Mermaid diagram (5):** a sequence/flow diagram of the workflow (5/0). **Execution metadata (5):** run duration + metered `audit_id`/cost telemetry recorded (5/0). **Summary (5):** a concise action/outcome summary (5/0). |

**Traceability check (required, from the reporting discipline):** the artifact must name the runbook at
the top (`**Runbook Used:** <skill name>`). One missing this is capped — it cannot be traced to the
procedure the grade is judging; dock Generation to ≤ 15.

**Scorecard fields:** `profile_name: REPORTING_RUBRIC`, `category_scores{…}`, `feedback[…]`,
`metadata{word_count}`.
