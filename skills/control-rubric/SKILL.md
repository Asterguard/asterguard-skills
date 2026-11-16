---
name: control-rubric
description: Resolve a compliance framework (ISO 27001, ISO 9001, SOC 2, HIPAA) into a per-control rubric — the audit questions, the evidence types an auditor expects, the crosswalk to other frameworks, and the security signals that can satisfy it. Uses the AsterVault controls.rubric tool when connected and bundled YAML packs offline. Use before judging controls, to know what evidence each control needs.
---

# Control Rubric

Turn a framework into something judgeable: for each control, **what question are we answering, what
evidence proves it, and what in our security graph already supplies that evidence.** The rubric is the
oracle the `evidence-judge` scores against.

## When to Activate

- After `evidence-collection`, before `evidence-judge`.
- Whenever a framework pack must be resolved or refreshed for an app/area.

## The contract

`control-rubric(framework, version?) → { framework, version, controls: [rubric_control] }` where a
`rubric_control` is:

```yaml
id: A.8.12                      # the control / clause id
title: Data leakage prevention
objective: Prevent unauthorized disclosure or exfiltration of information.
evidence_required:              # the TYPES an auditor expects — the checklist
  - { type: policy, what: A documented DLP / egress-control policy }
  - { type: config, what: Enforced default-deny egress allow-list / DLP obligation }
  - { type: test,   what: A test proving exfiltration is blocked }
audit_questions:
  - Is outbound egress restricted to an allow-list by default-deny?
  - Is PII tokenized or redacted on egress?
maps_to: [soc2:CC6.1, hipaa:164.312(e)(1)]        # crosswalk (reuses controls.map)
security_signal:                # how an AsterGuard review auto-supplies evidence
  weakness_ids: [llm_cfg_egress_no_dlp, egress_unrestricted]
  satisfied_when: Applied egress allow-list + DLP obligation; canary held on egress.
```

## Method

1. **Connected (default):** call the MCP `controls.rubric(framework, version)` — the full, grounded,
   versioned catalog lives server-side (like the weakness registry and crosswalk). Reconcile each
   control's `maps_to` with `controls.map` so the crosswalk is one source of truth.
2. **Offline:** load the bundled seed pack `references/packs/<framework>.yaml`. These are representative
   **subsets**, not the full catalog — enough to run and demo offline; the MCP supersedes them when
   connected. Say so in the report when running from a seed pack.
3. Attach each control's `security_signal` so `evidence-judge` knows which graph findings/policies count.
4. Write `./.asterguard/compliance/rubric.<framework>.json`.

## Practical Guidance

- **One crosswalk:** never hand-roll framework mappings — derive `maps_to` from `controls.map`. A
  control satisfied under SOC 2 CC6.1 is evidence toward its HIPAA/ISO mapped clauses (surface it, let
  the judge decide per framework).
- **Version matters:** record the framework version (e.g. ISO 27001:2022); auditors care which revision.
- **Don't invent controls:** if a framework/version isn't available (no MCP, no pack), say so and stop —
  never fabricate control ids.

## Integration

- Consumes the framework choice from `compliance-auditor`; feeds the rubric to `evidence-judge`.
- Reuses the MCP `controls.map` crosswalk (same SSOT as `weakness-graph`).

## References

- [Rubric schema + the `controls.rubric` MCP contract](references/rubric-schema.md)
- Seed packs: `references/packs/{iso-27001,iso-9001,soc2,hipaa}.yaml`
