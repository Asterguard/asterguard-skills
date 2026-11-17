---
name: detection-coverage-evaluation
description: Use when evaluating how much of the agent-security threat surface the shipped `.rule.yaml` pack actually covers — cross-reference active threat rules against the weakness registry and the ATT&CK/CAPEC crosswalk, find the weaknesses and TTPs with no firing rule, rank the gaps by risk, and hand each to detection-as-code to close.
---

# Detection: Coverage Evaluation vs Registry / ATT&CK

Measure the pack's detection coverage against the ground-truth threat surface. Take the shipped
`.rule.yaml` threat rules, resolve each to its weakness id, and cross-reference against the weakness
registry and the weakness→CWE→CAPEC→ATT&CK crosswalk — then enumerate the weaknesses and TTPs with
**no** firing rule. The agent-security analogue of detection-engineering coverage evaluation: the
"TDOs" are registry weaknesses + crosswalk TTPs, and coverage is measured by whether a threat rule
fires over synthetic/known events for each.

## When to Activate

- Periodic detection-coverage review of an agent pack / engagement.
- After the weakness registry or the ATT&CK crosswalk is enriched (new weaknesses/TTPs to cover).
- A hunt/incident revealed a class of behavior the pack never detects.

## Objective

Produce a coverage map of `.rule.yaml` threat rules vs the weakness registry + ATT&CK/CAPEC crosswalk,
a ranked list of uncovered weaknesses/TTPs, and a handoff of each gap to `detection-as-code-agent-rules`.

## Scope

Covers: measuring rule coverage over the registry/crosswalk and ranking gaps. Excludes: authoring the
missing rules (`detection-as-code-agent-rules`), tuning precision/recall of existing rules
(`detection-rule-tuning`), validating a single rule fires (`detection-rule-validation`).

## Inputs

- `${PACK_PROFILE}`: the pack(s)/axes whose rules to evaluate. *Source:* pack layout / `scan.plan`.
- `${COVERAGE_FRAME}`: the ground truth to measure against — weakness registry subset and/or ATT&CK
  crosswalk scope. *Source:* `registry.resolve` + the weakness→control/ATT&CK crosswalk.
- `${TARGET}` (optional): an engagement whose graph/events scope which weaknesses are in play (focus
  coverage on what this target can actually manifest).
- `${SYNTH_EVENTS}` (optional): synthetic/known events per weakness/TTP to test whether a rule fires.

## Outputs

- `${COVERAGE_MAP}`: per weakness/TTP `{weakness_id, attack_refs, covering_rules:[…], covered: yes|no,
  fired_on_synth: yes|no}`.
- `${COVERAGE_GAPS}`: ranked uncovered weaknesses/TTPs (by risk × reachability on `${TARGET}`).
- `${GAP_HANDOFFS}`: one `${DETECTION_GAP}` per gap → `detection-as-code-agent-rules`.
- `${COVERAGE_SCORE}`: covered / total, by axis and by ATT&CK tactic.
- `${STATUS}`: ["Success" | "Partial" | "Failure"].

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `rules.fetch(profile)` (the
  active pack rules), `registry.resolve` (the weakness set + each rule's weakness id), `controls.map` /
  `knowledge.graph` (the weakness→CWE→CAPEC→ATT&CK crosswalk), `graph.enrich` (which weaknesses
  `${TARGET}` can manifest), `risk.score` (rank gaps).
- **Client-side:** join rules↔weaknesses↔crosswalk; run the `ThreatRuleEngine` over `${SYNTH_EVENTS}`
  to confirm a nominal rule actually fires; compute the map, gaps, and score.
- **Sibling skills:** `engagement`, `weakness-graph` (weakness↔component↔control crosswalk),
  `atom-fetch-rules`, `atom-resolve-weakness`, `atom-map-controls`, `detection-as-code-agent-rules`,
  `record-in-engagement`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET or pack})` → context. Connected: ensure the ARS token.
2. **Enumerate the frame.** From `${COVERAGE_FRAME}`: `registry.resolve` the weakness set and
   `controls.map`/`knowledge.graph` their ATT&CK/CAPEC crosswalk → the ground-truth list to cover.
   Scope to what `${TARGET}` can manifest via `graph.enrich` if provided.
3. **Inventory active rules.** `atom-fetch-rules`(`rules.fetch`) the pack rules; `atom-resolve-weakness`
   each → its `weakness_id` + `attack_refs`.
4. **Join coverage.** Map each weakness/TTP to its covering rule(s). A weakness with ≥1 rule is
   *nominally* covered; confirm **effective** coverage by running the `ThreatRuleEngine` over
   `${SYNTH_EVENTS}` for it — a rule that never fires is not coverage.
5. **Rank the gaps.** For each uncovered (or nominally-but-not-effectively covered) weakness/TTP,
   `risk.score` by severity × reachability on `${TARGET}` → `${COVERAGE_GAPS}`.
6. **Hand off.** Emit one `${DETECTION_GAP}` per gap to `detection-as-code-agent-rules`; compute
   `${COVERAGE_SCORE}` by axis and ATT&CK tactic.
7. **Record + checkpoint.** `record-in-engagement` the coverage map + score + handoffs;
   `engagement.checkpoint`.

```mermaid
graph TD
    START([${PACK_PROFILE} + ${COVERAGE_FRAME}]) --> OPEN["engagement.open"]
    OPEN --> FRAME["enumerate weaknesses + ATT&CK crosswalk (registry.resolve + knowledge.graph)"]
    FRAME --> RULES["inventory rules (rules.fetch) → weakness_id + attack_refs"]
    RULES --> JOIN["join weakness/TTP ↔ covering rule(s)"]
    JOIN --> EFF{"rule fires on synthetic events?"}
    EFF -- "no / none" --> GAP["uncovered → risk.score rank"]
    EFF -- "yes" --> COV["covered"]
    GAP --> HAND["${GAP_HANDOFFS} → detection-as-code-agent-rules"]
    COV --> MAP["${COVERAGE_MAP} + ${COVERAGE_SCORE}"]
    HAND --> MAP
    MAP --> CP["record-in-engagement + checkpoint"]
```

## Decision Logic / Completion Criteria

- A weakness/TTP counts as **covered** only when a rule resolves to it **and** fires over its
  synthetic/known events; a rule that resolves but never fires is a gap, not coverage.
- Rank gaps by risk × reachability so the highest-exposure uncovered behaviors are closed first.
- **Done when:** every in-scope weakness/TTP has a covered/uncovered verdict, gaps are ranked and
  handed to `detection-as-code-agent-rules`, the coverage score is computed, and the engagement is
  checkpointed.

## Integration

- **Composes:** `weakness-graph`, `atom-fetch-rules`, `atom-resolve-weakness`, `atom-map-controls`,
  `detection-as-code-agent-rules`, `record-in-engagement`; `engagement` bookends.
- **Called by:** `threat-hunt` playbook / periodic review; feeds `detection-as-code-agent-rules` (close
  gaps), `detection-rule-tuning` (nominal-but-ineffective rules), and `detection-report`.
- **Offline:** join + engine evaluation run over the local pack rules + local registry/crosswalk data
  (note where the crosswalk is incomplete offline); `risk.score` degrades to local pack data.
  **Connected:** full `rules.fetch` + registry/crosswalk grounding + scoring, metered with `audit_id`s.
