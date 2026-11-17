---
type: Persona
title: "Persona: Compliance Manager"
description: "Ensures agent deployments meet applicable frameworks (SOC 2, ISO 27001, HIPAA, NIST) by mapping agent weaknesses to controls, assessing control coverage/gaps, gathering evidence, and reporting compliance posture."
related:
  - compliance-auditor
  - control-rubric
  - evidence-collection
  - audit-report
  - agent-incident-report
  - post-incident-review
  - ciso
  - soc_manager
---
# Persona: Compliance Manager

## Overview

The Compliance Manager ensures agent deployments adhere to applicable laws, regulations, and standards (SOC 2, ISO 27001, HIPAA, PCI DSS, NIST CSF) and internal policy. For AI agents this means mapping agent **weaknesses to controls** via the crosswalk, assessing control design/operating effectiveness, gathering evidence from the engagement stream, managing audits, and reporting posture. Their goal is to minimize compliance risk and demonstrate due diligence over the agent estate.

## Responsibilities

*   **Requirement identification.** Identify applicable frameworks and interpret their control requirements for the agent deployment context.
*   **Control assessment & gap analysis.** Assess control coverage against requirements using `controls.map` (weakness→control crosswalk: NIST/800-53/HIPAA/ISO/SOC 2) and the `control-rubric`; identify gaps and drive remediation with Security Engineering.
*   **Policy & procedure.** Develop and maintain agent-security and data-privacy policies/procedures that meet compliance obligations.
*   **Audit management.** Coordinate internal/external audits (`compliance-auditor`); gather and organize evidence (`evidence-collection`), liaise with auditors, and track remediation of findings.
*   **Risk assessment.** Participate in agent-security risk assessments to surface compliance-related risk and confirm controls are in place.
*   **Reporting & metrics.** Track compliance status and control coverage; report posture, risk, and remediation to management (`audit-report`).
*   **Training & currency.** Contribute to awareness of agent-security compliance responsibilities; track regulatory change.

## Skills

*   Strong grasp of major frameworks (SOC 2, ISO 27001, HIPAA, PCI DSS, NIST CSF) applied to AI-agent systems.
*   Understands agent-security controls and the weakness→control crosswalk.
*   Audit process and control-assessment methodology; interprets regulatory language.
*   Strong policy writing and documentation; evidence management.
*   Cross-team collaboration and auditor communication.

## Tools (AsterVault surface)

Compliance Managers use the surface indirectly — to gather evidence and assess control effectiveness, not for operational tasks.

*   **Control & coverage:** `controls.map` (weakness→control crosswalk), `control-rubric` (scoring control adequacy), `registry.resolve` (weakness→control linkage).
*   **Evidence:** `evidence-collection` and `compliance-auditor` to assemble audit-ready evidence from the engagement event stream; `engagement.context` and `memory.recall` to show incident-response and remediation processes were followed.
*   **Posture reporting:** `audit-report`; consumes `risk.score` coverage, `agent-incident-report`, and `post-incident-review` as evidence of process.

Connected calls metered (`X-ARS-Token`, `audit_id`). Offline: assess against the local pack's crosswalk and locally recorded engagement evidence.

**Scope limitation.** Operational investigation/response is out of scope — consume outputs and documented procedures as evidence; escalate operational needs.

## Relevant Runbooks

Compliance Managers are primarily consumers of runbook outputs or use runbooks as documented procedure/evidence:

*   `compliance-auditor` / `evidence-collection` / `audit-report` — evidence→controls audit workflow.
*   `control-rubric` — assess control adequacy for a weakness/finding.
*   `cloud-agent-vuln-triage` output — evidence of vulnerability-management process.
*   `agent-incident-report` and engagement detail — evidence that incident-response procedures are followed; the `irp-*` family serves as documented procedure.
*   `post-incident-review` — evidence of lessons-learned/continuous-improvement process.
