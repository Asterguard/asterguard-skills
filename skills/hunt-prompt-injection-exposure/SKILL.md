---
name: hunt-prompt-injection-exposure
description: Use when hunting untrusted-input → privileged-action paths across the security graph — places where untrusted content (a document, tool result, web page, email, RAG chunk) can reach the model's context and from there drive a privileged tool call or egress — ranking each exposed path by what the injection could reach and feeding confirmed exposure to remediation and detection-as-code.
---

# Hunt: Prompt-Injection Exposure

Hunt the graph for **reachable injection paths**: an untrusted-input source (document ingest, tool
result, web fetch, email, RAG chunk) that flows into the model's context and from there can reach a
**privileged action** (a state-changing tool, a secret, an egress endpoint). This is the latent
precondition for every prompt-injection incident — the `hunt-prompt-injection-exposure` finds the path
before an attacker walks it, where the IRP (`irp-prompt-injection`) responds after. Rank each path by
what the injection could reach; a planted canary confirms the live ones.

## When to Activate

- Proactive review of an agent's injection surface (new untrusted source added, new privileged tool
  granted, RAG corpus change).
- A hypothesis that untrusted content can steer the agent into a privileged action.

## Objective

Find and rank untrusted-input → privileged-action paths across `${TARGET}` under `${HYPOTHESIS}`,
confirm the live ones, and route exposed paths to trust-boundary remediation.

## Scope

Covers: reachable paths from an untrusted-input source to a privileged tool / secret / egress across
the graph, confirmed with canaries. Excludes: responding to an active injection (`irp-prompt-injection`),
exfil-only paths with no injection source (`hunt-exfil-paths`), pre-release red-team authoring
(`behavioral-redteam`).

## Inputs

- `${HYPOTHESIS}`: string — the exposure hypothesis (e.g. "a poisoned RAG chunk can reach the deploy
  tool"). *Source:* analyst / review.
- `${TARGET}`: engagement target. *Source:* engagement.
- `${SCOPE_FILTER}` (optional): limit to a source family / tool / boundary.
- `${CONFIRM_WITH_CANARY}` (optional, default off): on an authorized engagement, plant a canary to
  prove a path is live.

## Outputs

- `${HUNT_FINDINGS}`: per path `{source (untrusted input), hops, privileged_sink (tool/secret/egress),
  reachable: yes|guarded, canary_result?, blast_radius, verdict}`, ranked.
- `${REMEDIATION_LEADS}`: trust-boundary / input-provenance / tool-gating proposals → `remediation`.
- `${DETECTION_GAPS}`: "untrusted input reached a privileged sink" rules → `detection-as-code-agent-rules`.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with per-lane notes.

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `graph.enrich` /
  `knowledge.graph` (information-flow edges from untrusted sources to privileged sinks),
  `knowledge.query` (known injection patterns), `canary.mint`/`canary.plant`/`canary.scan`/`canary.verify`
  (prove a live path — authorized only), runtime `security.*` (recorded injection-shaped events),
  `risk.score`, `controls.map`.
- **Client-side:** build the untrusted-input → privileged-sink reachability over the information-flow
  graph; identify trust-boundary gaps; rank; shape remediation.
- **Sibling skills:** `engagement`, `information-flow` (flow graph), `enrich-indicator`,
  `canary-testing`, `confirm-action`, `remediation`, `record-in-engagement`,
  `detection-as-code-agent-rules`; atoms `atom-enrich-component`, `atom-query-pattern`,
  `atom-scan-canary`, `atom-map-controls`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET})` → context. Connected: ensure the ARS token. For
   canary confirmation, record the engagement authorization (dual-use discipline).
2. **Inventory untrusted sources + privileged sinks.** `graph.enrich`/`information-flow` across
   `${SCOPE_FILTER}` → untrusted-input nodes (ingest, tool results, web, RAG) and privileged sinks
   (state-changing tools, secret stores, egress).
3. **Compute reachability.** Build paths from each untrusted source through the information-flow graph
   to each privileged sink; mark whether a trust boundary / input-provenance check guards the path.
   `atom-query-pattern` for known injection shapes on those hops.
4. **Confirm live paths (optional, authorized).** For unguarded high-value paths, `canary-testing` /
   `canary.plant` an injection-shaped canary at the source and `canary.scan`/`canary.verify` the sink —
   an egress/tool hit is hard proof the path is live.
5. **Rank + route.** `risk.score` each path by reachable blast radius; `enrich-indicator` the sink;
   confirmed exposure → `${REMEDIATION_LEADS}` (trust boundary, input provenance, tool gating) for
   `remediation` via `confirm-action`.
6. **Close the gap + checkpoint.** Emit `${DETECTION_GAPS}` ("untrusted input reached privileged sink")
   for `detection-as-code-agent-rules`; `record-in-engagement`; `engagement.checkpoint`.

```mermaid
graph TD
    START([${HYPOTHESIS}]) --> OPEN["engagement.open(${TARGET})"]
    OPEN --> INV["inventory: untrusted sources + privileged sinks (information-flow)"]
    INV --> REACH["compute source → sink reachability; guarded?"]
    REACH --> LIVE{"unguarded high-value path?"}
    LIVE -- "yes + authorized" --> CAN["canary-testing: plant → scan/verify"]
    CAN --> RANK["risk.score blast radius"]
    LIVE -- "guarded/low" --> RANK
    RANK --> VERDICT{"exposed?"}
    VERDICT -- "yes" --> REM["${REMEDIATION_LEADS} → remediation [confirm-action]"]
    VERDICT -- "no" --> DOC["document guarded posture"]
    REM --> GAP["${DETECTION_GAPS} → detection-as-code-agent-rules"]
    GAP --> CP["record-in-engagement + checkpoint"]
    DOC --> CP
```

## Decision Logic / Completion Criteria

- A path is **exposed** when an untrusted-input source reaches a privileged sink with no trust-boundary
  / provenance guard; **confirmed live** when a planted canary egressed or fired the sink; **guarded**
  when a boundary breaks the path.
- Canary confirmation runs on **authorized engagements only**, recorded in the engagement; remediation
  is a proposal applied via `confirm-action`.
- **Done when:** every untrusted source → privileged sink path is enumerated and marked
  guarded/exposed (live ones canary-confirmed where authorized), exposed paths routed to remediation,
  the gap handed off, and the engagement checkpointed.

## Integration

- **Composes:** `information-flow`, `enrich-indicator`, `canary-testing`, `remediation`,
  `confirm-action`, `record-in-engagement`, `detection-as-code-agent-rules`; `engagement` bookends;
  atoms `atom-enrich-component`, `atom-query-pattern`, `atom-scan-canary`, `atom-map-controls`.
- **Called by:** `threat-hunt` playbook; feeds `remediation`; pre-stage for `irp-prompt-injection`
  (which responds when such a path is walked for real); a stage of `apt-agent-threat-hunt`.
- **Offline:** reachability runs over the local information-flow graph; canary confirmation needs the
  gateway, so note live-path confirmation as **pending**; `risk.score`/`controls.map` degrade to local
  pack data. **Connected:** full flow grounding + canary proof + runtime `security.*`, metered.
