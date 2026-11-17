---
name: detection-report
description: Use when documenting detection-engineering work for agent threat rules — coverage against the weakness registry / ATT&CK, new or changed .rule.yaml rules, and tuning outcomes (FP/FN, rule performance) — into one standardized report. Writes a Markdown report to ./.asterguard/reports/ via generate-report-file (or hands off to risk-report for HTML), naming the runbook used at the top.
---

# Detection Report

Summarize detection-engineering work on agent threat rules: coverage against the weakness registry and
ATT&CK, the `.rule.yaml` rules authored or changed, and their tuning outcomes (false-positive / false-
negative movement, volume, performance). The reporting deliverable for `detection-as-code-agent-rules`,
`detection-rule-tuning`, `detection-coverage-evaluation`, and `detection-rule-validation` — it reports on
existing rule state and recent detection work; it does not author or tune rules itself. Names the runbook
used at the top so output traces to procedure.

## When to Activate

- A detection runbook (`detection-as-code-agent-rules`, `detection-rule-tuning`,
  `detection-coverage-evaluation`, `detection-rule-validation`) finishes and a written record is needed.
- A periodic detection-coverage / rule-performance review, or a PIR needs the detection-gap closure
  documented.

## Objective

Emit one structured detection-engineering report — rule details, coverage, performance/tuning outcomes,
and recommendations — sourced from the rule pack + the engagement, written to `./.asterguard/reports/`.

## Scope

Covers: gathering rule definitions + coverage + performance/tuning data, synthesizing the report, and
writing it. Excludes: authoring or implementing rule changes (`detection-as-code-agent-rules`,
`detection-rule-tuning`) and validating a rule fires (`detection-rule-validation`) — their outputs are
inputs here.

## Inputs

- `${RULE_IDS}`: the detection rule(s) to report on (one or more `.rule.yaml` ids). *Source:* the
  detection runbook / rule pack. Mandatory.
- `${RUNBOOK_USED}`: the detection runbook this report documents (e.g. `detection-rule-tuning`).
  *Source:* the engagement event stream.
- `${TIMEFRAME_DAYS}` (optional): window for performance data (default 90).
- `${INCIDENT_ID}` (optional): the incident whose detection gap these rules close. *Source:* a PIR.

## Outputs

- `${REPORT_FILE_PATH}`: the path of the written report under `./.asterguard/reports/`.
- `${REPORT_CONTENT}`: the Markdown content (with the `**Runbook Used:**` header).
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with a message on non-success.

## Tools

- **Gateway (connected, metered — carry `X-ARS-Token`, record each `audit_id`):** `rules.fetch` (rule
  definitions/logic from the pack), `knowledge.query` (the weakness registry / ATT&CK coverage reference);
  performance data comes from the engagement's recorded rule-firing events.
- **Client-side:** read rule logic + firing history + tuning outcomes; compute coverage vs the weakness
  registry / ATT&CK; synthesize the report; build the mermaid diagram of the data-gathering path.
- **Sibling skills:** `engagement` (`context()` for rule-firing history + the detection work events),
  `atom-fetch-rules` (`rules.fetch`), `generate-report-file` (writes the artifact), `record-in-engagement`,
  `risk-report` (optional HTML/coverage view hand-off).

## Workflow Steps & Diagram

1. **Open + gather.** `engagement.open` (the target/program); `atom-fetch-rules` (`rules.fetch`) for each
   `${RULE_ID}` → logic/definition; read `context()` for each rule's firing history + recent tuning
   outcomes; `knowledge.query` the weakness-registry / ATT&CK reference for coverage. Connected: ensure
   the ARS token via `ars-token`.
2. **Analyze.** Compute coverage (which weaknesses / TTPs are now covered vs gaps), performance (volume,
   severity, FP/FN movement from tuning), and — if `${INCIDENT_ID}` — confirm the rule closes that
   incident's detection gap.
3. **Synthesize.** Compose the report: **Metadata** (`**Runbook Used:** ${RUNBOOK_USED}`, timestamp,
   `${RULE_IDS}`), **Rule Details** (id, name, logic summary), **Coverage** (vs weakness registry /
   ATT&CK), **Performance / Tuning Outcomes** (volume, FP/FN, before→after), **Findings & Recommendations**
   (further tuning, remaining gaps), and a **Workflow Diagram** (mermaid) of the data-gathering path.
4. **Write.** `generate-report-file` with the Markdown → `${REPORT_FILE_PATH}`. (Optional: hand the
   coverage data to `risk-report` for a shareable HTML coverage view.)
5. **Record + checkpoint.** `record-in-engagement` a `note` that the report was produced (with its path);
   `engagement.checkpoint`.

```mermaid
sequenceDiagram
    participant Engineer
    participant RB as detection-report
    participant Eng as engagement
    participant GW as AsterVault gateway
    participant GRF as generate-report-file
    Engineer->>RB: start with ${RULE_IDS}, ${RUNBOOK_USED}
    RB->>Eng: open(target) → context (rule-firing history + tuning events)
    RB->>GW: rules.fetch(RULE_IDS) + knowledge.query(coverage ref) [X-ARS-Token] → defs, audit_id
    Note over RB: compute coverage + performance; synthesize (Runbook Used header + sections + mermaid)
    RB->>GRF: write to ./.asterguard/reports/
    GRF-->>RB: REPORT_FILE_PATH
    RB->>Eng: record-in-engagement(note) + checkpoint
    RB-->>Engineer: REPORT_FILE_PATH, REPORT_CONTENT, STATUS
```

## Decision Logic / Completion Criteria

- The report **must** carry `**Runbook Used:** ${RUNBOOK_USED}` at the top (reporting requirement).
- IF `${INCIDENT_ID}` is given THEN the report must state whether the rule(s) close that incident's
  detection gap (the loop a PIR opened).
- **Done when:** the report has all sections including the runbook header + mermaid diagram, coverage and
  performance are reported from the rule pack + engagement, it is written to `./.asterguard/reports/`, and
  its generation is noted in the engagement.

## Integration

- **Composes:** `engagement` + `record-in-engagement` bookends, `atom-fetch-rules`, `generate-report-file`;
  optionally `risk-report`.
- **Called by:** `detection-as-code-agent-rules`, `detection-rule-tuning`, `detection-coverage-evaluation`,
  `detection-rule-validation`, `post-incident-review`; the `threat-hunt` playbook.
- **Offline:** rule definitions load from the local pack and firing history from the local engagement; the
  report writes to `./.asterguard/reports/` with no network, noting any coverage reference as degraded.
  **Connected:** full `rules.fetch` + `knowledge.query` coverage grounding, metered.
