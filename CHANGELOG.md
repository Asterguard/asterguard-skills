# Changelog

All notable changes to the AsterGuard skills pack are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Pre-1.0, minor
versions may include breaking changes to skill contracts; those are called out under **Changed**.

## [Unreleased]

### Added
- **Release process.** A hermetic pre-push smoke gate (`scripts/smoke.py`) that bundles the
  contract validator, the tool unit tests, and an offline pipeline smoke into one command —
  now the single thing CI runs. A gated, manually-dispatched **live end-to-end** test
  (`scripts/live_e2e.py` + `.github/workflows/live-e2e.yml`) that drives a real connected
  engagement against a gateway + target and asserts the audited, judged pipeline worked. A
  guarded release cutter (`scripts/release.sh`) and a `release-checklist` skill that walk the
  verify → smoke → changelog → tag → release → post-check sequence. This `CHANGELOG.md`.
- **Use-case videos wired for external hosting** — the `s1–s4` offensive scenario videos are
  referenced from the video host (like the launch films), not committed as binaries; a
  recording helper (`scripts/record-usecase.sh`) scaffolds the capture.

### Changed
- CI (`.github/workflows/ci.yml`) now runs `scripts/smoke.py` instead of three inline steps,
  so the hermetic gate has one definition that developers and CI share.

## [0.1.0] - 2026-11-25

First tagged release — the skills pack as an installable, contract-checked unit.

### Added
- **Drift toolkit** (`tools/drift/`) — a generic, reusable `drift(version_A, version_B)`
  primitive that diffs two versions of an agent across seven facets (prompt, tools, controls,
  model as *cause*; behavior, attack-surface, SBOM as *effect*) and explains cause → effect
  ("v2 removed the approval gate → new exfiltration path → ASR 0→75%"). SSOT-driven by
  `signals.yaml`; deterministic and offline by default, with an optional connected calibrated
  index via the gateway. Thin `skills/drift` and `skills/atom-compare-drift` wrappers.
- **Release safety net** — a contract validator (`scripts/validate.py`) checking skill
  frontmatter, link integrity, playbook/persona references, `mcp.json`, and `signals.yaml`
  SSOT agreement; a first GitHub Actions CI workflow running it on every PR and push.
- **The launch films** linked from the README (The Skills · The Invisible Risk · The Attack
  Surface · The Proof).
- The skills pack: 100+ composable security skills, playbooks, and personas; the live
  offensive harness (`tools/live-harness/`); worked examples and use-case scenarios.

[Unreleased]: https://github.com/Asterguard/asterguard-skills/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Asterguard/asterguard-skills/releases/tag/v0.1.0
