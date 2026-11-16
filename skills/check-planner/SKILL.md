---
name: check-planner
description: Plan the standard battery of security checks for a target — SAST/semgrep, DAST, IaC (kics/checkov), secrets/credentials, data-flow, PII, SCA, and compliance — as one client-side plan, grounded by recalled knowledge. Produces the list the standard checks run from; the behavioral red-team (attacker/defender/judge) is the follow-on. Use when you need to decide WHAT to check before running anything.
---

# Check Planner (the standard-tier plan)

Before any scan runs, decide **what** to check. This skill turns a target into one explicit, client-side
**plan** of the standard checks — SAST, DAST, IaC, secrets, data-flow, PII, SCA, compliance — each entry
grounded in recalled knowledge (which weaknesses matter for this stack), not a fixed pack. The plan is the
input the standard checks execute from, and it names the paths the **behavioral follow-on** should target.

Everything is **client-side**: the planning logic and the checks both run on the box. The AsterGuard
knowledge store is consulted for grounding (recalled weaknesses, crosswalk, approved patterns) — it does
not do the planning. Offline, the planner uses the bundled registry.

## When to Activate

- The first step of `security-engineer` (full review) or `pr-gate` (diff-scoped) — plan, then run.
- Any time you need the list of checks/tests to run for a repo, image, or live agent before scanning.
- To scope a run: the plan is where "only these checks, only these paths" is decided.

## Core Concepts

**Two tiers, in order.** The **standard tier** (this plan) is deterministic/structural and runs first:
static code, config, dependencies, secrets, data/PII flows, and compliance evidence. The **behavioral
tier** — `attacker` ▸ `defender` ▸ `judge`, orchestrated by `behavioral-redteam` — is the **follow-on**:
it runs after, and targets the risky paths the standard tier surfaced (a new tool, an ungated egress, a
sensitive data path). Standard = *is the code/config/data posture sound?*; behavioral = *can the running
agent be made to break it?*

**Grounded, not invented.** Each planned check carries the `weakness_id`(s) it hunts and the controls it
maps to, recalled from the knowledge store — so a finding is born resolved, and the plan is auditable
("why is this check here?").

**Scope is a plan input.** Full-repo (`security-engineer`) and diff-scoped (`pr-gate`) are the same plan
with a different scope: the diff planner keeps only checks whose targets intersect the change + its
reachable neighbors.

## The plan it produces

Written to `./.asterguard/plan.json` — a list of planned checks across the standard check types:

| Check type | Collector (client) | Plans |
|---|---|---|
| **SAST** | semgrep / opengrep | the rules/queries to run, grounded in the stack's weaknesses + the real data sinks |
| **DAST** | dast-generation | the dynamic tests to plan (endpoints/flows to probe) |
| **IaC** | kics / checkov | the config policies to run for the detected IaC |
| **Secrets / credentials** | trufflehog + patterns | the credential/secret checks (hit *locations*, never values) |
| **SCA** | grype / syft | the dependency CVE checks (from the SBOM) |
| **Data-flow** | data-flow | the source→sink paths to trace (stores/fields → tools → egress) |
| **PII** | information-flow (Presidio) | the field classes to detect + the flows to label (PII/PCI/PHI) |
| **Compliance** | compliance-auditor | the frameworks/controls to evidence (ISO 27001 / SOC 2 / HIPAA / …) |

```jsonc
// ./.asterguard/plan.json  (shape)
{
  "target": { "type": "code|infra|traffic", "profile": { "langs":[…], "frameworks":[…] } },
  "scope":  { "mode": "full|diff", "paths": […] },
  "checks": [
    { "type":"sast",     "collector":"semgrep", "rules":[…], "weakness_ids":[…], "targets":[…] },
    { "type":"iac",      "collector":"kics",    "policies":[…], "weakness_ids":[…] },
    { "type":"secrets",  "collector":"trufflehog", "weakness_ids":["hardcoded_secret"] },
    { "type":"sca",      "collector":"grype",   "from":"sbom" },
    { "type":"data_flow","targets":["store:*","data:*"] },
    { "type":"pii",      "classes":["pii","pci","phi"] },
    { "type":"dast",     "tests":[…] },
    { "type":"compliance","frameworks":["soc2","hipaa"] }
  ],
  "behavioral_followon": { "run": true, "target_paths":[…] }   // paths for attacker/defender/judge
}
```

## Method

1. **Profile the target** (local, cheap): languages, frameworks, entrypoints, declared data stores, IaC
   presence, dependency manifests. This decides which check types apply.
2. **Recall knowledge**: `knowledge-recall` → the weaknesses relevant to this stack, the control
   crosswalk, approved patterns, prior findings/waivers. (MCP `scan.plan` gives lane routing; this skill
   expands it into concrete checks.)
3. **Plan each check type** from the profile × recalled weaknesses: pick the SAST rules, the IaC policies,
   the data/PII sinks to trace, the compliance frameworks — each tagged with its `weakness_id`/controls.
4. **Scope** to full or diff.
5. **Mark the behavioral follow-on targets**: the paths the standard checks flag as risky (new/ungated
   egress, over-privileged tool, sensitive data path) become the attacker's targets in the next tier.
6. Emit `plan.json`. The orchestrator runs the standard checks from it, then the behavioral follow-on.

## Practical Guidance

- **Plan before you scan.** Don't run a collector that isn't in the plan; don't skip one that is. The plan
  is the contract between "what matters for this app" and "what we actually ran" — that's what makes a run
  auditable and a gate trustworthy.
- **Ground every entry.** A check with no `weakness_id` is noise; drop it or resolve it first.
- **Behavioral is a follow-on, never the opener.** Run the standard tier first; it both cheaply catches
  the structural issues and tells the behavioral tier where to aim.
- **All client-side.** The planner and the collectors run on the box; the knowledge store only grounds.

## Integration

- **Feeds:** `security-engineer` and `pr-gate` (both run `check-planner` as the planning step).
- **Standard-tier collectors it plans for:** `local-scan` (SAST/IaC/secrets/AI-BOM), `sca-graph`,
  `data-flow`, `information-flow`, `weakness-graph`, `dast-generation`, `compliance-auditor`.
- **Behavioral follow-on (tier 2):** `behavioral-redteam` → `attacker` ▸ `defender` ▸ `judge` +
  `canary-testing`, targeting the plan's `behavioral_followon.target_paths`.
- **MCP (grounding only):** `scan.plan`, `registry.resolve`, `controls.map`, `knowledge.*`, `memory.recall`.

## References

- `../../docs/graph-schema.md` — the shared schema the checks build to.
- `../../docs/RUN_PLAYBOOK.md` — the chain and the knowledge-store persistence model.
