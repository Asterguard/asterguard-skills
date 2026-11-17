---
name: hunt-over-privilege
description: Use when hunting agents, tools, and identities that hold more authority than they need across the security graph — granted scopes, tool permissions, or reach that exceed the principal's actual usage (authority > need) — ranking each excess grant by blast radius and feeding confirmed over-privilege to remediation and detection-as-code.
---

# Hunt: Over-Privilege (Authority > Need)

Hunt the graph for principals carrying excess authority: an agent granted tools it never calls, a
service identity with scopes beyond its workload, a tool whose reach exceeds its job. Compare each
principal's **granted** authority against its **exercised** authority (recorded events), rank the gap
by blast radius, and route confirmed over-privilege to least-privilege remediation. Standing
over-privilege is the precondition for most agent incidents — this hunt finds it before an attacker
does.

## When to Activate

- Periodic least-privilege review of an agent deployment, or after a grant/scope change.
- A hypothesis that a principal holds authority it does not use (scope creep, copy-pasted broad roles,
  unused tool grants).

## Objective

Find and rank principals whose granted authority exceeds their exercised need across `${TARGET}` under
`${HYPOTHESIS}`, and hand each confirmed excess grant to remediation with its blast radius.

## Scope

Covers: excess authority on a single principal (agent / tool / identity) measured as granted vs
exercised across the graph + recorded events. Excludes: lateral abuse chains
(`hunt-tool-abuse-lateral`), injection reachability (`hunt-prompt-injection-exposure`), applying the
fix (that is `remediation`, human-gated).

## Inputs

- `${HYPOTHESIS}`: string — the over-privilege hypothesis (e.g. "the support agent holds deploy scopes
  it never uses"). *Source:* analyst / periodic review.
- `${TARGET}`: engagement target. *Source:* engagement.
- `${SCOPE_FILTER}` (optional): limit to an identity / namespace / tool family.
- `${LOOKBACK}` (optional): recorded-event window used to measure exercised authority (default: wide,
  so unused grants are not misread as used).

## Outputs

- `${HUNT_FINDINGS}`: per principal `{principal, granted:[scopes/tools/reach], exercised:[…],
  excess:[granted − exercised], blast_radius, verdict}`, ranked.
- `${REMEDIATION_LEADS}`: least-privilege proposals (scopes/tools to drop) → `remediation`.
- `${DETECTION_GAPS}`: "authority used beyond baseline" rules worth adding → `detection-as-code-agent-rules`.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with per-lane notes.

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `graph.enrich` /
  `knowledge.graph` (granted scopes, tool permissions, reach per principal), runtime `security.*`
  (recorded tool-calls / scope usage = exercised authority), `risk.score` (blast radius / index),
  `controls.map` (least-privilege control for each gap).
- **Client-side:** diff granted vs exercised authority per principal; compute blast radius; rank;
  shape least-privilege proposals.
- **Sibling skills:** `engagement`, `enrich-indicator`, `agent-profiling` (authority graph),
  `record-in-engagement`, `remediation`, `confirm-action`, `detection-as-code-agent-rules`; atoms
  `atom-lookup-identity`, `atom-enrich-component`, `atom-map-controls`, `atom-score-finding`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET})` → context. Connected: ensure the ARS token.
2. **Inventory granted authority.** `graph.enrich`/`agent-profiling` across `${SCOPE_FILTER}` → each
   principal's granted scopes, tool permissions, and reach.
3. **Measure exercised authority.** Over `${LOOKBACK}`, aggregate recorded tool-calls / scope usage
   (`security.*`) per principal → what each actually used.
4. **Diff → excess.** For each principal, `excess = granted − exercised`. A non-empty excess is a
   candidate over-privilege finding.
5. **Rank by blast radius.** `risk.score` each excess grant (what it reaches, what it could touch);
   `enrich-indicator` the principal + the excess scope; `atom-map-controls` the least-privilege control.
6. **Route.** Confirmed excess → `${REMEDIATION_LEADS}` for `remediation` (least-privilege policy,
   applied only via `confirm-action`). Add a "used beyond baseline" `${DETECTION_GAPS}` entry so future
   drift is caught.
7. **Record + checkpoint.** `record-in-engagement` the excess findings + proposals;
   `engagement.checkpoint`.

```mermaid
sequenceDiagram
    participant Hunter
    participant RB as hunt-over-privilege
    participant Eng as engagement
    participant GW as AsterVault gateway
    participant REM as remediation
    participant DET as detection-as-code-agent-rules
    Hunter->>RB: ${HYPOTHESIS}
    RB->>Eng: open(${TARGET}) → context
    RB->>GW: graph.enrich / agent-profiling (granted) [X-ARS-Token]
    GW-->>RB: granted scopes/tools/reach, audit_id
    RB->>GW: security.* usage (exercised)
    GW-->>RB: exercised authority
    Note over RB: excess = granted − exercised; risk.score blast radius
    alt excess found
        RB->>REM: ${REMEDIATION_LEADS} (least-privilege) [confirm-action]
        RB->>DET: ${DETECTION_GAPS} (used-beyond-baseline)
    else least-privilege clean
        Note over RB: document clean posture
    end
    RB->>Eng: record events + checkpoint
    RB-->>Hunter: ${HUNT_FINDINGS}, ${REMEDIATION_LEADS}, ${STATUS}
```

## Decision Logic / Completion Criteria

- A grant is **over-privileged** when it appears in `granted` but never in `exercised` across a `${LOOKBACK}`
  wide enough to be representative; severity ranks by blast radius (`risk.score`).
- Remediation is a **proposal** only — applying it goes through `remediation` + `confirm-action` and is
  recorded as a `decision`; the hunt never narrows a grant itself.
- **Done when:** every in-scope principal has a granted-vs-exercised diff, excess grants are ranked and
  routed to remediation, the drift-detection gap is handed off, and the engagement is checkpointed.

## Integration

- **Composes:** `agent-profiling`, `enrich-indicator`, `remediation`, `confirm-action`,
  `record-in-engagement`, `detection-as-code-agent-rules`; `engagement` bookends; atoms
  `atom-lookup-identity`, `atom-enrich-component`, `atom-map-controls`, `atom-score-finding`.
- **Called by:** `threat-hunt` playbook; feeds `remediation` and `hunt-tool-abuse-lateral` (excess
  authority is the hop a lateral chain abuses).
- **Offline:** granted vs exercised diff runs over the local graph + recorded events; `risk.score` /
  `controls.map` degrade to local pack data (note it); the diff itself still completes. **Connected:**
  full graph grounding + runtime `security.*` usage + scoring, metered.
