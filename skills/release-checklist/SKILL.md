---
name: release-checklist
description: Cut a clean, verified release of the skills pack — run the hermetic smoke gate, roll the changelog, tag and publish — so new features never ship on top of a broken pack. Use when a maintainer wants to release, tag a version, or verify the pack is release-ready before publishing.
---

# Release Checklist

Ship a release only when the pack is proven sound. The gate is hermetic and automated; this skill
is the human-facing walk-through of the same sequence [`scripts/release.sh`](../../scripts/release.sh)
enforces, plus the one manual step a machine can't do (the live E2E against a real gateway).

## When to Activate

- A maintainer asks to **release / tag a version / publish** the skills pack.
- Before publishing, to confirm the pack is **release-ready** (green gate, changelog current).
- After merging a batch of feature PRs, to roll them into a tagged version.

## The gate (in order — each blocks the next)

1. **Sound tree.** On `master`, clean working tree, in sync with `origin/master`. No release off a
   feature branch or a dirty tree.
2. **Hermetic smoke.** [`scripts/smoke.py`](../../scripts/smoke.py) passes — the contract validator
   (`validate.py --offline`), the tool unit tests, and the offline pipeline smoke. This is the same
   thing CI runs on every PR, so a green `master` is the precondition, not a surprise.
3. **Live E2E (manual, when releasing a behavioral change).** Dispatch
   [`live-e2e.yml`](../../.github/workflows/live-e2e.yml) (or run
   [`scripts/live_e2e.py`](../../scripts/live_e2e.py) locally) against a real gateway + target.
   It asserts the connected, audited, judged pipeline works. A **HELD is fine** — what's proven is
   that the pipeline ran end to end and every verdict was gateway-judged (never self-report). Skip
   only for doc/tooling-only releases.
4. **Changelog.** [`CHANGELOG.md`](../../CHANGELOG.md) `[Unreleased]` has entries. The release script
   rolls `[Unreleased] → [X.Y.Z] - <today>` and opens a fresh `[Unreleased]`; keep entries written as
   you merge, not reconstructed at release time.
5. **Tag + publish.** Annotated tag `vX.Y.Z`, push `master` + tag, create the GitHub release with
   generated notes.

## Method

Dry-run first to see the changelog roll and the plan without touching anything:

```bash
scripts/release.sh X.Y.Z --dry-run
```

When it looks right, cut it:

```bash
scripts/release.sh X.Y.Z
```

The script refuses to proceed if any gate fails (dirty tree, out-of-sync master, smoke failure, a
tag that already exists, or an empty `[Unreleased]`). Nothing is pushed until every gate passes.

## Versioning (pre-1.0)

- **patch** (`0.1.x`) — fixes, doc/tooling changes, no contract change.
- **minor** (`0.x.0`) — new skills/tools, or a breaking change to a skill contract (called out under
  **Changed** in the changelog while pre-1.0).

## Post-release

- Confirm the release page and that `master` CI is green on the release commit.
- If the release includes new use-case runs, record and host the videos
  (`scripts/record-usecase.sh`) — they are hosted, never committed.

## Integration

- `scripts/smoke.py` — the hermetic gate (gate 2), shared with CI.
- `scripts/live_e2e.py` + `live-e2e.yml` — the gated live proof (gate 3).
- `scripts/release.sh` — automates gates 1, 2, 4, 5.
- `CHANGELOG.md` — the release log the script rolls.
