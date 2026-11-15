---
name: remediation
description: Turn a finding into an enforceable, least-privilege policy — generate egress and identity policy as code (SPIFFE/SPIRE, cloud IAM, network egress allowlists, OPA/Rego, Cedar, Kubernetes NetworkPolicy/AuthorizationPolicy, DLP, the AsterVault PDP, and more) grounded in the data-flow graph. Use when a security engineer wants the fix, not just the finding — especially for exfiltration, over-broad egress, or over-privileged identity.
---

# Remediation — policy generation

A finding describes a capability the system shouldn't have; remediation **removes it as policy**. The
policy is grounded in the graph: the *allowed* identities and destinations are exactly the legitimate
ones the data-flow shows are needed — everything else is denied. That removes the lethal trifecta's
third leg (the outbound channel) structurally, not by asking the model to behave.

## When to Activate

- A finding or **canary hit** shows exfiltration, over-broad egress, over-privileged identity, a
  confused-deputy path, or a missing egress/identity control.
- The engineer wants the fix as reviewable policy-as-code (and, optionally, enforced at the gateway).

## Core Concepts — target-agnostic generation (via `asterguard-remediation`)

Generation is **not** done here and **not** reinvented — it is the `asterguard-remediation` package:
a pure, deterministic **Finding → enforcement-policy morphism**. `from_episode(episode)` →
`RemediationPlan` of `ControlGap`s (one weakness, at one boundary, closed by one control: SPIRE / IAM
/ Egress / Tokenize / Network / Policy / Provenance / ToolGuard / Approval). `emit(target, plan)`
renders the plan to a dialect; `to_pr(plan, target, repo_root)` renders it as a **PR-style unified
diff**. The control catalog is YAML data and a new dialect is one emitter file — the extensible
catalog, SSOT. **AsterVault loads the emitted bundle to enforce; it does not regenerate.**

Targets the environment might use (each an `asterguard-remediation` emitter):

| Target family | Examples | What it constrains |
|---|---|---|
| Workload identity | **SPIFFE/SPIRE** registration + authz | which workload identity may reach which service |
| Cloud IAM | **AWS IAM**, **GCP IAM**, **Azure** roles/deny | scoped resource access, least privilege |
| Network egress | **Envoy/Istio** egress, **k8s NetworkPolicy**, firewall allowlist | which destinations a workload may call |
| Policy engines | **OPA/Rego**, **Cedar**, k8s **AuthorizationPolicy** | request-level allow/deny rules |
| Data protection | **DLP** rules, tokenization/redaction obligations | what data may leave, in what form |
| Gateway | the **AsterVault PDP** policy + egress guardrail | enforced at the broker itself |
| …(open set) | one new `asterguard-remediation` emitter + one catalog row | — |

The **knowledge** (control catalog + dialect templates) is `asterguard-remediation` data, SSOT — the
skill carries the **method**: build the plan, emit the target(s), open the PR, enforce.

## Method

1. Select findings needing policy remediation: confidentiality flows, canary exfil hits,
   `over_privileged_agent`, confused-deputy, missing egress/identity control.
2. `from_episode(episode)` → `RemediationPlan`; use `propose` / `for_review` to surface each gap with
   its frameworks. Unmapped gaps are surfaced, never dropped.
3. Determine the allow-set from the **graph**: the legitimate identities (from agent-profiling/identity
   nodes) and destinations (the real sinks in information-flow) this workload actually needs — these
   become the gap params. Default **deny**, allow only the graph-justified set.
4. `emit(target, plan)` for each target the environment uses (spire, scp/IAM, egress, networkpolicy,
   rego, cedar, tokenize, astervault…).
5. **Emit as a PR-style diff** — `to_pr(plan, target, repo_root)` renders each artifact to its target
   file as a unified diff (new-file or an edit to existing policy) with a PR body listing the control
   gaps closed. Open it as a **pull request** via `scripts/emit-pr.sh` (branch + commit + `gh pr create`):
   one PR per remediation, or one bundling an assessment's fixes.
6. **The PR review is the gate** — a human reviews/merges the diff; nothing is applied silently. After
   merge (or on explicit approval), **AsterVault loads the emitted bundle** and enforces (`policy.apply`):
   egress allowlist / scoped credentials / tokenization at the gateway.
7. Record the merged remediation in the knowledge layer so future work reuses the approved policy.

## Practical Guidance

- **Least privilege from the graph (low freedom):** never widen beyond what the data-flow proves is
  needed; an allow-list built from real sinks is defensible, a hand-waved one is not.
- **Match the target to the control:** identity over-privilege → SPIFFE/IAM; data egress → egress
  allowlist + DLP/tokenization; confused deputy → scoped credential + PDP rule. Most real fixes emit
  **several** targets together (identity + egress + gateway).
- **Enforce at the chokepoint when you can:** the AsterVault gateway can apply the egress allowlist and
  broker/ tokenize regulated data (modes B/B+), closing the loop find → fix → enforce.
- **Never auto-apply without review** — generate, explain, and let a human approve.

## Integration

- information-flow, weakness-graph, canary-testing — the findings that need fixing + the graph-derived allow-set
- **`asterguard-remediation`** — the SSOT Finding→policy morphism: `from_episode` / `emit` / `to_pr`
  (+ the YAML control catalog). Generation + PR-diff rendering live here, not in this skill.
- **AsterVault** — loads the emitted bundle and **enforces** (`policy.apply`): egress allowlist, scoped
  credentials (SPIFFE SVID / IAM), tokenization — via its existing PDP + egress guardrail. It does not regenerate.
- risk-report — shows each finding with its generated remediation PR and enforcement status

## References

- [Policy target catalog (extensible)](./references/policy-targets.md) — maps to `asterguard-remediation` emitters + controls catalog
- [AsterVault MCP tools](../weakness-graph/references/astervault-tools.md)
