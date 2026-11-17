---
name: confirm-action
description: Use as the human-in-the-loop gate before ANY state-changing or containment action — block egress, revoke a token, isolate a runtime, apply a policy, close a finding — presents the action and its blast radius to a human operator, waits for an explicit decision, and records it as a decision event. No containment proceeds without it.
---

# Common Step: Confirm Action

Put a human in the loop before any action that changes state or contains an agent. The reusable gate
every containment/remediation/closure step routes through first. It is the agent-security analogue of
a SOC "confirm action with user" step — hardened for **dual-use discipline**: the same capability that
contains a real compromise can disrupt a healthy production agent, so the gate is mandatory, explicit,
and recorded, never implied by an earlier approval.

## When to Activate

- Immediately before any **state-changing or containment** action: block egress, revoke/rotate an
  agent token, isolate a runtime/host, apply or tighten a policy (egress allowlist, SPIFFE/IAM,
  OPA/Cedar/PDP), or close a finding/incident.
- Called by `contain-indicator`, `endpoint-agent-triage-isolation`, `remediation`, `close-finding`, and
  every IRP's Containment/Eradication phase — anywhere the source would "confirm before a disruptive
  action".

## Objective

Obtain and record an explicit human decision (proceed / modify / abort) for one proposed action,
having first surfaced exactly what it will do and what it may disrupt — so a reversible, auditable
`decision` event precedes the action, and nothing destructive runs on inference.

## Scope

Covers: presenting the proposed action + blast radius, asking the operator, capturing the response,
and recording the `decision` event. Excludes: *executing* the action (the caller does that only on a
proceed), choosing the action, and the enforcement mechanics (that is `remediation`/`policy.apply`).

## Inputs

- `${ACTION_DESCRIPTION}`: string — the exact action, in plain terms (e.g. "Block egress to
  `paste.ee` for `svc:billing-agent`", "Revoke token `tok_…`", "Isolate runtime `pod/agent-7`").
  *Source:* the calling containment/remediation runbook.
- `${BLAST_RADIUS}`: string — what else this affects (which agents/tools/flows degrade), whether it is
  reversible, and how to roll back. *Source:* caller's `graph.enrich`/policy preview.
- `${EVIDENCE_REF}`: string — the finding/correlation/canary evidence justifying the action.
  *Source:* `./.asterguard/` artifact path (reference by path, not inlined).
- `${RESPONSE_OPTIONS}` (optional): list — e.g. `["Proceed", "Proceed with modification", "Abort"]`
  (default). `${TARGET}`: the engagement to record the decision in.

## Outputs

- `${USER_RESPONSE}`: string — the operator's explicit choice.
- `${DECISION}`: one of `proceed | modify | abort` — normalized.
- `${DECISION_EVENT_ID}`: string — the recorded `decision` event id.
- `${STATUS}`: ["Success" | "Failure"] — `Failure` if no clear decision was obtained.

## Tools

- **Gateway (connected, metered):** none directly — the gate is client-side. The `decision` record
  syncs via `record-in-engagement` (carries `X-ARS-Token`, returns `audit_id`).
- **Client-side:** present `${ACTION_DESCRIPTION}` + `${BLAST_RADIUS}` + `${EVIDENCE_REF}` to the
  operator, ask the follow-up question, and wait for an explicit answer — no default, no timeout
  auto-proceed.
- **Sibling skills:** `record-in-engagement` (writes the `decision` event); the caller
  (`remediation`/`close-finding`) executes only on `proceed`.

## Workflow Steps & Diagram

1. **Receive** `${ACTION_DESCRIPTION}`, `${BLAST_RADIUS}`, `${EVIDENCE_REF}` from the caller.
2. **Present.** Show the operator the action, its blast radius + reversibility/rollback, and the
   evidence reference — stated as the action's effect, plainly, with no assumption of a yes.
3. **Ask + wait.** Pose the follow-up question with `${RESPONSE_OPTIONS}`; block on an explicit human
   answer. Silence/ambiguity is **not** consent — treat as abort.
4. **Normalize.** Map `${USER_RESPONSE}` to `${DECISION}` (`proceed | modify | abort`); on `modify`,
   carry the operator's constraint back to the caller.
5. **Record.** `record-in-engagement` a `decision` event `{action, decision, by, evidence_ref,
   blast_radius}` → `${DECISION_EVENT_ID}` (+ `audit_id` connected).
6. **Return** `${DECISION}` to the caller — which executes the action **only** on `proceed`/`modify`.

```mermaid
sequenceDiagram
    participant Caller as Calling runbook
    participant CA as confirm-action
    participant Operator
    participant RE as record-in-engagement
    Caller->>CA: ACTION_DESCRIPTION, BLAST_RADIUS, EVIDENCE_REF
    CA->>Operator: present action + blast radius + evidence; ask (options)
    Operator-->>CA: explicit response
    Note over CA: normalize → proceed | modify | abort (silence = abort)
    CA->>RE: record decision event
    RE-->>CA: DECISION_EVENT_ID, audit_id
    CA-->>Caller: DECISION (caller executes only on proceed/modify)
```

## Decision Logic / Completion Criteria

- IF `${DECISION}` = `abort` OR no explicit answer was given THEN the caller performs **no** action and
  the `decision` (abort) is still recorded.
- IF `${DECISION}` = `modify` THEN the caller re-scopes the action to the operator's constraint and
  (for a materially different action) re-gates through this skill.
- A prior approval never carries to a new action — each state-changing action gets its own gate.
- **Done when:** an explicit `${DECISION}` is recorded as a `decision` event and returned.

## Integration

- **Composes:** `record-in-engagement` (the mandatory `decision` event).
- **Called by:** `contain-indicator`, `endpoint-agent-triage-isolation`, `remediation`,
  `close-finding`, and every IRP's Containment/Eradication/Recovery phases.
- **Offline:** the gate + the local `decision` event work fully; no token needed. **Connected:** the
  `decision` event also syncs to shared memory (metered) so the authorization is team-visible.
