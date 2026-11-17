---
type: Persona
title: "Persona: Agent Incident Responder (IR)"
description: "Manages end-to-end response to confirmed agent incidents — prompt injection, tool-abuse/RCE, agent-credential compromise, data exfil, model supply chain — through PICERL containment, eradication, and recovery."
related:
  - irp-prompt-injection
  - irp-agent-credential-compromise
  - irp-tool-abuse-rce
  - irp-data-exfil-via-agent
  - irp-model-supply-chain
  - contain-indicator
  - endpoint-agent-triage-isolation
  - agent-timeline-analysis
  - agent-incident-report
  - post-incident-review
  - soc_analyst_tier_2
  - soc_analyst_tier_3
  - threat_hunter
---
# Persona: Agent Incident Responder (IR)

## Overview

The Agent Incident Responder manages the response to confirmed agent incidents — prompt injection, tool abuse / code-exec, agent-credential compromise, data exfiltration through an agent, poisoned model/dependency supply chain — from identification through containment, eradication, recovery, and lessons-learned. They coordinate across personas, execute **human-gated** response actions, and minimize impact while restoring the agent to a trusted, least-privilege configuration. Response follows **PICERL**.

## Responsibilities

*   **Incident management.** Lead and coordinate response for confirmed agent incidents, driving the matching `irp-*` runbook; the case is the long-lived **engagement**.
*   **Triage & analysis.** Confirm validity and scope; reconstruct the agent's tool-call/egress **timeline** under the attacker's influence (`agent-timeline-analysis`); establish root cause and blast radius over the authority/reach graph.
*   **Containment.** Cut the abused authority — block the egress, revoke/narrow the agent token/identity, quarantine the poisoned context/source, isolate the runtime (`endpoint-agent-triage-isolation`) — each via `contain-indicator` → `confirm-action` → `policy.apply` / runtime `security.*`, recorded as a `decision` event.
*   **Eradication.** Remove the injection vector / malicious dependency / poisoned memory and any planted persistence (altered instructions, poisoned long-term memory).
*   **Recovery.** Restore the trusted system prompt + least-privilege policy (`remediation`); verify with a fresh canary run that the attack path no longer holds.
*   **Evidence & coordination.** Preserve the runtime audit and canary evidence; coordinate handoffs with Tier 2/3, hunters, and engineering.
*   **Communication & reporting.** Update stakeholders during the incident; author the post-incident report (`agent-incident-report`, naming the runbook used) and run `post-incident-review`.
*   **Playbook improvement.** Execute the `irp-*` playbooks and refine them from incident experience; ship a detection rule so the pattern is caught next time.

## Skills

*   Strong command of **PICERL** applied to agents.
*   Reconstructs agent action/tool timelines from runtime `security.*` audit and recorded events.
*   Knows agent attack vectors, persistence (poisoned memory/instructions), and least-privilege containment (egress allowlist, scoped identity, policy-as-code).
*   Decisive under pressure; disciplined about human-gated, auditable actions (dual-use).
*   Strong coordination, communication, and documentation on the engagement.

## Tools (AsterVault surface)

*   **Containment & recovery:** `contain-indicator`, `confirm-action`, `remediation`, `policy.apply`, runtime `security.*` (egress block, token revoke/narrow, runtime isolate).
*   **Scope & evidence:** `graph.enrich` (authority/reach of the abused path), `agent-timeline-analysis` over the runtime audit, `canary.scan`/`canary.verify` (hard proof + recovery check), `knowledge.query` (known attack patterns).
*   **Engagement:** `engagement` bookends, `record-in-engagement` (`decision` events + `audit_id`), `memory.recall`/`memory.capture`.

Connected calls metered (`X-ARS-Token`, `audit_id`). Offline: containment is advisory (policy emitted, not auto-applied) and canary re-verification is noted pending; the response still runs. Connected: full containment via `policy.apply`/`security.*`, metered, with canary verification.

## Relevant Runbooks

*   `irp-prompt-injection` — prompt-injection incident (PICERL).
*   `irp-agent-credential-compromise` — compromised agent identity/token.
*   `irp-tool-abuse-rce` — tool abuse / code-exec via an agent.
*   `irp-data-exfil-via-agent` — data exfiltration through an agent.
*   `irp-model-supply-chain` — poisoned model/dependency supply-chain incident.
*   `contain-indicator` / `endpoint-agent-triage-isolation` — containment + runtime isolation.
*   `agent-timeline-analysis` — reconstruct the influenced timeline.
*   `agent-incident-report` / `post-incident-review` — reporting and lessons-learned.

May leverage `hunt-*` findings when an incident arises from a hunt.
