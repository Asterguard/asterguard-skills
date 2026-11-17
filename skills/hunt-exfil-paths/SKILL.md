---
name: hunt-exfil-paths
description: Use when hunting confidential-data → egress paths across the security graph — information-flow violations where sensitive data (secrets, PII, proprietary context, tool outputs) can reach an outbound channel the agent controls — ranking each path by data sensitivity and egress exposure, confirming live ones with canaries, and feeding confirmed exfil paths to remediation and detection-as-code.
---

# Hunt: Data-Exfiltration Paths

Hunt the information-flow graph for **confidential-data → egress** paths: a route by which sensitive
data (a secret, PII, proprietary context, a privileged tool's output) can reach an outbound channel
the agent can drive (an egress endpoint, a message/webhook tool, a write to an external store). These
are the information-flow violations an exfil incident walks — find them, rank by sensitivity × egress
exposure, and confirm the live ones with a planted canary before an attacker finds them.

## When to Activate

- Proactive review of an agent's data-egress surface (new egress endpoint, new tool with outbound
  reach, sensitive data added to context/RAG).
- A hypothesis that confidential data can leave via an agent-controlled channel.

## Objective

Find and rank confidential-data → egress paths across `${TARGET}` under `${HYPOTHESIS}`, confirm the
live ones, and route exposed paths to egress-allowlist / data-boundary remediation.

## Scope

Covers: information-flow paths from a confidential-data source to an agent-controlled egress sink,
confirmed with canaries. Excludes: the injection that triggers exfil (`hunt-prompt-injection-exposure`),
responding to an active exfil (`irp-data-exfil-via-agent`), credential-store theft specifically
(`hunt-agentic-ttp-credential-access`).

## Inputs

- `${HYPOTHESIS}`: string — the exfil hypothesis (e.g. "customer PII in RAG can reach the outbound
  webhook tool"). *Source:* analyst / review.
- `${TARGET}`: engagement target. *Source:* engagement.
- `${SCOPE_FILTER}` (optional): limit to a data class / egress family / boundary.
- `${CONFIRM_WITH_CANARY}` (optional, default off): on an authorized engagement, plant a canary token
  in the data source and watch the egress.

## Outputs

- `${HUNT_FINDINGS}`: per path `{data_source (class + sensitivity), hops, egress_sink, reachable:
  yes|guarded, canary_result?, exposure, verdict}`, ranked.
- `${REMEDIATION_LEADS}`: egress-allowlist / data-boundary / DLP-gate proposals → `remediation`.
- `${DETECTION_GAPS}`: "confidential data reached egress" rules → `detection-as-code-agent-rules`.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with per-lane notes.

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `graph.enrich` /
  `knowledge.graph` (information-flow edges from data sources to egress), `knowledge.query` (known
  exfil-channel patterns), `canary.mint`/`canary.plant`/`canary.scan`/`canary.verify` (prove a live
  path — authorized only), runtime `security.*` (recorded egress events), `risk.score`, `controls.map`.
- **Client-side:** build confidential-source → egress reachability over the information-flow graph;
  classify data sensitivity; identify boundary gaps; rank; shape remediation.
- **Sibling skills:** `engagement`, `information-flow` (flow graph + data classes), `enrich-indicator`,
  `canary-testing`, `confirm-action`, `remediation`, `record-in-engagement`,
  `detection-as-code-agent-rules`; atoms `atom-trace-egress`, `atom-enrich-component`,
  `atom-scan-canary`, `atom-map-controls`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET})` → context. Connected: ensure the ARS token. For
   canary confirmation, record the engagement authorization (dual-use discipline).
2. **Inventory data sources + egress sinks.** `information-flow`/`graph.enrich` across `${SCOPE_FILTER}`
   → confidential-data nodes (secrets, PII, proprietary context, privileged tool outputs) with their
   sensitivity class, and egress sinks (endpoints, message/webhook tools, external writes).
3. **Compute reachability.** Build paths from each data source through the flow graph to each egress
   sink; mark whether a data boundary / egress allowlist / DLP gate guards the path.
   `atom-query-pattern` for known exfil-channel shapes.
4. **Confirm live paths (optional, authorized).** For unguarded high-sensitivity paths, `canary-testing`
   mints a canary token, `canary.plant`s it in the data source, and `canary.scan`/`canary.verify` watches
   the egress — an egress hit is hard proof the path is live.
5. **Rank + route.** `risk.score` each path by sensitivity × egress exposure; `atom-trace-egress` the
   sink; confirmed exposure → `${REMEDIATION_LEADS}` (egress allowlist, data boundary, DLP gate) for
   `remediation` via `confirm-action`.
6. **Close the gap + checkpoint.** Emit `${DETECTION_GAPS}` ("confidential data reached egress") for
   `detection-as-code-agent-rules`; `record-in-engagement`; `engagement.checkpoint`.

```mermaid
sequenceDiagram
    participant Hunter
    participant RB as hunt-exfil-paths
    participant Eng as engagement
    participant IF as information-flow
    participant GW as AsterVault gateway
    participant REM as remediation
    Hunter->>RB: ${HYPOTHESIS}
    RB->>Eng: open(${TARGET}) → context
    RB->>IF: data sources + egress sinks (flow graph)
    IF-->>RB: sources (sensitivity) + sinks
    RB->>GW: graph.enrich reachability + knowledge.query patterns [X-ARS-Token]
    GW-->>RB: source → egress paths (guarded?), audit_id
    opt unguarded high-sensitivity + authorized
        RB->>GW: canary.plant(source) → canary.scan/verify(egress)
        GW-->>RB: canary egress hit (hard proof)
    end
    Note over RB: risk.score sensitivity × exposure; verdict
    alt exposed
        RB->>REM: ${REMEDIATION_LEADS} [confirm-action]
    else guarded
        Note over RB: document guarded posture
    end
    RB->>Eng: record events + checkpoint
    RB-->>Hunter: ${HUNT_FINDINGS}, ${REMEDIATION_LEADS}, ${STATUS}
```

## Decision Logic / Completion Criteria

- A path is **exposed** when a confidential-data source reaches an agent-controlled egress with no data
  boundary / allowlist / DLP guard; **confirmed live** when a planted canary token egressed; **guarded**
  when a boundary breaks the path.
- Canary confirmation runs on **authorized engagements only**, recorded in the engagement; remediation
  is a proposal applied via `confirm-action`.
- **Done when:** every confidential-source → egress path is enumerated and marked guarded/exposed (live
  ones canary-confirmed where authorized), exposed paths routed to remediation, the gap handed off, and
  the engagement checkpointed.

## Integration

- **Composes:** `information-flow`, `enrich-indicator`, `canary-testing`, `remediation`,
  `confirm-action`, `record-in-engagement`, `detection-as-code-agent-rules`; `engagement` bookends;
  atoms `atom-trace-egress`, `atom-enrich-component`, `atom-scan-canary`, `atom-map-controls`.
- **Called by:** `threat-hunt` playbook; feeds `remediation`; pre-stage for `irp-data-exfil-via-agent`;
  a stage of `apt-agent-threat-hunt`.
- **Offline:** reachability runs over the local information-flow graph; canary confirmation needs the
  gateway, so note live-path confirmation as **pending**; `risk.score`/`controls.map` degrade to local
  pack data. **Connected:** full flow grounding + canary proof + runtime `security.*`, metered.
