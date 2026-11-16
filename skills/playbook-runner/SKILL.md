---
name: playbook-runner
description: Execute a security-review playbook — a configurable YAML that composes the building-block skills + vendor packs into one named review (architecture / design / deployment / full-360 / pr-gate). Use when asked to run a named review, a review of a given kind (architecture/design/deployment/compliance), or to run/customize a review playbook; it resolves the playbook, runs its steps, applies its gate, and emits its report.
---

# Playbook Runner

The security engineer's review functions — architecture review, design review, deployment review,
compliance, the full 360, the PR gate — are **playbooks**: configurable YAML that composes the
building-block skills + vendor packs. This skill executes any playbook against the schema in
`references/playbook-schema.md`. The review is **data**; only this runner and the rule engine are code,
so engineers and customers customize reviews by editing YAML, not skills.

## When to Activate

- "Run the architecture / design / deployment / compliance review", "run the 360", "gate this PR".
- A request to run a **named** playbook, or a review of a given **kind**.
- To define or customize a review — the person edits/forks a playbook; this runner executes it.

## Core Concepts

**Three layers of configuration, all data:** **packs** (how to read a vendor — `plugin.yaml`), **rules**
(what to detect — `.rule.yaml`), **playbooks** (which review, composed how — this schema). The runner is
the thin executor over all three.

**Reviews are compositions, not new scanners.** A playbook's `steps` are existing capability skills
(`data-flow`, `weakness-graph`, …) and `lens`es (named review question-sets). The runner orders and runs
them; it never re-implements a building block.

**Posture is a field.** `validate` = advisory (SecEng: report, never block). `gate` = pass/fail over the
delta (dev: `pr-gate`). The same composition serves both — only `posture` + `gate` differ.

**Customer override by name.** A playbook in `./.asterguard/playbooks/` overrides a shipped one of the
same name, so an org tailors a review (its steps, packs, rules, thresholds, report) without forking code.

## Method

1. **Load** the playbook: resolve `name` → `playbooks/<name>.yaml`, then `./.asterguard/playbooks/<name>.yaml`
   (later wins). Validate required fields (`name`, `posture`, `input`, `steps`).
2. **Scope + profile**: resolve `input` + `scope`; run `check-planner` to build the target profile and the
   standard-checks plan.
3. **Resolve packs**: `rules.fetch(profile)` (connected) or local pack load (offline), filtered by the
   playbook's `packs` axes/vendors.
4. **Run `steps` in order.** A `skill:` step runs that capability skill (passing `with:` args), writing its
   artifact to `./.asterguard/`. A `lens:` step applies its question-set (from the schema) **and** evaluates
   the matching pack threat-rules via the engine over the current graph/events → findings resolved to
   weakness ids.
5. **Filter + gate**: keep findings per `rules` (categories / severity_min / weakness_ids); if
   `posture: gate`, apply `gate` over the delta → `PASS | FAIL | WARN` (see `pr-gate`); `validate` reports
   only.
6. **Report + capture**: emit the `report` sections (HTML via `risk-report`, or the gate summary);
   `engagement` checkpoints the run (events, findings, the pack set) so the next run starts informed.

## Practical Guidance

- **Don't hardcode a review.** If a request is a kind of review, run the matching playbook; if none fits,
  compose a new playbook YAML rather than improvising steps — reviews must be reproducible and auditable.
- **Steps are the building blocks.** Never re-implement `data-flow`/`weakness-graph`/etc. inside the
  runner; a playbook only *orders* them.
- **Lenses read, packs detect.** A `lens:` supplies the questions; the pack threat-rules supply the
  machine detections — report both.
- **Everything client-side.** Steps, lenses, pack rules all run on the box; the MCP only serves pack
  content and grounding.

## Integration

- **Shipped playbooks** (`playbooks/`): `full-360`, `architecture-review`, `design-review`,
  `deployment-review`, `pr-gate` (and `compliance` via `compliance-auditor`).
- **Composes:** every capability skill as a `step`; `check-planner` (profile + plan), `engagement`
  (context bookends), the vendor **packs** + `rules.fetch`, the scanner's `ThreatRuleEngine` (lens rules).
- **Supersedes the hardcoded orchestrators:** `security-engineer` = the `full-360` playbook; `pr-gate` =
  the `pr-gate` playbook. Those skills remain as named entrypoints that invoke this runner.

## References

- `references/playbook-schema.md` — the full schema, `input`/`step`/`lens`/`gate`/`report` vocabulary, and
  the runner's resolution order.
- `../../docs/RUN_PLAYBOOK.md` — the end-to-end chain and the knowledge-store persistence model.
