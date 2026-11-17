---
type: Persona
title: "Persona: Chief Information Security Officer (CISO)"
description: "Senior executive who owns agent-security strategy, governance, and risk — setting the ARS/DRS risk posture, overseeing the agent-SOC and detection lifecycle, and aligning agent-security initiatives with business objectives."
related:
  - risk-report
  - detection-coverage-evaluation
  - agent-incident-report
  - post-incident-review
  - evals
  - soc_manager
  - compliance_manager
---
# Persona: Chief Information Security Officer (CISO)

## Overview

The CISO owns the enterprise strategy, governance, and risk program for **AI-agent security**. They set the agent-security vision, govern the ARS/DRS risk posture across the agent portfolio, oversee the agent-SOC and the detection lifecycle, and align agent-security initiatives with business objectives. They consume aggregated outputs; they do not run operational tooling.

## Responsibilities

*   **Strategy & governance.** Define and maintain the agent-security strategy, governance framework, and policy — including the risk appetite expressed as ARS/DRS thresholds and the gate posture (e.g. `c_fn:c_fp` cost ratio).
*   **Risk management.** Lead the agent-security risk program: identify, assess, and prioritize risk across agents/deployments using the portfolio ARS/DRS picture; drive mitigation.
*   **Operations oversight.** Provide strategic direction to the agent-SOC — triage, investigation, response, hunting, detection engineering. Own the **detection lifecycle**: ensure coverage review (`detection-coverage-evaluation`) and effectiveness metrics (`evals`) occur.
*   **Compliance & audit.** Ensure agent-security meets applicable regulation/standards (NIST, ISO 27001, SOC 2, HIPAA); oversee audits with the Compliance Manager.
*   **Budget & resources.** Own the agent-security budget across people, process, and the gateway/platform.
*   **Stakeholder communication.** Communicate agent-security posture, risk, and initiatives to executive leadership and the board; foster a security-aware culture around agent deployment.
*   **Incident leadership.** Provide strategic leadership during major agent incidents.
*   **Architecture.** Ensure security-by-design is embedded in the agent development and deployment lifecycle (least-privilege, provenance, canaries).

## Skills

*   Leadership, strategic planning, and governance; strong business acumen aligning agent-security to objectives.
*   Deep understanding of security frameworks (NIST CSF, ISO 27001, SOC 2) and risk methodology, applied to AI agents.
*   Broad knowledge of agent-security domains: injection, tool abuse, over-privilege, exfil, identity, model supply chain.
*   Fluent reading ARS/DRS risk indices, control-coverage, and `evals` effectiveness metrics at a portfolio altitude.
*   Excellent executive communication; crisis management and incident command.

## Tools (AsterVault surface)

CISOs interact at the **reporting and posture** altitude, reviewing aggregated outputs rather than operating tools directly.

*   **Risk & posture:** `risk.score` roll-ups (portfolio ARS/DRS), `controls.map` coverage, `graph.enrich` summaries for blast-radius context.
*   **Reports consumed:** `risk-report`, `agent-incident-report`, `post-incident-review`, `detection-coverage-evaluation`, and `evals` scorecards.
*   **Governance:** reviews the engagement event stream (`engagement.context`) for operational tempo and major events.

## Relevant Runbooks

CISOs care about the effectiveness, efficiency, and strategic alignment of the runbooks, not their execution:

*   Review outcomes/reports from the `irp-*` family and `post-incident-review` to gauge incident impact and response effectiveness.
*   Assess value from the `hunt-*` family to judge proactive agent-defense capability.
*   Oversee the detection lifecycle (`detection-as-code-agent-rules`, `detection-coverage-evaluation`) and its metrics.
*   Use `risk-report` and `evals` scorecards for portfolio risk posture and runbook-quality assurance.
*   Ensure runbooks align with policy, compliance, and strategic objectives.
