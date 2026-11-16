---
name: pr-gate
description: Run a diff-scoped agentic-security review on a pull request and return a pass/fail gate — scope the scan to the change, red-team the risk it introduces, prove breaks with canaries, and block only on what the PR adds. Use when a developer (or CI) wants to security-check a PR/diff before merge or release, not assess a whole repo.
---

# PR Security Gate (developer pre-release gate)

> Realized as the **`pr-gate`** playbook (`playbooks/pr-gate.yaml`, `posture: gate`), run by
> `playbook-runner`. This skill is the named entrypoint; the pipeline below is that playbook's
> composition as data — customizable per org.

The developer-posture twin of `security-engineer`. Where that skill does a full, advisory review of a
whole target, this one reviews **a pull request's change** and ends in a **gate decision** —
`PASS | FAIL | WARN` — so a developer can run `test → enforce → ship` themselves before merge, without a
security-team round-trip. It runs in a dev shell or in CI on a PR.

## When to Activate

- A developer or a CI job asks to "security-check / gate / review this PR (or diff / branch / commit range)".
- The intent is a **merge/release decision on a change**, not a full assessment of the repo.
- A pre-release self-gate: the author wants to prove their change is safe and apply the fix themselves.

For a full repo/agent assessment with an advisory report, use `security-engineer` instead.

## Core Concepts

**Gate on the delta, not the backlog.** A PR check that blocks on pre-existing findings is unusable, so
the gate's verdict is computed over what the PR *introduces or worsens* versus a baseline — never the
whole backlog. Pre-existing debt is reported as context, never a blocker.

**Baseline = the knowledge store.** "New" is defined against the app's last known state, recalled from the
AsterGuard knowledge store (`memory.recall` / `knowledge.graph` for this app), or a baseline scan of the
merge-base commit when no prior state exists. The delta is `head − base`.

**Scoped, but reachability-aware.** The review set is the changed files/components **plus their reachable
neighbors** in the graph — so a change that newly feeds a known sink (egress, a sensitive field) is
in-scope even if the sink file itself didn't change. A diff is not just the touched lines.

Like every skill, each stage writes to `./.asterguard/` (here under `./.asterguard/pr/<sha>/`) so the gate
is cacheable, resumable, and inspectable, and builds to the shared schema (`graph-schema.md`).

## The gate pipeline

1. **Resolve the change + baseline.** Read the diff (`git diff base...head`): changed files + hunks,
   and any dependency-manifest / IaC / config changes. `knowledge-recall` pulls the app's baseline
   (prior graph, findings, decisions, waivers) so the delta is well-defined. Classify the change:
   `code` · `deps` · `config` · `agent-behavior` (new tool / prompt / egress / data path).
2. **Scope.** Compute the review set = changed components + reachable neighbors from the baseline graph.
3. **Scan the delta.** Run collectors scoped to the change — SAST (semgrep/opengrep) on changed files,
   `sca-graph` only if manifests changed, `data-flow` / `information-flow` delta on touched stores/fields.
   Build the partial graph and merge it onto the recalled baseline.
4. **Resolve + score.** `registry.resolve` each finding → canonical weakness, `risk.score` for the
   **feature vector** (the harness composes the risk from it — no ARS model or eval runs here),
   `controls.map` for the clauses it touches. Diff against the baseline → the set of **new/worsened**
   weaknesses and the **risk delta** (harness-composed from the features, not a model score).
5. **Red-team what the change introduces.** For new/changed behavior (a new tool, a new egress, a new
   data path), run `behavioral-redteam` + `canary-testing` scoped to those paths; `security-judge` scores
   broke/held. A **new proven break** (a canary on egress) is the strongest gate signal.
6. **Decide the gate.** Apply the gate policy (`references/gate-policy.md`; data-driven, overridable per
   repo) to the delta → `PASS | FAIL | WARN` with a reason per blocking item. See below.
7. **Remediate + offer enforcement.** For each blocker, `remediation` drafts the least-privilege policy
   bundle grounded in the graph's allow-set. The developer can **apply it themselves** at the runtime
   gateway (`asterguard-runtimevault`'s `policy.apply(bundle, approved:true)`), then re-run the gate —
   this is the `test → enforce → ship` loop. The analysis side never enforces; it generates + recommends.
8. **Emit + capture.** Write `./.asterguard/pr/<sha>/gate.json` (verdict + blockers + fixes) and a
   PR-comment-ready summary, and set a non-zero exit on `FAIL` for CI. `memory-capture` records the
   decision and any waiver (with the *why*) back to the knowledge store.

## The gate decision

Default policy (fail-closed on what the change adds; everything keyed to the delta):

- **FAIL** if the PR introduces any: new **proven break** (canary-verified); new **high/critical** finding
  with no compensating control; new **PII/PCI/PHI → egress** flow with no gate; a **risk delta** above the
  repo's threshold (the harness composes risk from the feature vector; no ARS model runs client-side).
- **WARN** (merge allowed, flagged) for: new medium findings, new findings with a mitigating control
  already present, or a **risk delta** in the warn band.
- **PASS** otherwise — including when pre-existing findings remain (they are reported, not blocked).

The gate is reviewable, not a wall: a developer can **waive** a specific blocker with a reason, which is
captured to memory and (once a human promotes it) becomes an accepted exception for this app — so the same
item doesn't re-block every PR.

## Practical Guidance

- **Delta discipline (low freedom):** never let a pre-existing finding flip the verdict. If you can't
  establish a baseline, scan the merge-base once and treat *its* findings as the baseline — do not fail
  the PR for the repo's existing state.
- **Scope the red-team:** only exercise paths the diff changes or newly reaches; a full behavioral suite
  belongs to `security-engineer`, not a PR gate (latency + noise).
- **CI shape:** emit the machine verdict (`gate.json` + exit code) and the human summary (the PR comment).
  Keep the run bounded — a PR gate that takes too long gets disabled.
- **Enforcement is the dev's to apply:** this skill *recommends* the policy; applying it is an explicit
  `policy.apply(approved:true)` at the runtime gateway, after the canary proves the break is closed.

## Integration

- **Composes:** `knowledge-recall`, `local-scan`, `sca-graph`, `data-flow`, `information-flow`,
  `weakness-graph`, `behavioral-redteam`, `canary-testing`, `security-judge`, `remediation`, `memory-capture`.
- **MCP tools (when connected):** `registry.resolve`, `risk.score`, `controls.map`, `testgen.patterns`,
  `canary.*`, `knowledge.graph`, `memory.recall` / `memory.capture`. Offline, the harness model runs the
  delta review from the bundled knowledge and scans the change locally.
- **Enforcement target:** `asterguard-runtimevault` (`policy.apply`), never the analysis server.
- **Sibling:** `security-engineer` (full, advisory review — the security-engineer posture).

## References

- `references/gate-policy.md` — the gate-policy shape (thresholds, bands, waivers) and the default values.
- `../../docs/graph-schema.md` — the shared node/edge schema the delta graph is built to.
- `../../docs/RUN_PLAYBOOK.md` — the end-to-end chain and the knowledge-store persistence model.
