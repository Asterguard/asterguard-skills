# Eval Dataset Case + Scorecard Schema

The declarative shapes the `evals` skill consumes and produces. Adapted from the source harness's
`datasets/core_workflows.json` + `evaluators/base.py` dataclasses, retargeted from ADK graph workflows
to AsterGuard runbook skills + the engagement event stream. All plain files any harness can read; the
grade is client-side.

## 1. Dataset case (input)

A dataset is a JSON array of cases. One case grades one runbook run.

| Field | Type | Meaning |
|-------|------|---------|
| `test_id` | string | Stable id, e.g. `EVAL-TRIAGE-PROMPT-INJECTION-001`. |
| `skill_reference` | string | Path to the runbook under test, e.g. `skills/triage-agent-alert/SKILL.md`. (Replaces the source's `workflow_name`.) |
| `description` | string | One line: what this case exercises. |
| `rubric_type` | enum | `TRIAGE_IRP` \| `REPORTING` \| `THREAT_HUNTING` \| `DETECTION_ENGINEERING` — selects the reference rubric. |
| `input` | object | The run's starting inputs in our vocabulary — `indicator_value`, `indicator_type` (`weakness_id`\|`component`\|`identity`\|`egress`\|`artifact`\|`finding_id`), `agent_target`, `alert_source`, `rule_id`, … (mirror the runbook's Inputs). |
| `expected` | object | The assertions (below). |
| `min_passing_score` | number | Rubric threshold for overall pass (default 80). |

### `expected` (engagement-term assertions)

| Field | Type | Axis | Meaning |
|-------|------|------|---------|
| `expected_route` | string | trajectory | The disposition/verdict route the run should take — e.g. `ESCALATE_IRP`, `CLOSE_BENIGN`, `CONTAIN`, `DEPLOY_RULE`. Reduced from the run's `verdict`/route events. |
| `required_events` | string[] | trajectory | Typed engagement events that must appear (`run_started`, `finding_opened`, `verdict`, `decision`, `canary_hit`, `run_ended`, …) — our analogue of the source's `required_nodes`. |
| `prohibited_events` | string[] | trajectory | Events that must **not** appear — e.g. `decision:containment-without-confirm-action` (a containment with no preceding human gate). Our analogue of `prohibited_nodes`. |
| `required_output_fields` | string[] | schema | Output fields that must be present **and non-empty** in the run's artifacts/event payloads (e.g. `disposition`, `risk_read`, `engagement_event_ids`, `report_path`). |
| `required_comment_substrings` | string[] | schema | Substrings that must appear in the recorded event/report text (e.g. `High`, `Escalate`, `audit_id`). |

Scoring mirrors the source evaluators: trajectory route mismatch or a prohibited event ⇒ 0; a missing
required event ⇒ −0.5. Schema missing field ⇒ −0.5 each; missing substring ⇒ −0.5 each (`MetricResult`
`score` on a 0–1 scale, floored at 0).

## 2. MetricResult (per-axis output)

```
MetricResult{ name, score, max_score, passed, reason, metadata }
```

- `trajectory_and_routing` — `score` 0–1; metadata `{actual_route, executed_steps, expected_route}`.
- `schema_and_payload_integrity` — `score` 0–1; metadata `{present_fields, missing_fields}`.
- `rubric_total_score` — `score` 0–100; metadata = the rubric's `category_scores`.

## 3. RubricScorecard (from security-judge)

```
RubricScorecard{ profile_name, total_score, max_score=100, passed, category_scores{…}, feedback[…], metadata{…} }
```

## 4. EvaluationResult (overall)

```
EvaluationResult{ test_id, skill_reference, passed, total_score, max_score=100,
                  metrics{ trajectory_and_routing, schema_and_payload_integrity, rubric_total_score },
                  scorecard, run_id, duration_seconds, error }
```

`passed` = `rubric_total_score ≥ min_passing_score` **and** trajectory passed **and** schema passed
**and** the run's status is success.

## 5. Benchmark scorecard (output, under `./.asterguard/evals/`)

Two sidecar files per benchmark run:

- `scorecard-<ts>.json` — `{ timestamp, summary{ total, passed, failed, pass_rate, average_score,
  average_duration_seconds }, results[ EvaluationResult-view… ] }`.
- `scorecard-<ts>.md` — a summary table (`test_id | skill_reference | rubric_profile | score | traj |
  schema | status`) followed by the per-case category breakdown + rubric feedback.

The Markdown table + JSON summary mirror the source `benchmark_evaluator.py`, minus the ADK-specific
progressive-disclosure / MCP-schema release gates (replaced by our trajectory human-gate check).
