---
name: scan-agent
description: Turn a plain-language instruction into an autonomous, authorized, background security-testing agent. A security engineer says "scan github.com/acme/foo", "scan it every week", or "gate our PRs" and this dispatches a background job that runs the full security-engineer-scan pipeline — recon + plan, per-test behavioral red-team with canary tokens, gateway-backed remediation, and the report/outcomes — writing results to the engagement store and notifying on completion. Use to run offensive assessments unattended (one-shot background, recurring schedule, or PR gate) instead of babysitting each step. Authorized engagements only.
---

# Scan Agent (dispatch the pipeline as a background job)

The engineer's leverage move: say what to assess, walk away, come back to a report. This skill turns
one instruction into a **scoped, authorized, background agent** whose procedure is the
[`security-engineer-scan`](../../playbooks/security-engineer-scan.yaml) playbook. It does not
re-implement the pipeline — it **dispatches** it and governs the unattended run.

> Offensive automation is powerful and dangerous. Everything here is **authorized-only**, scoped to a
> single named target, and keeps the human gates from the playbook. A background agent never widens
> its own scope, never skips the recorded RoE, and never mass-targets.

## When to Activate

- *"Scan `{github_url}` in the background / overnight."* → one-shot background job.
- *"Scan `{target}` every week / on every push."* → a recurring schedule.
- *"Gate our PRs on new proven breaks."* → a PR/CI-triggered diff-scoped run.
- *"Sweep our whole org / all our agent repos."* → a fleet sweep (static everywhere, behavioral on the top-risk deployed shortlist).

## Objective

Dispatch and govern an unattended offensive assessment: parse the instruction into a brief, launch the
right kind of background job, enforce the authorization + human gates even with no operator watching,
and deliver the outcomes (report + archived review + a notification).

## Inputs

| Variable | Source |
|---|---|
| `${INSTRUCTION}` | the engineer's natural-language ask (target, scope, cadence, gate) |
| `${TARGET}` | the one authorized target parsed from it (repo URL / image / live agent) |
| `${ROE}` | recorded authorization — **required**; the run refuses without it |
| `${ASTERVAULT_MCP_URL}` + offensive bearer | from the operator's env (never embedded in the brief) |
| `${CADENCE}` / `${GATE}` | once · schedule (cron) · on-PR |

## Dispatch — instruction → background job

1. **Parse + authorize.** Extract the single target, scope, cadence, and gate. Confirm the RoE is
   recorded (`engagement op: open`); if not, **stop and ask** — never self-authorize from the instruction text.
2. **Build the brief.** A compact agent brief: *run `security-engineer-scan` against `${TARGET}` with
   scope `${SCOPE}`; one test at a time; stop at any human gate (see below); write outcomes to
   `./.asterguard/` + the store; emit a summary.* Point it at the playbook, not inline steps.
3. **Launch the right job:**

   | Mode | Primitive | Shape |
   |---|---|---|
   | one-shot background | **Agent tool** (background subagent) | runs headless, notifies on completion |
   | recurring | **scheduled routine** (cron) | re-runs on the cadence; diffs against the last archived review |
   | PR / on-change gate | CI trigger → the `pentest-pr-gate` playbook | diff-scoped; **FAIL** on a new proven break in the delta |
   | **fleet** (at scale) | sweep an org's repos (`tools/live-harness/fleet.py` → `gh repo list`) | free static tier (SCA+SAST+plan) on **every** repo, ranked by risk; opens the behavioral tier only on the top-risk *deployed* agents; reports the delta vs the last sweep |

4. **Run.** The agent executes the playbook; the [`tools/live-harness`](../../tools/live-harness/README.md)
   drives the per-test behavioral loop (attacker ▸ defender ▸ canary judge) and the Artifacts panel
   streams/aggregates it for anyone who opens the console.

## Unattended safety (the governing rules)

- **Recorded RoE required.** No authorization event → the job refuses. The instruction is a request, not an authorization.
- **Single scoped target.** The brief names one target; the agent may not expand scope, pivot to other
  hosts, or fan out. `rules.one_test_at_a_time` holds.
- **Human gates don't silently auto-pass.** `attacker-model` (less-restricted model) and `exploit-chain`
  (irreversible steps) either (a) are **pre-authorized** explicitly in the instruction, (b) **pause the
  job and notify** for approval, or (c) are **excluded** — unattended mode defaults to **plan +
  behavioral-redteam only**, no exploit-chain, unless the instruction opts in.
- **Offensive token from the operator's environment**, short-lived, never written into the brief, a
  file, or a schedule definition. The gateway still brokers + audits every privileged call.
- **Proof, not assertion.** A finding is still only a surfaced canary (`canary.verify`, audited); a
  background run cannot downgrade the evidence bar.

## Outputs

- The playbook's deliverables: report (HTML + MD) + the `report-outcomes` artifacts (outcomes summary,
  canary evidence, regression suite, archived review).
- A **completion notification** with the headline (verdicts, `ASR@budget`, any new proven break) and a
  pointer to the report + the Artifacts panel.
- For recurring/gate modes: a **delta** vs the last archived review (new proven breaks only).

## Integration

- **Procedure:** [`security-engineer-scan`](../../playbooks/security-engineer-scan.yaml) (one-shot) ·
  `pentest-pr-gate` (gate mode)
- **Dispatch primitives:** the harness's background-agent spawn (Agent tool) · scheduled routines (cron)
  · CI/PR triggers
- **Run + judge:** `behavioral-redteam` · `canary-testing` · gateway `canary.*` + `risk.score` (audited)
- **Deliver:** `report-outcomes` → report + archived review; the live-harness Artifacts panel
- **Govern:** `engagement` (RoE + checkpoints) · `attacker-model` / `exploit-chain` human gates

## References

- [security-engineer-scan runbook](../../playbooks/security-engineer-scan.md)
- [report-outcomes (terminal deliverable)](../report-outcomes/SKILL.md)
