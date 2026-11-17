---
type: Persona
title: "Agent-Security Personas"
description: "Index of the agent-security-ops personas that drive the AsterGuard runbook library, grouped by function — SOC, proactive, engineering, leadership, evaluation, and testing."
---
# Agent-Security Personas

Effective AI-agent security operations rely on a team of specialized roles, each driving a slice of the runbook library — *triage → investigate → hunt → respond → report → evaluate* for agent incidents (prompt injection, tool abuse, over-privilege, data exfil, agent-credential compromise, model supply chain). Each persona retargets its work to the **engagement + the security graph + the AsterVault gateway**, not a Chronicle/GTI/SOAR console. Understanding these personas tailors the runbooks, procedures, and gateway-tool interactions to each role's workflow.

## Organization by Function

### Agent-SOC
Day-to-day monitoring, triage, and investigation of agent findings and runtime alerts:
- **[Tier 1 Agent-SOC Analyst](./soc_analyst_tier_1.md)** — first-line triage of runtime alerts and scan findings.
- **[Tier 2 Agent-SOC Analyst](./soc_analyst_tier_2.md)** — escalated agent-incident investigation and guided hunts.
- **[Tier 3 Agent-SOC Analyst](./soc_analyst_tier_3.md)** — complex incidents, advanced hunts, detection authoring.
- **[Agent-SOC Manager](./soc_manager.md)** — orchestrates playbook execution and SOC effectiveness.

### Proactive Security
Finding agent threats before they become incidents:
- **[Agent Threat Hunter](./threat_hunter.md)** — hypothesis-driven hunts over the graph (over-privilege, injection exposure, exfil paths).
- **[Agentic CTI Researcher](./cti_researcher.md)** — weakness/TTP/pattern research via the knowledge surface + weakness registry.

### Security Engineering
Building and running the agent-security capability:
- **[Agent Detection Engineer](./detection_engineer.md)** — pack `.rule.yaml` threat-rule lifecycle.
- **[Agent Security Engineer](./security_engineer.md)** — gateway wiring, graph build, policy-as-code enforcement.
- **[Agent Incident Responder](./incident_responder.md)** — PICERL response to confirmed agent incidents.

### Leadership and Governance
Strategy, risk, and compliance over the agent estate:
- **[CISO](./ciso.md)** — agent-security strategy, ARS/DRS risk posture, oversight.
- **[Compliance Manager](./compliance_manager.md)** — weakness→control coverage, audit evidence, posture.

### Evaluation
- **[LLM Judge](./llm_judge.md)** — grades runbook executions (trajectory / schema / rubric / benchmark).

### Testing
- **[Agent Red Team](./red_team.md)** — authorized offensive testing (`behavioral-redteam`), dual-use discipline.

```{toctree}
:maxdepth: 1
:caption: All Personas:

personas
soc_analyst_tier_1
soc_analyst_tier_2
soc_analyst_tier_3
soc_manager
threat_hunter
cti_researcher
detection_engineer
security_engineer
incident_responder
ciso
compliance_manager
llm_judge
red_team
```
