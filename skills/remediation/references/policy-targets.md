# Policy target catalog (extensible)

Remediation generates policy-as-code for whatever target(s) an environment uses. This is an **open
set** — the authoritative catalog, templates, and per-target schemas live server-side in the
AsterVault target registry and are added as data, not code. This file is the *method* map; it carries
no proprietary templates.

## Target families and when to emit them

| Target | Emit when the finding is… | Artifact shape |
|---|---|---|
| **SPIFFE/SPIRE** | over-privileged / unscoped **workload identity**; service-to-service trust too broad | registration entries + authorization policy (which SPIFFE ID may call which) |
| **AWS IAM** | over-broad AWS resource access; a role the task doesn't need | scoped policy + explicit `Deny` on the exfil path; permission-boundary |
| **GCP IAM** | same, on GCP | least-privilege role binding; org-policy constraint |
| **Azure** | same, on Azure | RBAC role assignment / custom role; deny assignment |
| **Envoy / Istio egress** | **data egress** to an unapproved destination | `ServiceEntry` + `AuthorizationPolicy` / egress gateway allowlist |
| **k8s NetworkPolicy** | a workload can reach destinations it shouldn't | default-deny egress + explicit allow to the graph-justified set |
| **k8s AuthorizationPolicy** | request-level over-permission | allow rules scoped to the real callers/paths |
| **OPA / Rego** | policy-engine-enforced allow/deny needed | a `deny` rule keyed to the finding's condition |
| **Cedar** | authorization over principals/resources/actions | a `forbid`/`permit` policy scoped least-privilege |
| **DLP / tokenization** | regulated data may leave in the clear | redaction/tokenization obligation on the egress path |
| **AsterVault PDP** | enforce at the gateway itself | a policy rule + enforcement mode (A/A'/B/B+) + egress allowlist entry |
| …(extensible) | a target not listed | added to the server-side registry; `policy.generate` gains it with no client change |

## Rules

1. **Default deny, allow the graph-justified set only.** The allow-list = the legitimate identities
   and destinations the data-flow proves are needed; everything else is denied. No hand-waved scopes.
2. **Emit the full set a fix needs.** A real exfil fix is usually identity (SPIFFE/IAM) **+** egress
   (allowlist) **+** gateway (PDP/DLP) — generate them together, not one in isolation.
3. **Review before apply.** Every generated policy is proposed for human approval; `policy.apply`
   enforces at the gateway only after that.
4. **Prefer enforcement at the chokepoint.** Where the AsterVault gateway sits on the path, enforce
   there (egress allowlist + broker/tokenize) in addition to the infra policy, so the fix holds even if
   the infra policy drifts.

## How a new target is added

Add it to the AsterVault target registry (template + schema + the control→target mapping). The client
`remediation` skill and `policy.generate` pick it up automatically — no skill change. This keeps the
catalog SSOT and dynamic rather than a hardcoded list.
