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

## Core Concepts — target-agnostic generation

Remediation is **not** tied to one policy language. A finding resolves to a **control** (via
AsterVault `controls.map`), and the control is emitted for whatever **target(s)** the environment
uses, from an **extensible catalog** (new targets are added as data server-side, never hardcoded):

| Target family | Examples | What it constrains |
|---|---|---|
| Workload identity | **SPIFFE/SPIRE** registration + authz | which workload identity may reach which service |
| Cloud IAM | **AWS IAM**, **GCP IAM**, **Azure** roles/deny | scoped resource access, least privilege |
| Network egress | **Envoy/Istio** egress, **k8s NetworkPolicy**, firewall allowlist | which destinations a workload may call |
| Policy engines | **OPA/Rego**, **Cedar**, k8s **AuthorizationPolicy** | request-level allow/deny rules |
| Data protection | **DLP** rules, tokenization/redaction obligations | what data may leave, in what form |
| Gateway | the **AsterVault PDP** policy + egress guardrail | enforced at the broker itself |
| …(open set) | added via the server-side target registry | — |

The **knowledge** (templates, the finding→control→policy mapping, per-target schemas) lives in
AsterVault — nothing ships client-side. The skill carries the **method**: pick the control, pick the
target(s), generate least-privilege, review, optionally enforce.

## Method

1. Select findings needing policy remediation: confidentiality flows, canary exfil hits,
   `over_privileged_agent`, confused-deputy, missing egress/identity control.
2. For each, call AsterVault `remediation.suggest(finding)` → the remediation approach + the control it
   satisfies (reuses `controls.map`).
3. Determine the allow-set from the **graph**: the legitimate identities (from agent-profiling/identity
   nodes) and destinations (the real sinks in information-flow) this workload actually needs.
4. Call `policy.generate(finding, target)` for each target the environment uses → the concrete
   artifact (SPIFFE entry, IAM policy, egress allowlist, Rego/Cedar, NetworkPolicy, DLP rule, AsterVault
   PDP). Default **deny**, allow only the graph-justified set.
5. Emit the artifacts as files / a PR with an explanation and the finding it closes.
6. **Review before enforce** (HITL). Optionally `policy.apply` so the AsterVault gateway enforces the
   egress allowlist / scoped credentials / tokenization immediately.
7. Record the remediation in the knowledge layer so future work reuses the approved policy.

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
- AsterVault `remediation.suggest` / `policy.generate` / `policy.apply` — knowledge + generation + enforcement
- AsterVault SPIFFE SVID auth · IAM backends · egress guardrail · PDP — the primitives the generated policy configures
- risk-report — shows each finding with its generated remediation and enforcement status

## References

- [Policy target catalog (extensible)](./references/policy-targets.md)
- [AsterVault MCP tools](../weakness-graph/references/astervault-tools.md)
