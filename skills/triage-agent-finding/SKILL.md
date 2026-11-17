---
name: triage-agent-finding
description: Use when a STATIC scan finding emitted by `local-scan` or `weakness-graph` (not a runtime alert) needs a first-pass disposition — resolve the weakness, score it, check prior waivers and duplicates, then route to a severity and owner or close, without deep investigation or remediation.
---

# Runbook: Triage Agent Finding

Standardized first-pass assessment of a **static scan** finding — a weakness the shift-left scanners
(`local-scan`, `weakness-graph`) raised against a target before run time. The build-time sibling of
`triage-agent-alert`: there the signal is a live runtime alert; here it is a scanner-emitted weakness
with a code/graph locus. Triage only: it resolves, scores, and routes; it does not fix or deep-dive.

## When to Activate

- `local-scan` or `weakness-graph` emits a new finding (weakness on a component/identity/tool/egress
  path) that needs a disposition before it enters remediation or a release gate.
- A batch of scan findings must be severity-ranked and owner-routed.

## Objective

Produce a defensible disposition (`${ASSESSMENT}`) and routing (`${ACTION_TAKEN}`) for one static
finding — resolve what the weakness is, score it in context, honor any prior waiver, dedupe against
existing findings, then assign severity + owner or close.

## Scope

Covers: resolve the weakness, context-score it, check prior waivers + duplicates, set severity, route to
an owner or close.
Excludes: deep investigation, remediation/fix authoring (`remediation`), release-gate decisions
(`pr-gate`), and runtime alert triage (`triage-agent-alert`).

## Inputs

- `${FINDING_ID}`: string — the scan finding id. *Source:* `local-scan` / `weakness-graph` output.
- `${WEAKNESS_ID}`: string — the weakness the finding asserts (e.g. `LLM01-prompt-injection`).
  *Source:* finding payload. Typed `weakness_id` for `enrich-indicator`.
- `${TARGET}`: string — the app/repo + the locus (component/identity/tool/egress + code ref).
  *Source:* finding payload / engagement.
- `${FINDING_FEATURES}` (optional): object — scanner-supplied features (reachability, exposure,
  authority) fed to scoring. *Source:* scan artifact in `./.asterguard/`.

## Outputs

- `${ASSESSMENT}`: ["False Positive" | "Waived" | "Duplicate" | "Confirmed — <severity>"] — verdict +
  rationale.
- `${ACTION_TAKEN}` / route: ["Closed-FP" | "Closed-Waived" | "Closed-Duplicate" |
  "Routed → <owner>/<queue> @ <severity>"].
- `${WEAKNESS_FACTS}`: definition/STRIDE/CWE/attack_refs/controls (from `atom-resolve-weakness`).
- `${RISK_READ}`: ARS/DRS index + rationale (from `atom-score-finding`).
- `${WAIVER_CHECK}`: `{waived: yes|no, waiver:…, why:…}` from prior sightings.
- `${DUPLICATE_OF}`: prior finding id this duplicates, if any.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] — with a per-lane note on non-success.

## Tools

- **Gateway (connected, metered — carry `X-ARS-Token`, record each `audit_id`):** `registry.resolve`
  (via `atom-resolve-weakness`), `controls.map`, `risk.score` (via `atom-score-finding`),
  `memory.recall` (prior waivers).
- **Client-side:** assemble the feature vector from `${FINDING_FEATURES}` + the resolved facts; map the
  risk index to a severity band; pick the owner/queue.
- **Sibling skills:** `engagement` (open/context/checkpoint) · `atom-resolve-weakness` ·
  `atom-score-finding` · `check-duplicate-findings` · `record-in-engagement` · `close-finding`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET})` → load context + history. Connected: ensure the ARS
   token via `ars-token`. Pull prior dispositions for this locus from `engagement.context()`.
2. **Resolve the weakness.** `atom-resolve-weakness(${WEAKNESS_ID})` → `${WEAKNESS_FACTS}`
   (definition/STRIDE/CWE/attack_refs/controls). If it won't resolve, degrade to local pack data and
   note it in `${STATUS}`.
3. **Check prior waivers.** `atom-recall-memory` / `engagement.context()` for a waiver on this
   weakness+locus → `${WAIVER_CHECK}`. If actively waived with a valid *why*: `record-in-engagement` a
   `note`, `close-finding` (reason=`waived`), route **Closed-Waived**. Stop.
4. **Dedupe.** `check-duplicate-findings` over engagement + memory → `${DUPLICATE_OF}`. If confirmed:
   `close-finding` (reason=`duplicate`, root-cause=the prior id), route **Closed-Duplicate**. Stop.
5. **Score in context.** `atom-score-finding` over the feature vector (`${FINDING_FEATURES}` +
   reachability/authority from `${WEAKNESS_FACTS}`) → `${RISK_READ}` (index + rationale).
6. **Assess + set severity.** Decide FP vs confirmed; map `${RISK_READ}` to a severity band
   (critical/high/medium/low) → `${ASSESSMENT}`.
7. **Route + record.** FP → `close-finding` (reason=`false_positive`). Confirmed → pick the owner/queue
   by control family + severity and route. `record-in-engagement` the `verdict` + `decision` events
   (with `audit_id`s); `engagement.checkpoint`.

```mermaid
sequenceDiagram
    participant Analyst
    participant RB as triage-agent-finding
    participant Eng as engagement
    participant RW as atom-resolve-weakness
    participant SC as atom-score-finding
    participant Dup as check-duplicate-findings
    participant GW as AsterVault gateway
    Analyst->>RB: ${FINDING_ID}, ${WEAKNESS_ID}, ${TARGET}
    RB->>Eng: open(target) → context + history
    RB->>RW: resolve(weakness) [X-ARS-Token] → ${WEAKNESS_FACTS}, audit_id
    RB->>GW: memory.recall waivers → ${WAIVER_CHECK}
    alt actively waived
        RB->>Eng: close-finding (waived) + checkpoint
        RB-->>Analyst: Closed-Waived
    else not waived
        RB->>Dup: locus+weakness → ${DUPLICATE_OF}
        alt confirmed duplicate
            RB->>Eng: close-finding (duplicate) + checkpoint
            RB-->>Analyst: Closed-Duplicate
        else new finding
            RB->>SC: risk.score(features) [X-ARS-Token] → ${RISK_READ}, audit_id
            Note over RB: assess FP vs confirmed; map to severity
            alt False Positive
                RB->>Eng: close-finding (false_positive) + checkpoint
                RB-->>Analyst: Closed-FP
            else Confirmed
                RB->>Eng: record verdict + decision (owner/severity) + checkpoint
                RB-->>Analyst: Routed → owner @ severity
            end
        end
    end
```

## Decision Logic / Completion Criteria

- IF `${WAIVER_CHECK}.waived` THEN **Closed-Waived** → `close-finding`.
- IF `${DUPLICATE_OF}` confirmed THEN **Closed-Duplicate** → `close-finding`.
- IF the finding is unreachable/non-exploitable in context (per `${RISK_READ}`) THEN **Closed-FP**.
- ELSE **Confirmed** at the severity band from `${RISK_READ}` → route to the owner/queue (feeds
  `remediation` or a release gate). Higher bands may escalate to `investigate-agent-incident`.
- **Done when:** the weakness is resolved, waivers + duplicates are checked, a score + severity are set,
  the routing action is taken, and events are recorded + checkpointed.

## Integration

- **Composes:** `atom-resolve-weakness`, `atom-score-finding`, `check-duplicate-findings`,
  `close-finding`; `engagement` + `record-in-engagement` bookends.
- **Fed by:** `local-scan`, `weakness-graph`. **Routes to:** `remediation`, `pr-gate`, or
  `investigate-agent-incident` for confirmed high-severity findings.
- **Offline:** registry/score degrade to local pack data + the local graph; disposition still produced
  (noted `Partial`). **Connected:** full `registry.resolve` + `risk.score` + `memory.recall`, metered,
  each metered call records an `audit_id`.
