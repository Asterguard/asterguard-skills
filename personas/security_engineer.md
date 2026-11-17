---
type: Persona
title: "Persona: Agent Security Engineer"
description: "Designs and maintains the agent-security posture — the AsterVault gateway wiring, the security-graph build, policy-as-code enforcement (egress allowlists, scoped identity, OPA/Cedar PDP), and detection automation."
related:
  - detection-as-code-agent-rules
  - detection-rule-tuning
  - cloud-agent-vuln-triage
  - contain-indicator
  - remediation
  - detection_engineer
  - soc_manager
  - ciso
---
# Persona: Agent Security Engineer

## Overview

The Agent Security Engineer designs, implements, and maintains the agent-security infrastructure: the AsterVault gateway wiring, the **security-graph build** (scan → ingest → enrich), **policy-as-code** enforcement at the gateway/PDP (egress allowlists, SPIFFE/IAM scoped identity, OPA/Cedar), detection automation, and the metering/audit lanes. Their goal is a robust, least-privilege, efficient agent-security posture.

## Responsibilities

*   **Gateway & pipeline management.** Deploy, configure, and maintain the gateway surface (grounding, metering, canary/audit) and the scan→graph pipeline; ensure scanners, ingest, and enrichment produce a sound security graph.
*   **Detection engineering.** Develop, test, tune, and deploy `.rule.yaml` detection content (`detection-as-code-agent-rules`, `detection-rule-tuning`) and keep the pack current (shared with the Detection Engineer persona).
*   **Policy-as-code & enforcement.** Author and manage least-privilege policy — egress allowlists, scoped tokens/SPIFFE identity, OPA/Cedar rules at the PDP — via `remediation` + `policy.apply`; this is how containment is realized (`contain-indicator`), always human-gated.
*   **Automation & integration.** Build the `security-operations` playbooks and wire `playbook-runner` orchestration; automate scan/grounding/metering so runs are reproducible and audited.
*   **Agent-deployment security.** Harden agent runtimes and their cloud/infra; act on `cloud-agent-vuln-triage` output by tuning controls or implementing remediation.
*   **Telemetry management.** Ensure runtime `security.*` egress/audit, recorded `./.asterguard/` events, and canary signals are ingested and usable for detection and investigation.
*   **Collaboration.** Work with the SOC, Incident Responders, Threat Hunters, and agent/application owners so the gateway and policy meet operational needs.

## Skills

*   Strong grasp of agent-security architecture: tool/capability graphs, identity/scope delegation, egress surfaces, model/dependency supply chain.
*   Hands-on with the AsterVault gateway surface, the scan→graph pipeline, and the engagement/event model.
*   Policy-as-code fluency: egress allowlists, SPIFFE/IAM, OPA/Cedar, a PDP; designs least-privilege enforcement.
*   Authors `.rule.yaml` detection content; understands FP/FN tradeoffs.
*   Automation/IaC and integration; troubleshooting the pipeline and metering.

## Tools (AsterVault surface)

*   **Policy & enforcement:** `policy.apply` + `remediation` (least-privilege policy, egress allowlist, scoped identity, OPA/Cedar/PDP); `confirm-action` gating; runtime `security.*` for enforcement.
*   **Detection:** `rules.fetch(profile)` + `.rule.yaml` + the `ThreatRuleEngine`.
*   **Pipeline & grounding:** `scan.plan`, `graph.enrich`, `registry.resolve`, `controls.map`, `risk.score`; `canary.mint`/`canary.plant`/`canary.scan`/`canary.verify` for the egress-verification lane.
*   **Orchestration:** `playbook-runner` + the `security-operations` playbooks; `ars-token` for metering wiring.

Connected calls metered (`X-ARS-Token`, `audit_id`). Offline: policy is emitted as advisory artifacts (not auto-applied) and detection is authored/validated against the local pack.

## Relevant Runbooks

*   `detection-as-code-agent-rules` / `detection-rule-tuning` — detection content lifecycle.
*   `remediation` — least-privilege policy-as-code emission.
*   `contain-indicator` — containment via egress block / scoped policy (human-gated).
*   `cloud-agent-vuln-triage` — act on cloud/infra vulns of agent deployments.
*   Refines/automates steps inside `investigate-agent-incident` and the `hunt-*` family by improving the pipeline and telemetry; uses investigation findings to close detection/logging gaps.
