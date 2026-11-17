---
name: evals
description: Use when grading a runbook-skill run — evaluate a triage / investigation / hunt / IRP / detection / reporting run on four axes (trajectory, schema, rubric 0–100, benchmark) entirely client-side, grounded in the engagement event stream and the security-judge/judge skills, and emit a pass/fail scorecard to ./.asterguard/evals/. The evaluation substrate for the llm_judge persona and the gate that says "a runbook isn't done without an evals case".
---

# Evals (runbook-run evaluator)

Grade a **runbook-skill run** the way the red-team judge grades an attack: from evidence the run can't
fabricate — the engagement's typed **event stream** (`events.jsonl`), the artifacts it wrote under
`./.asterguard/`, and the metered `audit_id`s it recorded — not from the run's own say-so. The source
`adk_runbooks` ships a Python eval harness (`trajectory` + `schema` + `rubric` + `benchmark`
evaluators) that scores an ADK graph run; this skill ports the **method**, not the Python: *the harness
model itself evaluates a runbook run.* Everything is client-side; the gateway only serves control
mappings and grounds the odd lookup.

## When to Activate

- A runbook run finished (or a recorded `${RUN_ID}` exists) and needs grading before it is trusted,
  shipped, or regression-tracked.
- A **new or changed runbook** needs its evals dataset case authored — a runbook is not done without one
  (trajectory + schema + rubric), so regressions are caught.
- The `llm_judge` persona is asked to score a run, a dataset, or a benchmark.
- CI / continuous-testing replays a dataset of cases to catch drift in a runbook.

## Objective

Return, for one runbook run against one dataset case, a per-axis `MetricResult` plus an overall
pass/fail vs the case's `min_passing_score` — with every verdict citing the event/artifact/`audit_id`
that proves it. Aggregate a set of case results into a benchmark scorecard (Markdown + JSON).

## Scope

Covers: trajectory (route + required/prohibited steps from the event sequence), schema (required output
fields present + non-empty), rubric (0–100 via `security-judge`), benchmark (scorecard). Grades a run
that already happened. Excludes: *running* the runbook under test (the orchestrator/`playbook-runner`
does that), judging an individual attacker↔target exchange (that is `judge`/`security-judge`), and
authoring the runbook itself.

## Inputs

- `${RUN_ID}`: string — the engagement run to grade. *Source:* the `run_started`/`run_ended` events the
  runbook wrote, or the playbook run id. **Or** `${ENGAGEMENT}` + a time/route window.
- `${CASE}`: a declarative eval case (see `references/eval-dataset-schema.md`) — `test_id`,
  `skill_reference` (the runbook under test), `rubric_type`, `input`, `expected{expected_route,
  required_output_fields, required_comment_substrings}`, `min_passing_score`. *Source:* the runbook's
  `evals/` dataset. For an ad-hoc grade, derive `expected` from the runbook's **Outputs** section.
- `${DATASET}` (optional, benchmark mode): a list of `${CASE}`s to replay/aggregate.

## Outputs

- `${TRAJECTORY}`: `MetricResult{name: trajectory_and_routing, score 0–1, passed, reason, metadata}` —
  did the run follow `expected_route` and visit the required steps / avoid the prohibited ones.
- `${SCHEMA}`: `MetricResult{name: schema_and_payload_integrity, …}` — required output fields present +
  non-empty and the required comment substrings observed.
- `${RUBRIC}`: `MetricResult{name: rubric_total_score, score 0–100, …}` + the itemized
  `RubricScorecard` (category breakdown + feedback) from the matching rubric.
- `${BENCHMARK}`: the scorecard — `./.asterguard/evals/scorecard-<ts>.md` + `scorecard-<ts>.json`.
- `${RESULT}`: `EvaluationResult{test_id, skill_reference, passed, total_score, metrics{…}}` — overall
  `passed` = rubric ≥ `min_passing_score` **and** trajectory passed **and** schema passed **and** run
  status success.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with a per-axis note.

## Tools

- **Gateway (connected, metered — carry `X-ARS-Token`, record each `audit_id`):** only `controls.map`
  (via `security-judge`, to attach control clauses to a rubric break) and an optional `knowledge.query`
  to ground an interpretive rubric call. The grade needs **no** server; offline it is fully functional.
- **Client-side:** read `events.jsonl` + the `./.asterguard/` artifacts for `${RUN_ID}`; reduce the
  event sequence to the executed-route + visited-steps; check fields/substrings; apply the rubric; write
  the scorecard. The harness model is the judge.
- **Sibling skills:** `engagement` (`context()` / read the event stream + `baseline()`), `security-judge`
  (applies the 0–100 rubric scoring with control mapping + bias control), `judge` (the independent-
  evidence contract this inherits — verdict from out-of-band evidence, cite the span, canary = proof).

## How a dataset case is shaped

Adapted from the source's declarative JSON (`test_id`, `workflow_name`, `rubric_type`, `input`,
`expected{…}`, `min_passing_score`). Our version retargets `workflow_name` → `skill_reference` (the
runbook under test) and re-expresses `expected` in **engagement** terms:

```json
{
  "test_id": "EVAL-TRIAGE-PROMPT-INJECTION-001",
  "skill_reference": "skills/triage-agent-alert/SKILL.md",
  "rubric_type": "TRIAGE_IRP",
  "description": "High-risk: canary egress on an injection alert → escalate to IRP.",
  "input": {
    "indicator_value": "LLM01-prompt-injection",
    "indicator_type": "weakness_id",
    "agent_target": "svc:support-agent",
    "alert_source": "canary_egress"
  },
  "expected": {
    "expected_route": "ESCALATE_IRP",
    "required_events": ["run_started", "finding_opened", "verdict", "run_ended"],
    "prohibited_events": ["decision:containment-without-confirm-action"],
    "required_output_fields": ["disposition", "risk_read", "engagement_event_ids"],
    "required_comment_substrings": ["High", "Escalate", "audit_id"]
  },
  "min_passing_score": 85.0
}
```

`rubric_type` is one of `TRIAGE_IRP | REPORTING | THREAT_HUNTING | DETECTION_ENGINEERING` and selects
the reference rubric. See `references/eval-dataset-schema.md` for the full field list + the scorecard
schema.

## Workflow Steps & Diagram

1. **Load the run + case.** `engagement.open(target)` → read the event window for `${RUN_ID}`
   (`events.jsonl` between its `run_started` and `run_ended`) and the artifacts it referenced under
   `./.asterguard/`. Resolve `${CASE}` (or derive `expected` from the runbook's Outputs).
2. **Trajectory axis.** Reduce the event sequence to the **executed route** (the disposition/verdict
   route the run took — e.g. `ESCALATE_IRP`, `CLOSE_BENIGN`, `CONTAIN`) and the **visited steps** (which
   sub-skills ran / which typed events fired). Compare to `expected_route`, `required_events`,
   `prohibited_events`. Route mismatch or a prohibited event ⇒ score 0; a missing required step ⇒ −0.5.
   → `${TRAJECTORY}`.
3. **Schema axis.** Collect the run's output fields (from the artifacts + the typed event payloads).
   Every `required_output_fields` entry must be **present and non-empty**; every
   `required_comment_substrings` must appear in the recorded event text. Missing field or substring ⇒
   −0.5 each. → `${SCHEMA}`.
4. **Rubric axis.** Hand the run's output + trace to `security-judge` with the `rubric_type`'s reference
   rubric → an itemized 0–100 `RubricScorecard` (category scores + feedback). Judge from evidence, cite
   the event/`audit_id`; a canary-hit event is hard proof for the action-execution category. →
   `${RUBRIC}`.
5. **Overall verdict.** `passed` = rubric_total ≥ `min_passing_score` **and** trajectory passed **and**
   schema passed **and** the run's status is success. → `${RESULT}`.
6. **Benchmark + record.** Aggregate `${RESULT}` (and the rest of `${DATASET}`) into the scorecard
   (Markdown table + JSON sidecar) under `./.asterguard/evals/`; `record-in-engagement` a `verdict`
   event (the grade) + `note` (the scorecard path) and `engagement.checkpoint`.

```mermaid
sequenceDiagram
    participant J as llm_judge / CI
    participant EV as evals
    participant Eng as engagement
    participant SJ as security-judge
    participant GW as AsterVault gateway
    J->>EV: ${RUN_ID} + ${CASE}
    EV->>Eng: open(target) → events.jsonl window + artifacts
    EV->>EV: reduce events → executed route + visited steps
    EV->>EV: trajectory axis (route / required / prohibited)
    EV->>EV: schema axis (fields present+non-empty, substrings)
    EV->>SJ: rubric_type + run output/trace → score 0–100
    SJ->>GW: controls.map(break) [X-ARS-Token] (optional)
    SJ-->>EV: RubricScorecard (categories + feedback)
    EV->>EV: overall passed = rubric≥min ∧ traj ∧ schema ∧ success
    EV->>Eng: verdict + note(scorecard path) + checkpoint
    EV-->>J: ${TRAJECTORY}, ${SCHEMA}, ${RUBRIC}, ${BENCHMARK}, ${RESULT}
```

## Decision Logic / Completion Criteria

- **Evidence first (the `judge` contract):** a verdict cites the event span / `audit_id` / canary-hit
  that proves it. No evidence for a claimed action ⇒ the rubric's action-execution category does **not**
  score it, and the finding is treated as unproven — never credited from the run's self-report.
- **Hard gates stay hard:** trajectory route mismatch, any prohibited event (e.g. a containment
  `decision` with no preceding `confirm-action` gate), or a missing required output field fails the
  overall verdict regardless of the rubric total.
- **Partial lanes don't block the grade:** if the gateway (`controls.map`/`knowledge.query`) is offline,
  the rubric still scores from local evidence; set `${STATUS}` = `Partial` and note the degraded lane.
- **Done when:** all four axes have a `MetricResult`, the overall `passed` + `total_score` are set, the
  scorecard is written under `./.asterguard/evals/`, and the grade is checkpointed to the engagement.

## The dataset rule

**A new runbook isn't done without an evals case.** Every triage/investigation/hunt/IRP/detection/
reporting runbook ships at least one dataset case here — covering its expected route, its required
outputs, and its matching rubric — so a change to that runbook is caught by a regression grade. The
reporting discipline (`**Runbook Used:**` at the top of every report) is what lets this skill trace a
run's output back to the procedure it is grading.

## Integration

- **Composes:** `engagement` (event stream + context), `security-judge` (0–100 rubric scoring + control
  mapping), `judge` (the independent-evidence/cite-the-span contract), `record-in-engagement`
  (checkpoint the grade).
- **Grades:** every runbook — the triage/investigation/hunting/detection/IRP/reporting skills — and the
  `security-operations` playbooks end to end.
- **Substrate for:** the `llm_judge` persona (this is its evaluation surface) and CI/continuous-testing
  regression runs over a `${DATASET}`.
- **Offline:** fully functional — the grade reads local `events.jsonl` + artifacts; only `controls.map`
  for a rubric break and an optional interpretive `knowledge.query` need the gateway and degrade
  cleanly. **Connected:** those lanes are live and metered (each `audit_id` recorded).

## References

- [Triage & IRP rubric (100 pts)](references/triage-irp-rubric.md)
- [Reporting rubric (100 pts)](references/reporting-rubric.md)
- [Threat-hunting & deep-analysis rubric (100 pts)](references/threat-hunting-rubric.md)
- [Detection-engineering rubric (100 pts)](references/detection-rubric.md)
- [Eval dataset case + scorecard schema](references/eval-dataset-schema.md)
