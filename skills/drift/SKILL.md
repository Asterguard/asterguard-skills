---
name: drift
description: Measure what changed between two versions of an agent and whether it got safer or more dangerous — a generic version-to-version differ across prompt, tools, controls, model, behavior, attack-surface and dependencies, that explains cause → effect ("v2 removed the approval gate → new exfiltration path → ASR 0→75%"). Use for release gates, continuous monitoring run-over-run, or incident forensics ("what changed since the last good run?").
---

# Drift (version-to-version差, explained)

Drift is one generic primitive — `drift(version_A, version_B, facet) -> Delta` — applied
across every facet of an agent. It does **not** re-profile or re-scan; it **diffs two
snapshots** the other skills already produce and **explains the change**. The deliverable is
not "ARS went up" — it is *which edit caused which regression*.

This skill is thin orchestration over the deterministic comparators in
[`tools/drift`](../../tools/drift/README.md); the calibrated drift index + trend come from the
`drift.compare` gateway via `atom-compare-drift` when connected.

## When to Activate

- **Release gate** — "did this version get worse than the last?" (composes under `pr-gate`).
- **Continuous monitoring** — run-over-run on the same deployed agent (run 1 → run 2).
- **Incident forensics** — "what changed since the last good run?" Drift *is* the answer.
- **A/B · model swap · dependency bump** — same skill, different version pair.

## Core Concepts

**Two snapshots, not a re-scan.** A version snapshot is what the pipeline already wrote to
`./.asterguard/`: the agent profile (`agent-profiling`: system_prompt, tools, controls,
model), the enriched surface facets (`graph.enrich`), the SBOM+CVE roll-up (`sca-graph`), and
the behavioral run-records (`behavioral-redteam`). Two runs in an `engagement` are two such
snapshots.

**Cause vs effect — the reason it is worth explaining.** The facets split into what a human
edited (**prompt · tools · controls · model** — cause) and what that did to posture
(**behavior · surface · sbom** — effect). The explainer links a cause-signal to the
effect-signal it predicts, so the output names the edit behind the regression.

**Security-signed, SSOT-driven.** Every signal carries a `direction` (worse/better/neutral)
and `weight` from `tools/drift/signals.yaml` — the single source of truth the comparators, the
explainer, and the gateway all read. Adding a signal or a facet is a YAML edit, never new
orchestration.

## Method

1. **Resolve the two versions.** Via `engagement`: `open(target)` then pick run A (baseline /
   N−1, or the `baseline` pointer) and run B (latest). Or take two explicit snapshot dirs /
   two commits the user hands you. Each resolves to a dir with any of `profile.json`,
   `surface.json`, `sbom.json`, `runs/`.
2. **Run the comparators.** `python tools/drift/drift.py <A_dir> <B_dir>` — it runs every
   applicable facet comparator, groups cause vs effect, aggregates to a band, and fires the
   cause→effect links into a narrative. (Call an individual comparator directly for a single
   facet, e.g. `tool_drift.py`.)
3. **Calibrate (connected).** Hand the assembled signals to `atom-compare-drift` →
   `drift.compare` for the calibrated drift index + the multi-run trend for this target;
   attach `X-ARS-Token`. Offline, keep the deterministic band and say the trend is unavailable.
4. **Record.** Append a `drift_measured` event to the `engagement` (from_run, to_run, band,
   per-facet deltas, regressions) so the trend compounds, and `memory.capture` the proven
   regressions.
5. **Report / gate.** Render the drift view via `risk-report` (two-version side-by-side +
   the cause→effect chain + a trend sparkline from the engagement log). For a gate, apply the
   org threshold: FAIL/WARN on `band ∈ {regression, critical-regression}` — e.g. any new
   proven break, an ARS band increase, or a newly-reachable regulated class.

## Connected vs Offline

- **Offline** (default): the full deterministic report — every per-facet `Delta`, the band,
  and the cause→effect narrative. Runs anywhere, no network, no token.
- **Connected**: adds the calibrated drift index + per-target trend from `drift.compare`
  (metered via `X-ARS-Token`), and syncs the `drift_measured` event to the shared knowledge
  store so the trend is cross-run and cross-box. The model stays server-side.

## Inputs / Outputs

- **Inputs:** two version refs (two engagement `run_id`s, two commits, or two snapshot dirs);
  optional facet selection (default: all present).
- **Outputs:** `DriftReport` (`schema: asterguard.drift/1`) — `{by_facet, causes[], effects[],
  aggregate{direction,magnitude,band}, links_fired[], narrative[], summary, calibration}`; a
  `drift_measured` engagement event; and the rendered drift view.

## AI Agent Execution Notes

- **Do not re-scan to get a snapshot** — drift reads what the pipeline already produced. If a
  snapshot is missing a facet, that facet is simply skipped; report which facets were compared.
- **Keep the local narrative and the gateway index consistent** — both read the same
  `signals.yaml`; pass the exact signals the comparators emitted to `drift.compare`.
- **Gate on the delta, never the backlog** — like `pr-gate`, the verdict is about what changed
  between the two versions, not the standing debt.
- `drift.compare` is the planned gateway tool; until it is deployed, connected runs degrade to
  the deterministic local report — expected, not an error.
