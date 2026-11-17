---
type: Persona
title: "Agent-Security Personas"
description: "Overview of the agent-security-ops personas in this directory — their responsibilities, skills, AsterVault gateway tooling, and the runbook skills each drives — grouped by function."
related:
  - soc_analyst_tier_1
  - soc_analyst_tier_2
  - soc_analyst_tier_3
  - soc_manager
  - threat_hunter
  - cti_researcher
  - detection_engineer
  - security_engineer
  - incident_responder
  - ciso
  - compliance_manager
  - llm_judge
  - red_team
---
# Agent-Security Personas

This directory describes the roles that drive the AsterGuard agent-security-ops runbook library — each persona's responsibilities, skills, the **AsterVault gateway** surface it uses (`registry.*`, `graph.enrich`, `risk.score`, `controls.map`, `knowledge.*`, `memory.*`, `canary.*`, `policy.apply`, `rules.fetch`, runtime `security.*`), and the runbook skills it owns or consumes. The "case" is always the long-lived **engagement**; findings/decisions flow to shared memory; connected calls are metered (`X-ARS-Token`) and return an `audit_id`.

## Agent-SOC
*   [Tier 1 Agent-SOC Analyst](./soc_analyst_tier_1.md) — first-line triage of runtime alerts and scan findings; escalate or close.
*   [Tier 2 Agent-SOC Analyst](./soc_analyst_tier_2.md) — deep investigation, timeline reconstruction, guided hunts.
*   [Tier 3 Agent-SOC Analyst](./soc_analyst_tier_3.md) — complex incidents, advanced multi-hypothesis hunts, detection authoring.
*   [Agent-SOC Manager](./soc_manager.md) — orchestrates `playbook-runner` over the `security-operations` playbooks; tracks ARS/DRS metrics.

## Proactive Security
*   [Agent Threat Hunter](./threat_hunter.md) — hypothesis-driven hunts over the graph: over-privilege, injection exposure, exfil paths.
*   [Agentic CTI Researcher](./cti_researcher.md) — weakness/TTP/pattern research via `knowledge.*` + the weakness registry.

## Security Engineering
*   [Agent Detection Engineer](./detection_engineer.md) — authors/validates/tunes pack `.rule.yaml` threat rules over the built graph.
*   [Agent Security Engineer](./security_engineer.md) — gateway wiring, graph build, policy-as-code enforcement, detection automation.
*   [Agent Incident Responder](./incident_responder.md) — PICERL containment/eradication/recovery for confirmed agent incidents.

## Leadership and Governance
*   [CISO](./ciso.md) — agent-security strategy, ARS/DRS risk posture, detection-lifecycle oversight.
*   [Compliance Manager](./compliance_manager.md) — weakness→control coverage, audit evidence, compliance posture.

## Evaluation
*   [LLM Judge](./llm_judge.md) — grades runbook executions against the `evals` rubrics via `security-judge`.

## Testing
*   [Agent Red Team](./red_team.md) — authorized offensive testing via `behavioral-redteam` (attacker/defender/judge), under dual-use discipline.
