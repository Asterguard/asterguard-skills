---
name: suspicious-tool-call-triage
description: Use when an agent makes an anomalous or unexpected tool invocation — an unexpected tool, an out-of-scope parameter, an unusual egress destination, or abnormal call volume — and you need to gather identity + authority context, enrich the destination, review recent tool-call history, and route close-as-benign or escalate, without deep investigation or containment.
---

# Runbook: Suspicious Tool-Call Triage

Initial triage of an **anomalous agent tool invocation** — the agent-security analogue of a suspicious
login. The "login" is a tool call that deviates from the agent's expected behavior: an unexpected tool,
an out-of-scope scope/parameter, an unusual egress destination, or abnormal call volume. Gather the
identity's granted authority, enrich the destination, review recent call history, and recommend a route.
Triage only: it decides benign-vs-escalate; it does not contain or revoke.

## When to Activate

- A runtime signal (or user report) flags an agent tool call as anomalous: unexpected tool, scope,
  destination, or volume (impossible-cadence, burst, or first-ever-seen call).
- `triage-agent-alert` routed a tool-call anomaly here for the authority-focused view.

## Objective

Determine whether an anomalous tool call is expected/authorized activity or a sign of compromise
(injection-driven action, stolen token, over-privilege abuse), and route **close-as-benign** or
**escalate** with a recommendation — grounded in the identity's authority, destination reputation, and
recent call patterns.

## Scope

Covers: extract the call's identity/tool/destination, enrich the identity's authority and the egress,
review recent tool-call history, relate to open findings, assess, and recommend a route.
Excludes: containment/token revocation/egress blocking (human-gated via the IRPs + `confirm-action`),
and deep timeline reconstruction (`agent-timeline-analysis`).

## Inputs

- `${ALERT_ID}`: string — the anomalous-tool-call alert/finding id. *Source:* runtime `security.*` /
  engagement event.
- `${AGENT_IDENTITY}`: string — the agent/service principal that made the call (e.g.
  `svc:billing-agent`). *Source:* the recorded tool-call event. Typed `identity` for `enrich-indicator`.
- `${TOOL_CALL}`: object — tool name, parameters/scope, destination, timestamp. *Source:* recorded
  event.
- `${EGRESS}` (derived, optional): string — the destination endpoint/host the call reached. Typed
  `egress` for `enrich-indicator`.
- `${ANOMALY_TYPE}` (derived): one of `unexpected-tool | out-of-scope | unusual-egress | volume`.

## Outputs

- `${ASSESSMENT}`: ["Benign/Expected" | "Suspicious" | "Duplicate"] — verdict + rationale.
- `${ACTION_TAKEN}` / route: ["Closed-Benign" | "Closed-Duplicate" | "Escalated → <IRP>"] — with the
  recommendation (e.g. "revoke token", "block egress") left for the human-gated IRP.
- `${IDENTITY_AUTHORITY}`: the identity's granted tools/scopes/authority (from `atom-lookup-identity`).
- `${EGRESS_READ}`: destination reputation/context (from `enrich-indicator` on the egress).
- `${CALL_HISTORY}`: recent tool-call pattern for this identity (the targeted recorded-events search).
- `${RELATED_FINDINGS}`: open findings sharing this identity/egress.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] — with a per-lane note on non-success.

## Tools

- **Gateway (connected, metered — carry `X-ARS-Token`, record each `audit_id`):** `graph.enrich`
  (identity authority), `knowledge.query` (known tool-abuse patterns), `memory.recall`, `risk.score`
  (via the composed skills), runtime `security.*` recorded tool-call search.
- **Client-side:** classify `${ANOMALY_TYPE}`; compare the call against the identity's authority
  envelope; read the cadence/volume pattern; form the recommendation.
- **Sibling skills:** `engagement` (open/context/checkpoint) · `atom-lookup-identity` ·
  `enrich-indicator` · `find-related-findings` · `check-duplicate-findings` · `record-in-engagement` ·
  `close-finding`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${AGENT_IDENTITY} / deployment)` → context + history.
   Connected: ensure the ARS token via `ars-token`.
2. **Extract + classify.** From `${TOOL_CALL}` derive `${ANOMALY_TYPE}` and the typed indicators
   (`identity`, `egress`).
3. **Dedupe.** `check-duplicate-findings` → if this anomaly is already an open finding, `close-finding`
   (reason=`duplicate`), route **Closed-Duplicate**. Stop.
4. **Identity authority.** `atom-lookup-identity(${AGENT_IDENTITY})` → `${IDENTITY_AUTHORITY}`: was the
   tool/scope actually granted? An ungranted tool or out-of-scope parameter is a strong suspicious
   signal.
5. **Enrich the destination.** `enrich-indicator` on `${EGRESS}` (type `egress`) → `${EGRESS_READ}`
   (reputation, prior sightings, first-pass risk). Surface any prior waiver.
6. **Recent call history.** One targeted runtime `security.*` search for this identity's recent
   tool-calls around the alert time → `${CALL_HISTORY}` (first-ever tool? cadence spike? paired with an
   untrusted-input turn?). Connected: carries `X-ARS-Token`, returns `audit_id`.
7. **Relate.** `find-related-findings` on identity + egress (status=open) → `${RELATED_FINDINGS}`.
8. **Assess + route.** Weigh authority breach + destination reputation + call pattern → `${ASSESSMENT}`.
   Benign → `close-finding`. Suspicious → escalate to the matching IRP with the recommendation.
   `record-in-engagement` the `verdict` + `decision` events (with `audit_id`s); `engagement.checkpoint`.

```mermaid
sequenceDiagram
    participant Analyst
    participant RB as suspicious-tool-call-triage
    participant Eng as engagement
    participant ID as atom-lookup-identity
    participant EN as enrich-indicator
    participant GW as AsterVault gateway
    Analyst->>RB: ${ALERT_ID}, ${AGENT_IDENTITY}, ${TOOL_CALL}
    RB->>Eng: open(identity/deployment) → context
    Note over RB: classify ANOMALY_TYPE; dedupe (close if duplicate)
    RB->>ID: lookup_identity [X-ARS-Token] → ${IDENTITY_AUTHORITY}, audit_id
    RB->>EN: egress destination → ${EGRESS_READ}
    RB->>GW: security.* recent tool-calls [X-ARS-Token] → ${CALL_HISTORY}, audit_id
    Note over RB: authority breach? bad destination? anomalous cadence?
    alt Benign / Expected
        RB->>Eng: close-finding (benign) + checkpoint
        RB-->>Analyst: Closed-Benign
    else Suspicious
        RB->>Eng: record verdict + decision (recommendation) + checkpoint
        RB-->>Analyst: Escalated → IRP (tool-abuse / credential-compromise / injection)
    end
```

## Decision Logic / Completion Criteria

- IF `${DUPLICATE_OF}` confirmed THEN **Closed-Duplicate** → `close-finding`.
- IF the tool/scope is within `${IDENTITY_AUTHORITY}`, the destination is reputable/allow-listed, and the
  cadence matches history (or a prior waiver covers it) THEN **Closed-Benign**.
- IF the call uses an ungranted tool/scope, reaches a suspicious or non-allow-listed egress, or the
  pattern traces to an untrusted-input turn THEN **Suspicious → Escalated**: route to `irp-tool-abuse-rce`
  (tool abuse / code-exec), `irp-agent-credential-compromise` (stolen token), or `irp-prompt-injection`
  (injection-driven). The revoke/block recommendation is handed to that IRP for human-gated action.
- **Done when:** the call is classified, authority + destination + history are gathered, an assessment is
  set, the route is taken, and events are recorded + checkpointed.

## Integration

- **Composes:** `atom-lookup-identity`, `enrich-indicator`, `find-related-findings`,
  `check-duplicate-findings`, `close-finding`; `engagement` + `record-in-engagement` bookends.
- **Escalated from:** `triage-agent-alert`. **Escalates to:** `irp-tool-abuse-rce`,
  `irp-agent-credential-compromise`, `irp-prompt-injection`.
- **Offline:** identity/graph/egress grounding degrade to the local graph + recorded events in
  `./.asterguard/`; recommendation still produced (noted `Partial`). **Connected:** full `graph.enrich` +
  runtime tool-call search, metered, each metered call records an `audit_id`.
