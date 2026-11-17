---
name: close-finding
description: Use when resolving a finding or incident — closes it with a closure reason, a root cause, and a justification comment, routing through the human gate first and recording a finding_closed event so the disposition is explicit, attributed, and reproducible.
---

# Common Step: Close Finding

Resolve a finding or incident on the engagement with a required reason, root cause, and comment. The
reusable building block every triage/investigation/IRP runbook calls to dispose of an item. It is the
agent-security analogue of a SOC "close SOAR case/alert" step — but closure is a `finding_closed`
**event** on the engagement stream (there is no separate case object), and because closing is a
state-changing act it passes through `confirm-action` first.

## When to Activate

- A finding/incident has reached a disposition and must be closed with a documented reason + root
  cause.
- Called by `triage-agent-alert`, `triage-agent-finding`, `close-duplicate-findings-wf`,
  `investigate-agent-incident`, and every IRP's Recovery/Lessons-learned phase — anywhere the source
  would "close the case/alert".

## Objective

Record a `finding_closed` event that carries a valid closure reason, a root cause, and a justifying
comment — after a human gate — and sync the structural closure to shared memory, so the item is
resolved reproducibly and will not silently re-open or re-block later work.

## Scope

Covers: validating the closure reason/root-cause, gating the closure, writing the `finding_closed`
event, and syncing the structural record. Excludes: deciding the disposition itself (the caller's
analysis), de-duplication (use `check-duplicate-findings`), and any containment action (use
`contain-indicator`/`remediation`).

## Inputs

- `${FINDING_ID}`: string — the finding/incident to close. *Source:* engagement context / prior
  runbook output.
- `${ARTIFACT_TYPE}`: one of `finding | incident`. *Source:* caller.
- `${CLOSURE_REASON}`: one of `malicious | not_malicious | benign_true_positive | duplicate |
  waived | inconclusive | fixed`. *Source:* caller's disposition.
- `${ROOT_CAUSE}`: string — the underlying cause (e.g. `over-privileged tool grant`, `unsanitized
  untrusted input → privileged action`, `false positive: sink is guarded`). *Source:* investigation.
- `${CLOSURE_COMMENT}`: string — the justification. *Source:* caller. `${TARGET}`: the engagement.

## Outputs

- `${CLOSURE_EVENT_ID}`: string — id of the recorded `finding_closed` event.
- `${MEMORY_ID}` (optional): string — shared-memory closure record id, when captured.
- `${AUDIT_ID}` (optional): string — `audit_id` of the metered sync, when connected.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] — with a message on non-success.

## Tools

- **Gateway (connected, metered — carry `X-ARS-Token`, record the `audit_id`):** `memory.capture`
  (via `record-in-engagement`) — the structural closure for team recall.
- **Client-side:** validate `${CLOSURE_REASON}` against the enum and that `${ROOT_CAUSE}` +
  `${CLOSURE_COMMENT}` are non-empty; assemble the closure payload.
- **Sibling skills:** `confirm-action` (the human gate — closing is state-changing);
  `record-in-engagement` (writes `finding_closed` + structural sync); `engagement` (the fold moves the
  item out of `open_findings`).

## Workflow Steps & Diagram

1. **Receive** `${FINDING_ID}` + `${CLOSURE_REASON}` + `${ROOT_CAUSE}` + `${CLOSURE_COMMENT}` from the
   caller.
2. **Validate.** Reason is a known enum value; root cause + comment are present and specific. Reject a
   bare "closed" with no root cause.
3. **Gate.** `confirm-action` with the finding, the proposed closure reason, and its effect (the item
   leaves the open set; a `waived` closure means future runs won't re-block it). Abort → do not close.
4. **Record closure.** On `proceed`, `record-in-engagement` a `finding_closed` event `{finding_id,
   reason, root_cause, comment, by}` → `${CLOSURE_EVENT_ID}`; the fold removes it from `open_findings`.
5. **Sync.** The same step `memory.capture`s the structural closure (ids, reason, root cause, *why* —
   no raw code/data) → `${MEMORY_ID}`, `${AUDIT_ID}`. Degrade on failure (note in `${STATUS}`).
6. **Return** `${CLOSURE_EVENT_ID}` (+ memory/audit ids) + `${STATUS}`.

```mermaid
sequenceDiagram
    participant Caller as Calling runbook
    participant CF as close-finding
    participant CA as confirm-action
    participant RE as record-in-engagement
    participant GW as AsterVault gateway
    Caller->>CF: FINDING_ID, CLOSURE_REASON, ROOT_CAUSE, COMMENT
    Note over CF: validate reason enum + root cause + comment
    CF->>CA: gate closure (state-changing)
    CA-->>CF: DECISION
    alt proceed
        CF->>RE: record finding_closed (+ structural capture)
        RE->>GW: memory.capture [X-ARS-Token]
        GW-->>RE: MEMORY_ID, audit_id
        RE-->>CF: CLOSURE_EVENT_ID
    else abort
        Note over CF: no closure; item stays open
    end
    CF-->>Caller: CLOSURE_EVENT_ID?, STATUS
```

## Decision Logic / Completion Criteria

- IF `${CLOSURE_REASON}` is not a known enum value OR root cause/comment is missing THEN `${STATUS}` =
  `Failure` and nothing is closed.
- IF `confirm-action` returns `abort` THEN the finding stays open; record only the (abort) `decision`.
- IF reason = `waived` THEN ensure the comment states scope + by, since a waiver suppresses future
  re-blocking — it is a decision the engagement must honor and be able to revisit.
- IF the memory sync fails THEN `${STATUS}` = `Partial` (the local `finding_closed` is authoritative).
- **Done when:** the `finding_closed` event is recorded, the item has left `open_findings`, and any
  structural sync has returned or recorded a degraded note.

## Integration

- **Composes:** `confirm-action` (gate), `record-in-engagement` (event + structural sync),
  `engagement` (fold).
- **Called by:** `triage-agent-alert`, `triage-agent-finding`, `close-duplicate-findings-wf`,
  `investigate-agent-incident`, the IRPs' Recovery/Lessons-learned phases.
- **Offline:** the gate + local `finding_closed` event close the item fully; no token needed.
  **Connected:** the structural closure also syncs to shared memory (metered) for cross-engagement
  recall.
