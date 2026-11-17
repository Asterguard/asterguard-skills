---
name: hunt-tool-abuse-lateral
description: Use when hunting lateral tool/agent abuse chains — one agent or tool pivoting into another's authority (confused-deputy hops, tool-to-tool privilege reuse, an agent invoking a peer to reach a resource it cannot reach directly) across the security graph and recorded agent events — the agent-security analogue of lateral movement, feeding confirmed gaps to detection-as-code.
---

# Hunt: Lateral Tool/Agent Abuse Chains

Proactively hunt chains where authority moves sideways between agents/tools: a confused-deputy hop, a
tool reused to reach a resource outside its caller's grant, or one agent invoking a peer to pivot into
authority it does not hold directly. The agent-security analogue of PsExec/WMI lateral movement —
here the "remote exec" is one component borrowing another's privilege. Sweep the graph for abusable
hops and the recorded events for chains actually walked.

## When to Activate

- A hypothesis or prior finding suggests privilege is hopping between components (confused deputy,
  tool chaining, over-trusting A2A/MCP calls).
- An over-privilege or injection hunt surfaced a pivot worth tracing end to end.

## Objective

Prove or clear lateral authority-abuse chains against `${TARGET}` under `${HYPOTHESIS}`, map each
confirmed chain end to end (origin → hops → reached resource), and route confirmed abuse to response.

## Scope

Covers: tool-to-tool / agent-to-agent authority-reuse chains and confused-deputy pivots across the
graph + recorded events. Excludes: single-node over-privilege (`hunt-over-privilege`), credential
theft (`hunt-agentic-ttp-credential-access`), exfil-only paths (`hunt-exfil-paths`), containment.

## Inputs

- `${HYPOTHESIS}`: string — the lateral-abuse hypothesis (e.g. "the summarizer tool is being chained
  through the file-writer to reach the deploy API"). *Source:* analyst / intel.
- `${TARGET}`: engagement target. *Source:* engagement.
- `${ORIGIN}` (optional): a starting agent/tool/identity to trace from.
- `${SCOPE_FILTER}` (optional): limit to a namespace / trust boundary.
- `${LOOKBACK}` (optional): recorded-event window.

## Outputs

- `${HUNT_FINDINGS}`: confirmed/suspected chains `{origin, hops:[tool/agent edges], reached_resource,
  evidence, verdict}`, negatives noted.
- `${DETECTION_GAPS}`: confirmed chain shapes lacking a covering rule → `detection-as-code-agent-rules`.
- `${ESCALATION}`: incident/finding id if escalated.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with per-lane notes.

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `graph.enrich` /
  `knowledge.graph` (authority edges, reach, trust boundaries between components), `knowledge.query`
  (known confused-deputy/tool-chaining patterns), runtime `security.*` (recorded tool-call chains),
  `risk.score`.
- **Client-side:** compute reachable authority-abuse paths over the graph; match recorded event
  sequences to abusable hops; correlate to the hypothesis; decide verdict.
- **Sibling skills:** `engagement`, `enrich-indicator`, `pivot-on-indicator`, `correlate-indicator`,
  `agent-timeline-analysis`, `record-in-engagement`, `detection-as-code-agent-rules`; atoms
  `atom-enrich-component`, `atom-lookup-identity`, `atom-query-pattern`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET})` → context. Connected: ensure the ARS token.
2. **Map abusable hops.** `graph.enrich`/`knowledge.graph` from `${ORIGIN}` (or across `${SCOPE_FILTER}`):
   find edges where one component can invoke/trust another whose authority exceeds the caller's — the
   candidate lateral hops. `atom-query-pattern` for known confused-deputy/tool-chaining shapes.
3. **Trace recorded chains.** Over `${LOOKBACK}`, search recorded tool-call sequences (`security.*`) for
   chains that actually walked those hops; `agent-timeline-analysis` reconstructs the order. Note
   negative results.
4. **Walk each chain end to end.** `pivot-on-indicator` origin → each hop → reached resource; confirm
   the resource was outside the origin's direct grant (that is what makes it lateral abuse).
5. **Correlate + decide.** `correlate-indicator` chain evidence vs `${HYPOTHESIS}`; verdict
   confirmed/suspected/absent.
6. **Escalate or clear.** Confirmed abuse → open a finding, hand to `irp-tool-abuse-rce` (or the
   matching IRP). Clean → document the cleared hypothesis.
7. **Close the gap + checkpoint.** Emit `${DETECTION_GAPS}` (chain shapes) for
   `detection-as-code-agent-rules`; `record-in-engagement`; `engagement.checkpoint`.

```mermaid
sequenceDiagram
    participant Hunter
    participant RB as hunt-tool-abuse-lateral
    participant Eng as engagement
    participant GW as AsterVault gateway
    participant TL as agent-timeline-analysis
    participant DET as detection-as-code-agent-rules
    Hunter->>RB: ${HYPOTHESIS} (+ ${ORIGIN})
    RB->>Eng: open(${TARGET}) → context
    RB->>GW: graph.enrich/knowledge.graph (authority hops) [X-ARS-Token]
    GW-->>RB: abusable hops, audit_id
    RB->>GW: security.* recorded tool-call chains
    GW-->>RB: event sequences
    RB->>TL: reconstruct chain order
    TL-->>RB: ordered chain(s)
    Note over RB: walk origin → hops → reached resource; verdict
    alt confirmed lateral abuse
        RB->>Eng: finding_opened → irp-tool-abuse-rce
        RB->>DET: ${DETECTION_GAPS} (chain shapes)
    else clean
        Note over RB: document cleared hypothesis
    end
    RB->>Eng: record events + checkpoint
    RB-->>Hunter: ${HUNT_FINDINGS}, ${DETECTION_GAPS}, ${STATUS}
```

## Decision Logic / Completion Criteria

- **Confirmed** when a recorded tool-call chain traverses an authority hop to reach a resource the
  origin could not reach directly. **Suspected** when the hop exists in the graph but no recorded chain
  walked it (a latent path — still a detection gap).
- Confirmed → escalate to the matching IRP; never contain inside the hunt.
- **Done when:** candidate hops are mapped, recorded chains traced (with negatives), each confirmed
  chain walked end to end and verdicted, gaps handed off, and the engagement checkpointed.

## Integration

- **Composes:** `enrich-indicator`, `pivot-on-indicator`, `correlate-indicator`,
  `agent-timeline-analysis`, `record-in-engagement`, `detection-as-code-agent-rules`; `engagement`
  bookends; atoms `atom-enrich-component`, `atom-lookup-identity`, `atom-query-pattern`.
- **Called by:** `threat-hunt` playbook; escalates to `irp-tool-abuse-rce`.
- **Offline:** path computation + recorded-chain trace run over the local graph/events; pattern
  research degrades to local pack data; note degraded lanes. **Connected:** full graph/knowledge
  grounding + runtime `security.*`, metered.
