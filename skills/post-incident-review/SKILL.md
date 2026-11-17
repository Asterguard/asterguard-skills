---
name: post-incident-review
description: Use when an agent incident response is complete or winding down and you need the lessons-learned pass — reconstruct what happened, grade what held and what failed, find the root cause and the gap to close, and turn each gap into a tracked recommendation (the detection gap feeds detection-as-code-agent-rules). Reads the engagement event stream; produces a PIR with SMART recommendations.
---

# Post-Incident Review (PIR)

The lessons-learned pass after an agent incident: reconstruct the timeline, grade the response phase by
phase, establish root cause, identify the prevention / detection / response gaps, and convert each gap
into a tracked, owned recommendation. The engagement event stream *is* the incident record — the PIR
folds it, it does not re-investigate. Its detection-gap output is the direct input to
`detection-as-code-agent-rules` (ship the rule so it's caught next time); its control/process gaps feed
`remediation`. This runbook orchestrates; it does not re-run the incident.

## When to Activate

- The Lessons-Learned (L) phase of any IRP (`irp-prompt-injection`, `irp-agent-credential-compromise`,
  `irp-tool-abuse-rce`, `irp-data-exfil-via-agent`, `irp-model-supply-chain`) — called at the end.
- An incident is closed or nearing closure and its outcome should improve future prevention, detection,
  and response.

## Objective

Produce a structured post-incident review for one agent incident: timeline, phase-by-phase response
assessment, root cause, gaps, and SMART recommendations — each assigned, tracked, and routed to the skill
that closes it — so the next incident of this kind is prevented or caught earlier.

## Scope

Covers: reconstructing the incident from the engagement stream, grading the response, root-cause
analysis, gap identification, and recommendation tracking. Excludes: re-running the investigation or any
containment (the IRP already did that), and the report document itself (hand off to `agent-incident-report`).

## Inputs

- `${INCIDENT_ID}`: the engagement incident/finding id being reviewed. *Source:* the completing IRP.
- `${AGENT_TARGET}`: the agent/deployment the incident was on. *Source:* engagement.
- `${RUNBOOKS_USED}`: the IRP + sub-runbooks executed. *Source:* the engagement event stream.
- `${INCIDENT_REPORT}` (optional): the incident report, if already written. *Source:* `agent-incident-report`.

## Outputs

- `${TIMELINE}`: the reconstructed incident timeline (detection → containment → recovery) with the metrics
  the stream supports (time-to-detect, time-to-contain, time-to-recover).
- `${RESPONSE_ASSESSMENT}`: what held / what failed, per PICERL phase — including whether the runbooks and
  tools were effective (runbook-feedback).
- `${ROOT_CAUSE}`: the established root cause(s) of the incident.
- `${GAPS}`: prevention / detection / response gaps, each typed and routed.
- `${RECOMMENDATIONS}`: SMART recommendations, each with an owner, a target, and a route (detection gap →
  `detection-as-code-agent-rules`; control/process gap → `remediation`; runbook gap → runbook update).
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with a message on non-success.

## Tools

- **Gateway (connected, metered — carry `X-ARS-Token`, record each `audit_id`):** `memory.recall` (prior
  incidents of this kind + their PIRs, to spot recurring gaps), `knowledge.query` (expected controls /
  patterns for the incident class), `memory.capture` (the lessons, as durable records).
- **Client-side:** fold the engagement event stream into the timeline + metrics; grade each phase; reason
  the root cause; derive and type the gaps; write the SMART recommendations.
- **Sibling skills:** `engagement` (`context()` / event stream = the incident record; `checkpoint` at the
  end), `record-in-engagement` (the PIR outcomes as typed events), `detection-as-code-agent-rules` +
  `remediation` (recommendation routing), `agent-incident-report` (the report document), `memory-capture`.

## Workflow Steps & Diagram

1. **Open + gather.** `engagement.open(${AGENT_TARGET})`; read `context()` + the event stream for
   `${INCIDENT_ID}` (findings, `decision`s, `canary_hit`s, `policy_applied`, verdicts); `memory.recall`
   prior incidents of this class. Connected: ensure the ARS token via `ars-token`.
2. **Reconstruct timeline + metrics.** Fold the stream into `${TIMELINE}`: detection → identification →
   containment → eradication → recovery, with time-to-detect / -contain / -recover where the stream
   supports them.
3. **Assess the response (per phase).** Grade each PICERL phase — what held, what failed, whether the
   runbooks guided correctly and the tools worked (runbook-feedback). → `${RESPONSE_ASSESSMENT}`.
4. **Root cause + gaps.** Establish `${ROOT_CAUSE}`; derive `${GAPS}` and type each as **prevention**,
   **detection**, or **response**; `knowledge.query` the expected controls to sharpen them.
5. **Recommendations (SMART) + route.** Write `${RECOMMENDATIONS}`, each with owner + target date, and
   route: detection gap → `detection-as-code-agent-rules`; control/process gap → `remediation`; runbook
   gap → a runbook update. Each is recorded as a `decision` event.
6. **Hand off report + checkpoint.** Hand `${ROOT_CAUSE}` / `${GAPS}` / `${RECOMMENDATIONS}` to
   `agent-incident-report` (which names this runbook at the top); `record-in-engagement` all PIR events;
   `engagement.checkpoint`; `memory.capture` the lessons (what held, the gap, the fix, and the *why*).

```mermaid
sequenceDiagram
    participant Analyst
    participant PIR as post-incident-review
    participant Eng as engagement
    participant GW as AsterVault gateway
    participant Route as detection-as-code / remediation
    Analyst->>PIR: start with ${INCIDENT_ID}
    PIR->>Eng: open(target) → context + event stream
    PIR->>GW: memory.recall(prior incidents) [X-ARS-Token] → recurring gaps, audit_id
    Note over PIR: fold stream → TIMELINE + metrics; grade phases → RESPONSE_ASSESSMENT
    PIR->>GW: knowledge.query(expected controls) → sharpen GAPS
    Note over PIR: ROOT_CAUSE + typed GAPS + SMART RECOMMENDATIONS
    PIR->>Route: route detection gap / control gap
    PIR->>Eng: append(decision events) + checkpoint
    PIR->>GW: memory.capture(lessons + why)
    PIR-->>Analyst: TIMELINE, RESPONSE_ASSESSMENT, ROOT_CAUSE, GAPS, RECOMMENDATIONS, STATUS
```

## Decision Logic / Completion Criteria

- IF a **detection gap** is found THEN route it to `detection-as-code-agent-rules` (a rule must be shipped
  to close the loop) and track the recommendation.
- IF a **control/process gap** is found THEN route it to `remediation`; IF a **runbook gap** is found THEN
  open a runbook-update recommendation.
- Each recommendation is **SMART** (specific, measurable, owned, dated) and recorded as a `decision`.
- **Done when:** the timeline + metrics are reconstructed, every phase is graded, root cause is
  established, each gap is typed and routed to an owned recommendation, the report is handed off, and the
  lessons are captured to memory.

## Integration

- **Composes:** `engagement` (event stream = incident record) + `record-in-engagement` bookends,
  `memory-capture`, `detection-as-code-agent-rules` + `remediation` (gap routing), `agent-incident-report`
  (report document).
- **Called by:** every IRP (`irp-prompt-injection`, `irp-agent-credential-compromise`, `irp-tool-abuse-rce`,
  `irp-data-exfil-via-agent`, `irp-model-supply-chain`) as its Lessons-Learned phase; the
  `incident-response` playbook.
- **Offline:** prior-incident recall + control lookup degrade to the local engagement + pack data; the
  PIR still completes from the local event stream. **Connected:** full cross-incident recall + knowledge
  grounding, metered, with lessons captured to shared memory.
