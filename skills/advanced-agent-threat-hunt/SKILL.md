---
name: advanced-agent-threat-hunt
description: Use when running a deep, multi-hypothesis, iterative hunt over an agent target that goes beyond a single indicator or TTP — formulate several hypotheses, sweep the security graph and recorded events, pivot on what you find, and iterate until each hypothesis is confirmed or cleared, feeding confirmed gaps to detection-as-code.
---

# Hunt: Advanced Multi-Hypothesis Agent Hunt

The flexible, iterative hunt for a threat hunter working a target with no single clean indicator:
formulate multiple hypotheses from intel or observed anomalies, sweep the built graph + recorded agent
events, pivot on each lead, refine the hypotheses, and repeat until the surface is covered. The
agent-security analogue of hypothesis-driven advanced threat hunting — behavioral and anomaly-led
rather than IOC-led.

## When to Activate

- Broad intel (a new agentic-threat report, a novel technique) or an observed anomaly warrants a
  deep-dive hunt beyond `indicator-threat-hunt` / the guided TTP hunts.
- A tier-3 hunter owns a target and wants an iterative, multi-hypothesis sweep.

## Objective

Confirm or clear a set of hypotheses about `${TARGET}` through iterative graph/event analysis and
pivoting, surfacing both confirmed threats and detection gaps, under the guiding `${HYPOTHESIS}`.

## Scope

Covers: multi-hypothesis, iterative, pivot-driven hunting over one target's graph + recorded events.
Excludes: single-indicator sweeps (`indicator-threat-hunt`), a single named TTP family (the guided
hunts), containment (IRPs).

## Inputs

- `${HYPOTHESIS}`: string — the top-level hunt objective; sub-hypotheses are derived during the hunt
  (e.g. "this agent is being steered to exfiltrate data via a novel channel"). *Source:* hunter.
- `${TARGET}`: engagement target. *Source:* engagement.
- `${INTEL_REFS}` (optional): knowledge-corpus pattern/report ids giving context.
- `${SCOPE_FILTER}` (optional): initial surface to narrow the first iteration.
- `${LOOKBACK}` (optional): recorded-event window (default: wide, e.g. the full engagement history).

## Outputs

- `${HUNT_FINDINGS}`: per sub-hypothesis `{statement, verdict: confirmed|suspected|cleared, evidence,
  pivots_taken}`, negatives recorded.
- `${DETECTION_GAPS}`: confirmed behaviors lacking a covering rule → `detection-as-code-agent-rules`.
- `${NEW_HYPOTHESES}`: leads worth a follow-up hunt.
- `${ESCALATION}`: incident/finding id(s) if escalated.
- `${STATUS}`: ["Success" | "Partial" | "Failure"] with per-lane notes.

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `knowledge.query` /
  `knowledge.graph` (intel + technique context), `graph.enrich` (iterative pivoting), runtime
  `security.*` (recorded-event search), `memory.recall`, `risk.score`.
- **Client-side:** formulate + refine hypotheses; build each iteration's query; analyze for outliers /
  anomalies; decide pivots; judge each hypothesis.
- **Sibling skills:** `engagement`, `enrich-indicator`, `pivot-on-indicator`, `correlate-indicator`,
  `deep-dive-indicator-analysis`, `agent-timeline-analysis`, `record-in-engagement`,
  `detection-as-code-agent-rules`; atoms `atom-query-pattern`, `atom-enrich-component`,
  `atom-recall-memory`.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET})` → context + history. Connected: ensure the ARS
   token.
2. **Frame hypotheses.** From `${HYPOTHESIS}` + `${INTEL_REFS}` (`knowledge.query`) + the engagement's
   anomalies, write a short set of testable sub-hypotheses.
3. **Iterate per hypothesis (loop):**
   a. Build an initial query over the graph + recorded events (`security.*`), scoped by `${SCOPE_FILTER}`.
   b. Analyze for outliers/anomalies supporting or refuting it.
   c. **Pivot:** `pivot-on-indicator` / `graph.enrich` on each lead; `deep-dive-indicator-analysis` on
      the strongest; refine the hypothesis and re-query. Repeat until converged.
   d. Record the verdict (confirmed/suspected/cleared) + evidence, including negatives.
4. **Enrich + correlate.** `enrich-indicator` confirmed leads; `correlate-indicator` across
   sub-hypotheses to see if separate leads are one threat.
5. **Route.** Confirmed threat → open a finding and hand to the matching IRP. Inconclusive leads →
   `${NEW_HYPOTHESES}` for a follow-up. Clean → document.
6. **Close the gap + checkpoint.** Emit `${DETECTION_GAPS}` for `detection-as-code-agent-rules`;
   `record-in-engagement` the hypotheses, pivots, verdicts; `engagement.checkpoint`.

```mermaid
graph TD
    START([${HYPOTHESIS}]) --> OPEN["engagement.open(${TARGET})"]
    OPEN --> FRAME["frame sub-hypotheses (knowledge.query + anomalies)"]
    FRAME --> LOOP["iterate: query graph + security.* events"]
    LOOP --> ANALYZE{"anomaly supports hypothesis?"}
    ANALYZE -- "lead" --> PIVOT["pivot-on-indicator + deep-dive-indicator-analysis → refine"]
    PIVOT --> LOOP
    ANALYZE -- "converged" --> VERDICT{"confirmed?"}
    VERDICT -- "yes" --> ESC["enrich + finding_opened → irp-*"]
    VERDICT -- "inconclusive" --> NEWH["${NEW_HYPOTHESES}"]
    VERDICT -- "cleared" --> DOC["document (incl. negatives)"]
    ESC --> GAP["${DETECTION_GAPS} → detection-as-code-agent-rules"]
    GAP --> CP["record-in-engagement + checkpoint"]
    NEWH --> CP
    DOC --> CP
```

## Decision Logic / Completion Criteria

- A sub-hypothesis is **confirmed** when graph + recorded-event evidence converges on it after
  pivoting; **suspected** when evidence is partial; **cleared** when iterative search exhausts the
  surface with only negatives.
- Confirmed → escalate to the matching IRP; inconclusive → record as a `${NEW_HYPOTHESES}` lead, never
  leave it implicit.
- **Done when:** every framed sub-hypothesis is verdicted with evidence (including negatives), gaps and
  new hypotheses are handed off, and the engagement is checkpointed.

## Integration

- **Composes:** `enrich-indicator`, `pivot-on-indicator`, `correlate-indicator`,
  `deep-dive-indicator-analysis`, `agent-timeline-analysis`, `record-in-engagement`,
  `detection-as-code-agent-rules`; `engagement` bookends; atoms `atom-query-pattern`,
  `atom-enrich-component`, `atom-recall-memory`.
- **Called by:** `threat-hunt` playbook; escalates to `irp-*`; feeds `apt-agent-threat-hunt` when a
  lead implicates a known actor/campaign.
- **Offline:** iterative sweep runs over the local graph/events; intel context degrades to local pack
  data; note degraded lanes. **Connected:** full knowledge/graph grounding + runtime `security.*`,
  metered.
