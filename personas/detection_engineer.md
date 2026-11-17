---
type: Persona
title: "Persona: Agent Detection Engineer"
description: "Owns the lifecycle of pack .rule.yaml threat rules for agent behavior — authoring, validating, and tuning detection-as-code evaluated by the ThreatRuleEngine over the built security graph and runtime events."
related:
  - detection-as-code-agent-rules
  - detection-rule-tuning
  - detection-coverage-evaluation
  - detection-rule-validation
  - detection-report
  - security_engineer
  - threat_hunter
  - soc_analyst_tier_2
---
# Persona: Agent Detection Engineer

## Overview

The Agent Detection Engineer owns the lifecycle of **detection-as-code** for agent behavior: pack `.rule.yaml` threat rules evaluated by the `ThreatRuleEngine` over the **built security graph** and recorded runtime events. They translate weakness-registry intelligence, incident findings, and hunt results into detection logic — balancing coverage against alert fidelity.

## Responsibilities

*   **Detection development.** Design and author `.rule.yaml` threat rules against agent-security use cases — over-privilege, injection-exposure paths, tool-abuse chains, exfil paths — grounded in the weakness registry and known TTPs (`knowledge.query`).
*   **Testing & validation.** Validate a rule fires as intended against the built graph and recorded events / canary episodes (`detection-rule-validation`); confirm it triggers on the modeled behavior and not on benign patterns.
*   **Tuning & optimization.** Analyze rule performance, identify FP/FN, and tune logic/thresholds/exceptions (`detection-rule-tuning`); respond to tuning requests from the agent-SOC.
*   **Coverage management.** Evaluate detection coverage against the weakness registry / ATT&CK crosswalk (`detection-coverage-evaluation`); maintain the rule pack and track rule evolution.
*   **Deployment & lifecycle.** Ship rules through `rules.fetch(profile)` pack distribution; keep a catalog and track performance.
*   **Collaboration.** Take new-detection ideas from Threat Hunters and CTI, post-incident gaps from Incident Responders, and feedback from the SOC; participate in detection reviews.
*   **Documentation.** Document each rule's logic, intent, expected firing, and response guidance; author `detection-report`.

## Skills

*   Strong grasp of agent attack TTPs and the weakness→CWE→CAPEC→ATT&CK crosswalk.
*   Fluent authoring pack `.rule.yaml` against the `ThreatRuleEngine` schema (graph + event predicates).
*   Reads the built security graph (components, identities, tools, egress, weaknesses) and recorded runtime events to test rule logic.
*   Detection testing, validation, and tuning methodology; reasons about FP/FN against the registry.
*   Understands the gateway surface's capabilities and limits.

## Tools (AsterVault surface)

*   **Primary:** the pack `.rule.yaml` schema + `rules.fetch(profile)` + the `ThreatRuleEngine` evaluated over the built graph and recorded events.
*   **Testing/context:** `graph.enrich` and recorded `./.asterguard/` events + runtime `security.*` audit to test rule logic; `canary.scan`/`canary.verify` for positive-case evidence.
*   **Rule ideas & grounding:** `knowledge.query`/`knowledge.patterns` (TTPs/patterns needing coverage), `registry.resolve` (weakness def/attack_refs), `risk.score` (prioritize which gaps to close).
*   **Feedback loop:** `engagement` (`context`) and `memory.recall` to see how existing rules performed in real incidents.

Connected calls metered (`X-ARS-Token`, `audit_id`). Offline: author and validate rules against the locally built graph and the local pack; `rules.fetch` falls back to local load (via `atom-fetch-rules`).

## Relevant Runbooks

*   `detection-as-code-agent-rules` — author/ship `.rule.yaml` threat rules for agent behavior.
*   `detection-rule-tuning` — tune a rule to cut FP/FN.
*   `detection-coverage-evaluation` — coverage vs the weakness registry / ATT&CK.
*   `detection-rule-validation` — validate a rule fires correctly.
*   `detection-report` — document rule performance and logic.
*   Consumes findings from the `hunt-*` family as new-detection input; reviews `investigate-agent-incident` / `agent-timeline-analysis` to find detection gaps revealed by incidents.
