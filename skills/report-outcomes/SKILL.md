---
name: report-outcomes
description: The terminal reports-&-outcomes generator for an authorized offensive engagement. After the scan + per-test behavioral red-team complete, fold the proven runs into the deliverables — the engagement report (composing pentest-report + risk-report), an outcomes summary (per-test verdicts, ASR@budget, the proven kill-chain), the audited canary evidence, a re-runnable regression suite of the proven breaks, and an archived-review record written to team memory. Use as the final step of the security-engineer-scan / pentest playbooks, or whenever a completed engagement's run records need turning into shareable, auditable outcomes.
---

# Report & Outcomes (terminal generator)

The last step of an engagement: turn the raw per-test runs into the things people act on. Not a new
report format — it **composes** the existing reporting skills and adds the outcomes that close the
loop (a regression suite, an archived review). Every number traces to a run record; nothing is
authored by hand.

> Realized as the `outcomes` tier of [`playbooks/security-engineer-scan.yaml`](../../playbooks/security-engineer-scan.yaml)
> (and the reporting tail of `pentest.yaml`). This skill is the named, pluggable entrypoint — an org
> can swap it for its own generator without editing the playbook.

## When to Activate

- The terminal step of `security-engineer-scan` / `pentest` / `offensive-engineer`, once every
  planned behavioral test has a verdict.
- Any time a directory of engagement run records needs to become a shareable, auditable deliverable.

## Objective

Aggregate the engagement's run records into five outcomes, each grounded in a proven run and (in
connected mode) an `audit_id` — so the deliverable is reproducible and attributable.

## Inputs

- `${RUNS_DIR}` — the engagement's run records (default `./.asterguard/runs/*.json`), each carrying
  `verdict`, `asr`, `canary`, `evidence.verify` + `audit_id(s)`, `weakness`, `ars`, and the transcript.
- `${GRAPH}` — `./.asterguard/graph.json` (security graph: components + weaknesses).
- `${REMEDIATIONS}` — `./.asterguard/remediation.json` (the gateway-backed policy bundle).
- `${ENGAGEMENT}` — scope/authorization + attacker model (engagement context).

## Outputs (the five emits)

| Emit | What it is | Source |
|---|---|---|
| **report** | the engagement report, HTML + MD | **composes** `pentest-report` (kill-chain, PoC) + `risk-report` (graph, facets, ARS) |
| **outcomes_summary** | per-test verdicts, `ASR@budget`, severity rollup, the proven kill-chain order | the run records |
| **canary_evidence** | each audited `canary.verify` hit — type, planted location, episode, `audit_id` | `evidence.verify` + `audit_id` |
| **regression_suite** | the proven breaks as re-runnable test specs → expected **HELD** after remediation | each `broke` run's turns + canary type |
| **archived_review** | the decision + report record, written to team memory / the Artifacts panel | `memory-capture` (store / Postgres) |

## Pipeline

1. **Aggregate.** `scripts/aggregate_outcomes.py ${RUNS_DIR}` reads every run record and emits
   `outcomes.json`, `canary-evidence.json`, and `regression-suite.json` (schema in
   [`references/outcomes-schema.md`](references/outcomes-schema.md)). Verdicts come only from the
   canary — a run is a finding iff its `verify.fired` is true.
2. **Report.** Call `risk-report` (graph + facets + ARS) and `pentest-report` (kill-chain + PoC per
   finding); this skill supplies the aggregated `outcomes_summary` + `canary_evidence` so the two
   renderers agree on the same numbers. One HTML Artifact + the MD.
3. **Regression hand-off.** Write `regression-suite.json` — each proven break as a test spec the
   `behavioral-redteam` harness can replay against the remediated target; the post-remediation re-run
   must flip every one to **HELD**.
4. **Archive.** `memory-capture` writes the `archived_review` (verdicts, ASR, report pointer, the
   *why*) to team memory (Postgres when wired) so the next engagement on this app starts informed;
   the live-harness Artifacts panel reads it under **Archived reviews**.

## Honest-labeling rules

- **Connected vs offline.** Carry the `audit_id` of each `canary.verify` when connected; when the
  runs were offline (in-process verifier), label them offline and do not imply gateway proof.
- **No invented numbers.** ARS comes from `risk.score`; severities from the finding; CVE counts from
  the SCA. An outcome with no backing run is omitted, not estimated.
- **Held ≠ safe.** A HELD verdict means the canary did not leave on this budget/attacker — report it
  as such, with the attacker model and `ASR@budget`, never as a guarantee.

## Integration

- **Composes:** `pentest-report` (engagement report) · `risk-report` (graph/facets/ARS render)
- **Consumes:** `behavioral-redteam` / `exploit-chain` run records · `canary-testing` evidence ·
  `remediation` policy bundle · the security graph
- **Writes:** `memory-capture` → team memory (the archived review)
- **Gateway:** `risk.score` (ARS), and the `audit_id`s already on the run records
- **Live:** the [`tools/live-harness`](../../tools/live-harness/README.md) Artifacts panel renders the
  same outcomes (Findings / Security graph / Archived reviews) live

## References

- [Outcomes schema (SSOT)](references/outcomes-schema.md)
- [Security-engineer scan runbook](../../playbooks/security-engineer-scan.md)
