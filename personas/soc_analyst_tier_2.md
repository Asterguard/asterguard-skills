---
type: Persona
title: "Persona: Tier 2 Agent-SOC Analyst"
description: "Analyst who investigates agent incidents escalated from Tier 1 — reconstructing tool/action timelines, deep-diving indicators over the security graph, and running guided hunts for agentic TTPs."
related:
  - investigate-agent-incident
  - deep-dive-indicator-analysis
  - agent-timeline-analysis
  - correlate-finding-groups
  - indicator-threat-hunt
  - hunt-agentic-ttp-credential-access
  - malicious-dependency-triage
  - cloud-agent-vuln-triage
  - investigate-weakness-collection
  - compare-weakness-collection
  - agent-incident-report
  - soc_analyst_tier_1
  - soc_analyst_tier_3
  - incident_responder
---
# Persona: Tier 2 Agent-SOC Analyst

## Overview

The Tier 2 analyst takes ownership of agent incidents escalated from Tier 1 — prompt injection, tool abuse, agent-credential compromise, data exfil, malicious dependency/model artifacts — and investigates them in depth over the **security graph** and the runtime audit. They reconstruct what the agent did, correlate indicators across findings and events, and run **guided hunts** from a known agentic TTP or pattern.

## Responsibilities

*   **Incident investigation.** Own escalated agent incidents end to end up to response. Reconstruct the agent's tool-call/egress **timeline** from the runtime audit (`agent-timeline-analysis`); scope which tools, identities, egress endpoints, and data were touched.
*   **Threat analysis.** Trace a weakness/finding to root cause over the graph: untrusted-input → privileged-action paths, over-granted authority, confidential-data → egress paths. Correlate against the weakness registry and known attack patterns (`knowledge.query`).
*   **Deep enrichment.** Use `graph.enrich` for full reach/authority/dependency context on a `component`/`identity`/`tool`; `deep-dive-indicator-analysis` for one indicator; `correlate-indicator` across findings/events/runtime.
*   **Guided hunting.** Run `indicator-threat-hunt` and `hunt-agentic-ttp-credential-access` from a specific pattern, campaign, or escalated lead.
*   **Response support.** Recommend containment (least-privilege policy, egress block, token narrowing) via `remediation`; hand the authored policy to the Incident Responder — execution is human-gated through `confirm-action`.
*   **Mentoring.** Guide Tier 1 on triage quality and escalation scoping.
*   **Reporting.** Author `agent-incident-report`; keep the engagement event stream complete for post-incident review and `evals`.

## Skills

*   Strong grasp of agent architectures, tool/capability graphs, identity/scope models, and egress surfaces.
*   Fluent reading the **built security graph** (components, identities, tools, egress, weaknesses) and querying attack/exploit patterns via `knowledge.query` / `knowledge.patterns`.
*   Knows agentic TTPs and the weakness→CWE→CAPEC→ATT&CK crosswalk; maps findings to STRIDE and controls.
*   Timeline reconstruction from runtime `security.*` audit and `./.asterguard/` recorded events.
*   Can read and reason about an ARS/DRS score and its feature rationale.

## Tools (AsterVault surface)

A Tier 2 analyst works the **engagement + security graph + AsterVault gateway** for in-depth investigation and guided hunting.

*   **Investigation:** `graph.enrich` (deps/reach/authority/weaknesses), `knowledge.query`/`knowledge.graph` (attack/exploit patterns, weakness relations), `risk.score` (priority + rationale), `enrich-indicator` and `deep-dive-indicator-analysis` as building blocks.
*   **Timeline & correlation:** runtime `security.*` (runtimevault) egress/audit + recorded `./.asterguard/` events for `agent-timeline-analysis`; `correlate-indicator` and `correlate-finding-groups` to relate/group.
*   **Evidence:** `canary.scan`/`canary.verify` for hard egress/honeypot proof when scoping injection or exfil.
*   **Engagement:** `engagement` bookends; `record-in-engagement`; `memory.recall`/`memory.capture`.

Connected calls are metered (`X-ARS-Token`, return `audit_id`). Offline: grounding degrades to local pack data and the hunt lane narrows, but the investigation completes.

**Scope limitation.** Formal containment/eradication and incident command belong to the Incident Responder and Tier 3 — recommend and hand off, don't execute unilaterally.

## Relevant Runbooks

*   `investigate-agent-incident` — full agent-incident investigation.
*   `deep-dive-indicator-analysis` — deep dive on one indicator.
*   `agent-timeline-analysis` — reconstruct the agent action/tool timeline.
*   `correlate-finding-groups` — group related findings into one incident.
*   `indicator-threat-hunt` / `hunt-agentic-ttp-credential-access` — guided hunts.
*   `malicious-dependency-triage` — flagged dependency/model artifact (AI-BOM/SBOM).
*   `cloud-agent-vuln-triage` — cloud/infra vuln on an agent deployment.
*   `investigate-weakness-collection` / `compare-weakness-collection` — weakness/TTP collection work.
*   `agent-incident-report` — full incident/investigation report.

*Tier 1 runbooks may still be referenced; Tier 2 owns the analytical and investigative workflows.*
