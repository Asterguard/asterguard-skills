# drift — version-to-version drift toolkit

Deterministic, dependency-free comparators that answer: **what changed between two versions
of an agent, and did it make the agent more or less safe?** The `drift` skill is thin
orchestration over these scripts — the same way `local-scan` is thin orchestration over
`grype` / `checkov`.

Drift is one generic primitive — `drift(version_A, version_B, facet) -> Delta` — applied
across facets. The explanation (cause → effect) is the product, not a bare number.

## The contract

Every comparator emits the **same typed, security-signed `Delta`**:

```json
{
  "facet": "prompt|tools|controls|behavior|surface|model|sbom",
  "added": [...], "removed": [...], "changed": [...],
  "signals": ["weakened_guardrail", "new_egress_tool"],
  "direction": "worse|better|neutral",
  "magnitude": 0.0,
  "evidence": [...]
}
```

The security meaning of every signal (its `direction` and `weight`), plus the cause→effect
`links` and the verdict `bands`, live **only** in [`signals.yaml`](signals.yaml) — the SSOT.
Adding a signal or a new facet never edits a comparator. `common.py` loads the SSOT with
PyYAML when present, else a built-in minimal parser (so the toolkit runs with zero deps).

## Facets — cause vs effect

| Script | Facet | Role | Diffs |
|---|---|---|---|
| `prompt_drift.py` | prompt | cause | clause-level: dropped/weakened guardrails, new injectable surface |
| `tool_drift.py` | tools | cause | AI-BOM: tools ±, approval flipped, reach broadened, over-privilege |
| `controls_drift.py` | controls | cause | policy: control removed/loosened, allowlist widened, gap reopened |
| `model_drift.py` | model | cause | provider/model changed, sampling/safety loosened |
| `surface_drift.py` | surface | effect | attack-surface facets: new path / reach / egress sink, ΔARS |
| `behavior_drift.py` | behavior | effect | red-team run-sets: new break, ASR@budget ↑, refusal ↓ (+Beta-Binomial ASR) |
| `sbom_drift.py` | sbom | effect | dependency set, new KEV, CVE-surface growth |

`drift.py` composes all applicable comparators over two snapshot dirs, groups cause vs
effect, aggregates to a band, and runs `explain.py` to fire the cause→effect links into a
narrative ("v2 removed the approval gate → new exfiltration path → ASR 0→75%").

## Usage

```bash
# one facet, standalone
python tools/drift/tool_drift.py  A/profile.json B/profile.json
python tools/drift/surface_drift.py A/surface.json B/surface.json

# the whole thing over two version snapshots
python tools/drift/drift.py  A_dir/ B_dir/              # offline, deterministic
python tools/drift/drift.py  A_dir/ B_dir/ --connected  # + calibrated index from the gateway

# tests
python -m unittest discover -s tools/drift/tests
```

A **version snapshot** is a directory containing any of: `profile.json` (system_prompt,
tools, controls, model), `surface.json` (graph.enrich facets), `sbom.json` (sca-graph
roll-up), `runs/*.json` (behavioral run-records). See `tests/fixtures/v1` and `v2` for a
worked safe→regressed example.

## Offline vs connected (the enterprise boundary)

- **Offline** (default): the full deterministic report — every delta, the band, and the
  cause→effect narrative. Useful on its own, runs anywhere, no network.
- **Connected** (`--connected`): the assembled signals are handed to the AsterVault gateway
  tool **`drift.compare`** for a *calibrated drift index* + multi-run trend, metered via
  `X-ARS-Token`. The model stays server-side; the client only assembles signals and consumes
  the index. `drift.compare` is **not yet deployed** — the client already degrades cleanly
  (report returned, calibration marked degraded). Server implementation lands in the
  AsterVault MCP repo, not here.

## Extending — drop-in facets

Each new facet is one comparator + a few `signals.yaml` rows; the composer and explainer do
not change. Declared-but-not-yet-implemented adapters (same pattern):

- `identity_drift.py` — principals/roles/scopes broadened (`assumes`/`governs`); confused-deputy surface.
- `dataset_drift.py` — RAG corpus / knowledge sources changed; new untrusted-ingest surface.
- `config_drift.py` — IaC/config posture (checkov/kics); a bucket goes public, auth disabled.
- `secrets_drift.py` — new exposed credentials vs the last scan.
- `coverage_drift.py` — % weaknesses with a mapped+enforced control; compliance posture.

## This is one shape of a broader pattern: statistical skills

A "statistical skill" assembles observations client-side, hands them to a model, and consumes
a typed estimate + rationale (+ an offline/degraded flag). Many classical methods are
**closed-form and run locally** like these comparators; the learned ones live server-side.

**Local, closed-form (ship as `tools/` scripts):**
- Beta-Binomial ASR estimate (credible interval from few trials — already in `behavior_drift.py`).
- Distribution-drift stats — PSI, KL/JS divergence, KS test over feature distributions.
- Change-point detection — CUSUM / Page-Hinkley over a run-series ("when did posture regress?").
- Survival / hazard — Kaplan-Meier + Cox for time-to-break (inconclusive = right-censored).
- Trend/forecast — exponential smoothing on the ARS trajectory.
- Calibration — Brier score + reliability diagram on judge verdicts.

**Server-side, learned (gateway models, metered):**
- Risk scoring (`risk.score`), predictive-risk (change→vuln classifier), anomaly detection
  (isolation forest / autoencoder over tool-call sequences), causal inference (did control X
  cut breaks?), active test selection (Thompson-sampling bandit).
