---
name: proactive-pattern-campaign-hunt
description: Use when launching a proactive hunt seeded from a known attack campaign or pattern (an agentic kill-chain, a published exploit pattern, a prior incident's TTP set) — pull the pattern's indicators and TTPs from the knowledge corpus, correlate them against the target's graph and recorded events, and feed confirmed gaps to detection-as-code.
---

# Hunt: Proactive Pattern / Campaign Hunt

Proactively hunt the target for a **known campaign or pattern**: given a pattern/campaign id, pull its
indicators and TTPs from the knowledge corpus (`knowledge.query`/`knowledge.graph`), then correlate
them against the built graph and recorded agent events to find any foothold. The agent-security
analogue of a GTI-campaign hunt — the "campaign" is a known agentic kill-chain or exploit pattern
rather than an APT infrastructure set.

## When to Activate

- A new campaign/pattern is published (agentic kill-chain, exploit pattern, prior-incident TTP set)
  and you must check whether this target is affected.
- A knowledge-corpus pattern is worth sweeping across the engagement proactively.

## Objective

Determine whether any indicator or TTP of `${PATTERN_ID}` is present in `${TARGET}` under
`${HYPOTHESIS}`, enrich confirmed presence, and route active matches to incident response.

## Scope

Covers: pulling a known pattern's indicators/TTPs and correlating them against the target's graph +
recorded events. Excludes: free-form multi-hypothesis hunts (`advanced-agent-threat-hunt`), single
ad-hoc indicators (`indicator-threat-hunt`), containment.

## Inputs

- `${HYPOTHESIS}`: string — the campaign hypothesis (e.g. "this target shows the LLM data-exfil
  kill-chain from incident X"). *Source:* analyst / intel.
- `${PATTERN_ID}`: the campaign/pattern/kill-chain id in the knowledge corpus. *Source:* intel feed,
  prior incident, weakness registry.
- `${TARGET}`: engagement target. *Source:* engagement.
- `${LOOKBACK}` (optional): recorded-event window.

## Outputs

- `${HUNT_FINDINGS}`: `{pattern, matched_indicators:[…], matched_ttps:[…], evidence, verdict}`, with
  non-matches noted.
- `${DETECTION_GAPS}`: matched TTPs lacking a covering rule → `detection-as-code-agent-rules`.
- `${ESCALATION}`: incident/finding id if escalated.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with per-lane notes.

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `knowledge.query` /
  `knowledge.patterns` / `knowledge.graph` (the pattern's indicators, TTPs, and kill-chain topology),
  `graph.enrich` (map indicators to target nodes), runtime `security.*` (recorded events for the TTPs),
  `memory.recall`, `risk.score`.
- **Client-side:** unpack the pattern into indicator + TTP sets; correlate each against graph/events;
  assemble the match verdict.
- **Sibling skills:** `engagement`, `enrich-indicator`, `correlate-indicator`, `indicator-threat-hunt`
  (per-indicator sweep), `record-in-engagement`, `detection-as-code-agent-rules`; atoms
  `atom-query-pattern`, `atom-recall-memory`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET})` → context. Connected: ensure the ARS token.
2. **Pull the pattern.** `knowledge.query`/`knowledge.graph`(`${PATTERN_ID}`) → the pattern's
   indicators, TTPs, and kill-chain topology.
3. **Correlate indicators.** For each indicator, sweep the graph + recorded events (compose
   `indicator-threat-hunt` per indicator, or `correlate-indicator` in bulk). Record matches +
   non-matches.
4. **Correlate TTPs.** For each TTP in the pattern, query recorded agent events (`security.*`) for the
   behavior; note which stages of the kill-chain have evidence on this target.
5. **Assemble verdict.** A match on any kill-chain stage = foothold; multiple contiguous stages =
   active campaign presence. Enrich confirmed matches with `enrich-indicator`.
6. **Escalate or clear.** Active campaign presence → open a finding and hand to the matching IRP. No
   matches → document the cleared hypothesis.
7. **Close the gap + checkpoint.** Emit `${DETECTION_GAPS}` for matched TTPs to
   `detection-as-code-agent-rules`; `record-in-engagement`; `engagement.checkpoint`.

```mermaid
graph TD
    START([${HYPOTHESIS} + ${PATTERN_ID}]) --> OPEN["engagement.open(${TARGET})"]
    OPEN --> PULL["knowledge.query/graph(${PATTERN_ID}) → indicators + TTPs"]
    PULL --> CORR_I["correlate indicators vs graph + events"]
    PULL --> CORR_T["correlate TTPs vs recorded events"]
    CORR_I --> ASSEMBLE{"kill-chain stages matched?"}
    CORR_T --> ASSEMBLE
    ASSEMBLE -- "contiguous stages" --> ESC["enrich + finding_opened → irp-*"]
    ASSEMBLE -- "isolated/none" --> DOC["document (incl. non-matches)"]
    ESC --> GAP["${DETECTION_GAPS} → detection-as-code-agent-rules"]
    GAP --> CP["record-in-engagement + checkpoint"]
    DOC --> CP
```

## Decision Logic / Completion Criteria

- **Active presence** when contiguous kill-chain stages of `${PATTERN_ID}` have evidence on the target;
  **foothold** when an isolated stage matches; **clear** when none do.
- Confirmed active presence → escalate to the matching IRP; never contain inside the hunt.
- **Done when:** every pattern indicator + TTP has been correlated (with non-matches recorded), the
  verdict is assembled with evidence, gaps handed off, and the engagement checkpointed.

## Integration

- **Composes:** `indicator-threat-hunt`, `enrich-indicator`, `correlate-indicator`,
  `record-in-engagement`, `detection-as-code-agent-rules`; `engagement` bookends; atoms
  `atom-query-pattern`, `atom-recall-memory`.
- **Called by:** `threat-hunt` playbook; escalates to `irp-*`.
- **Offline:** correlation runs over the local graph/events; the pattern corpus degrades to local pack
  data (note if the pattern id is unavailable offline). **Connected:** full knowledge-corpus + graph
  grounding + runtime `security.*`, metered.
