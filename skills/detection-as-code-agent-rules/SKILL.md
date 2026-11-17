---
name: detection-as-code-agent-rules
description: Use when authoring, reviewing, and shipping a vendor-pack `.rule.yaml` threat rule for agent behavior — detection-as-code evaluated over the built security graph and recorded events by the ThreatRuleEngine, git-backed and CI-validated — turning a confirmed hunt gap or incident pattern into a reusable, grounded detection resolved to a weakness id.
---

# Detection: Author Agent `.rule.yaml` Threat Rules

Detection-as-code for agent security. A detection here is **not** a SIEM/YARA-L rule — it is a
vendor-pack `.rule.yaml` **threat rule** that the `ThreatRuleEngine` evaluates over the built security
graph and recorded agent events (the same engine `playbook-runner` lenses invoke). This runbook turns
a confirmed hunt gap, incident pattern, or weakness into a rule: author it, ground it to a weakness
id, validate it fires, review it, and ship it through the git-backed, CI-validated pack flow.

## When to Activate

- A hunt (`hunt-*`) or IRP confirmed a behavior with no covering threat-rule and handed over a
  `${DETECTION_GAP}`.
- A new weakness/TTP in the registry needs machine detection over the graph/events.
- `detection-coverage-evaluation` flagged a gap to close.

## Objective

Produce a reviewed, CI-validated `.rule.yaml` threat rule that fires on the target behavior over the
graph/events, is resolved to its weakness id, and is merged into the pack so `playbook-runner` /
`ThreatRuleEngine` evaluate it on every run.

## Scope

Covers: authoring + grounding + local validation + review + ship of one agent threat rule. Excludes:
false-positive/negative tuning (`detection-rule-tuning`), fire-correctness test design
(`detection-rule-validation`), coverage gap-finding (`detection-coverage-evaluation`), and the hunting
that discovers the behavior (`hunt-*`).

## Inputs

- `${DETECTION_GAP}`: the behavior to detect `{description, evidence, source hunt/incident}`. *Source:*
  a `hunt-*` / IRP handoff or `detection-coverage-evaluation`.
- `${WEAKNESS_ID}` (optional): the registry weakness this rule grounds to. *Source:* `registry.resolve`
  if not supplied.
- `${PACK}`: the vendor pack + axis/category the rule belongs in. *Source:* pack layout.
- `${EXAMPLE_EVENTS}` (optional): known-positive/negative event rows for local validation. *Source:*
  the hunt's evidence / `./.asterguard/events`.

## Outputs

- `${RULE_FILE}`: the `.rule.yaml` (match over graph nodes/edges + recorded events, severity,
  `weakness_id`, metadata) written under the pack.
- `${VALIDATION_RESULT}`: `detection-rule-validation` result (fires on positives, silent on negatives).
- `${REVIEW_STATUS}`: human review outcome (`confirm-action`).
- `${SHIP_STATUS}`: branch/PR + CI result; merged or blocked.
- `${STATUS}`: ["Success" | "Partial" | "Failure"].

## Tools

- **Gateway (connected, metered — `X-ARS-Token`, record `audit_id`):** `registry.resolve` (ground the
  rule to a weakness id), `rules.fetch(profile)` (existing pack rules — avoid duplicates), `controls.map`
  (the control the rule supports), `knowledge.query` (the behavior's canonical pattern).
- **Client-side:** author the `.rule.yaml`; run the `ThreatRuleEngine` locally over the graph +
  `./.asterguard/events` / `${EXAMPLE_EVENTS}`; shape the PR.
- **Sibling skills:** `engagement`, `atom-fetch-rules`, `atom-resolve-weakness`, `detection-rule-validation`,
  `confirm-action` (review gate), `record-in-engagement`; `weakness-graph` for the weakness↔component link.

## Workflow Steps & Diagram

1. **Open engagement.** `engagement.open(${TARGET or pack})` → context. Connected: ensure the ARS token.
2. **Ground the behavior.** `atom-resolve-weakness`(`registry.resolve`) → `${WEAKNESS_ID}`;
   `knowledge.query` the canonical pattern; `controls.map` the control the rule supports.
3. **Check for duplicates.** `atom-fetch-rules`(`rules.fetch`) the pack's existing rules — extend an
   existing rule rather than add a near-duplicate (mirror `weakness-graph`'s one-node discipline).
4. **Author the rule.** Write `${RULE_FILE}` as a `.rule.yaml`: a match over graph nodes/edges +
   recorded-event conditions (not a log query), with `severity`, `weakness_id`, and metadata, in the
   `${PACK}` axis/category.
5. **Validate locally.** `detection-rule-validation` runs the `ThreatRuleEngine` over the
   graph/`${EXAMPLE_EVENTS}`: must fire on known-positives, stay silent on known-negatives → `${VALIDATION_RESULT}`.
6. **Review (human-gated).** `confirm-action` — a reviewer approves the rule (grounding correct, scope
   right, no obvious FP) → recorded as a `decision`.
7. **Ship.** Commit to a branch, open the PR; CI validates syntax + fire-correctness; on green, merge →
   `${SHIP_STATUS}`. The merged rule is now evaluated by `playbook-runner` lenses.
8. **Record + checkpoint.** `record-in-engagement` the rule id + weakness id + ship status;
   `engagement.checkpoint`.

```mermaid
graph TD
    START([${DETECTION_GAP}]) --> OPEN["engagement.open"]
    OPEN --> GROUND["registry.resolve → ${WEAKNESS_ID}; knowledge.query pattern"]
    GROUND --> DUP["rules.fetch → de-dupe against pack"]
    DUP --> AUTHOR["author ${RULE_FILE} (.rule.yaml over graph + events)"]
    AUTHOR --> VAL["detection-rule-validation (ThreatRuleEngine)"]
    VAL --> OK{"fires on +, silent on −?"}
    OK -- "no" --> AUTHOR
    OK -- "yes" --> REVIEW["confirm-action (human review)"]
    REVIEW --> SHIP["branch + PR + CI validate → merge"]
    SHIP --> CP["record-in-engagement + checkpoint"]
```

## Decision Logic / Completion Criteria

- A rule ships only when it is **grounded** (resolved to a `weakness_id`), **validated** (fires on
  positives, silent on negatives via `detection-rule-validation`), **reviewed** (`confirm-action`), and
  **CI-green**.
- Prefer extending an existing pack rule over adding a near-duplicate; a generic lane label is not a
  rule identity (mirror `weakness-graph`).
- **Done when:** `${RULE_FILE}` is merged (or explicitly blocked with a reason), the engine evaluates
  it on the next run, and the engagement is checkpointed.

## Integration

- **Composes:** `atom-resolve-weakness`, `atom-fetch-rules`, `detection-rule-validation`,
  `confirm-action`, `record-in-engagement`, `weakness-graph`; `engagement` bookends.
- **Called by:** every `hunt-*` (gap handoff), the IRPs (lessons-learned rule), `detection-coverage-evaluation`;
  the shipped rule is consumed by `playbook-runner` / `ThreatRuleEngine` and reported by `detection-report`.
- **Offline:** author + run the engine locally over `./.asterguard/` graph/events and local pack rules;
  grounding (`registry.resolve`/`controls.map`) degrades to local pack data (mark controls `unresolved`,
  never invent an id); CI/merge is noted as pending. **Connected:** full grounding + `rules.fetch`
  de-dupe + metered CI, with `audit_id`s recorded.
