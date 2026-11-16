# Rubric schema + the `controls.rubric` MCP contract

One schema serves both run modes: the bundled offline YAML packs and the MCP `controls.rubric` tool
return the **same shape**, so `evidence-judge` doesn't care where the rubric came from.

## `rubric_control`

```yaml
id: string                 # the control / clause id, verbatim from the framework (e.g. "A.8.12", "CC6.1")
title: string
objective: string          # what the control is trying to achieve, one sentence
evidence_required:         # the TYPES of evidence an auditor expects — the checklist to satisfy
  - type: policy|process|change|config|test|record|narrative
    what: string           # what specifically must exist
audit_questions:           # the questions the judge answers from evidence
  - string
maps_to: [string]          # crosswalk to other frameworks' clauses — MUST come from controls.map (SSOT)
security_signal:           # OPTIONAL — how an AsterGuard security review auto-supplies evidence
  weakness_ids: [string]   # weakness ids whose closed/open state is evidence
  satisfied_when: string   # the observable condition in the security graph that supports "satisfied"
```

## The MCP tool (connected mode, default)

```
controls.rubric(framework, version?) -> { framework, version, controls: [rubric_control] }
```

- Returns the **full, grounded, versioned catalog** — the proprietary knowledge, server-side (same
  place as the 578-weakness registry and the crosswalk). The client never ships it.
- `maps_to` is reconciled with `controls.map` on the server so there is exactly one crosswalk.
- `framework ∈ { iso-27001, iso-9001, soc2, hipaa, ... }`; `version` defaults to the current revision
  the server holds (e.g. `iso-27001:2022`). Unknown framework/version → error, never a fabricated set.

## The offline packs (fallback)

`control-rubric/references/packs/<framework>.yaml` carry a **representative subset** of controls in the
exact `rubric_control` shape — enough to run, demo, and air-gap. They are explicitly **seed packs**: the
MCP catalog supersedes them when connected, and `audit-report` states when a review ran from a seed
pack. Do not treat a seed pack as complete framework coverage.

## Pack file shape

```yaml
framework: iso-27001
version: "2022"
source: seed-pack            # vs "astervault" when from controls.rubric
controls:
  - { id: ..., title: ..., objective: ..., evidence_required: [...], audit_questions: [...], maps_to: [...], security_signal: {...} }
```
