# Gate policy — the PR gate's pass/fail rules

The gate policy is **data** (overridable per repo at `./.asterguard/gate-policy.yaml`, else the default
below). Every rule is evaluated over the **delta** (`head − base`), never the backlog.

## Shape

```yaml
# ./.asterguard/gate-policy.yaml
baseline: knowledge-store        # knowledge-store | merge-base | none
ars_delta:
  fail_at: 1.5                   # ARS increase (0–10) that fails the PR
  warn_at: 0.5
fail_on:                         # any one of these, introduced by the PR, fails it
  - new_proven_break             # a canary-verified break on a path the diff adds/reaches
  - new_finding_severity: high   # new finding >= this severity with no compensating control
  - new_ungated_sensitive_egress # new PII/PCI/PHI -> egress flow with no gate/DLP
warn_on:
  - new_finding_severity: medium
  - new_finding_with_control     # a new finding whose control is already present
  - ars_delta_warn_band
exempt:
  paths: ["**/test/**", "**/*_test.*", "docs/**"]   # changes here don't trigger the gate
require:                         # optional positive checks the PR must satisfy
  - controls_present_for: [new_ungated_sensitive_egress]
```

## Verdict

- **FAIL** — one or more `fail_on` conditions hold for the delta, or `ars_delta >= fail_at`. CI exits
  non-zero. Each blocker is reported with its weakness_id, where it was introduced (`file:line`), the
  canary evidence if any, and the recommended policy.
- **WARN** — only `warn_on` conditions hold (merge allowed, flagged on the PR).
- **PASS** — none of the above. Pre-existing findings that the PR does not worsen are listed as context,
  never as blockers.

## Waivers

A developer may waive a specific blocker:

```yaml
waivers:
  - weakness_id: llm_cfg_egress_no_dlp
    at: "handler.py:42"
    reason: "egress target is an internal, allow-listed service; DLP applied at the mesh"
    by: "dev@org"
```

A waiver is written to the knowledge store via `memory.capture` (kind `waiver`); it suppresses that one
item for this app until a human **promotes** it (`memory.promote`, the review gate) into an accepted
exception. Waivers are scoped to the app/team and audited — they are not a global mute.

## Why delta-scoped

A PR gate's only job is to keep a change from making the app's security posture worse. Blocking on the
repo's existing debt makes developers disable the gate; surfacing debt as context while gating strictly on
the delta keeps the gate trusted and in the merge path. Backlog burn-down is the `security-engineer`
posture's job, not the gate's.
