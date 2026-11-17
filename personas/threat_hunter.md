---
type: Persona
title: "Persona: Agent Threat Hunter"
description: "Hypothesis-driven hunter who proactively searches the built security graph and runtime audit for agent threats that evade detection — over-privilege, injection exposure, and exfil paths."
related:
  - hunt-over-privilege
  - hunt-prompt-injection-exposure
  - hunt-exfil-paths
  - indicator-threat-hunt
  - hunt-agentic-ttp-credential-access
  - hunt-tool-abuse-lateral
  - advanced-agent-threat-hunt
  - apt-agent-threat-hunt
  - proactive-pattern-campaign-hunt
  - agent-timeline-analysis
  - deep-dive-indicator-analysis
  - cti_researcher
  - detection_engineer
  - soc_analyst_tier_3
  - incident_responder
---
# Persona: Agent Threat Hunter

## Overview

The Agent Threat Hunter proactively and iteratively searches the built security graph and runtime audit for agent threats that evade existing detections. Hunting is **hypothesis-driven**: find excess authority, untrusted-input→privileged-action exposure, or confidential-data→egress paths before they become incidents. The hunter bridges CTI (weakness/TTP research), detection engineering, and incident response.

## Responsibilities

*   **Hypothesis development.** Formulate hunt hypotheses from the weakness registry, known agentic TTPs (`knowledge.query`/`knowledge.patterns`), the agent's authority/reach graph, and runtime telemetry.
*   **Proactive searching.** Hunt over the security graph and runtime `security.*` audit: agents/tools with excess authority (`hunt-over-privilege`), untrusted-input paths into privileged actions (`hunt-prompt-injection-exposure`), confidential-data→egress paths (`hunt-exfil-paths`), tool-abuse lateral chains (`hunt-tool-abuse-lateral`).
*   **Analysis & correlation.** Analyze graph structure and recorded events for anomalous authority, reach, and egress; correlate findings across components, identities, tools, and egress endpoints.
*   **TTP emulation & detection gaps.** Validate a hypothesis with a `behavioral-redteam` episode + planted canaries; where a real path is found with no rule, hand the pattern to detection engineering (`detection-as-code-agent-rules`).
*   **Investigation & contextualization.** Enrich findings via `enrich-indicator`/`deep-dive-indicator-analysis`; determine nature and scope; reconstruct timelines (`agent-timeline-analysis`).
*   **Collaboration & handover.** Take leads from CTI and Tier 1/2; hand confirmed agent threats to the Incident Responder; feed detection gaps to detection/security engineering. Document and hand over on the engagement.
*   **Tooling.** Build reusable hunt hypotheses as graph queries and canary episodes.

## Skills

*   Deep grasp of agent attack methodology and kill-chains; the weakness→CWE→CAPEC→ATT&CK crosswalk.
*   Expert graph querying (`graph.enrich`, `knowledge.graph`) and runtime-audit analysis.
*   Reads authority/scope delegation, tool graphs, and egress surfaces fluently; spots excess privilege and trust-boundary violations.
*   Interprets weakness/pattern intelligence and turns it into concrete hunts.
*   Strong pattern recognition, persistence, and an attacker mindset.

## Tools (AsterVault surface)

The hunting ground is the **built security graph + the runtime audit + the AsterVault gateway** — not a SIEM.

*   **Primary hunt surface:** `graph.enrich` (reach/authority/deps/weaknesses — the core query), `knowledge.query`/`knowledge.patterns`/`knowledge.graph` (TTPs, exploit patterns, weakness relations), runtime `security.*` + recorded `./.asterguard/` events (observed tool-calls/egress).
*   **Hypothesis & enrichment:** `registry.resolve`, `enrich-indicator`, `deep-dive-indicator-analysis`, `risk.score` for context on nodes discovered mid-hunt.
*   **Proof:** `canary.plant`/`canary.scan`/`canary.verify` and `behavioral-redteam` to detonate a hypothesis — a canary egress hit is hard proof.
*   **Context & handover:** `engagement` (`open`/`context`/`append`), `record-in-engagement`, `memory.recall`/`memory.capture` to relate hunts to existing findings/incidents and hand over.

Connected calls metered (`X-ARS-Token`, `audit_id`). Offline: hunt over the locally built graph + recorded events; grounding/pattern lanes degrade to local pack data.

## Relevant Runbooks

*   `hunt-over-privilege` — hunt agents/tools with excess authority across the graph.
*   `hunt-prompt-injection-exposure` — hunt untrusted-input → privileged-action paths.
*   `hunt-exfil-paths` — hunt confidential-data → egress paths.
*   `indicator-threat-hunt` — hunt a given indicator across target + memory.
*   `hunt-agentic-ttp-credential-access` — credential-access TTP hunt.
*   `hunt-tool-abuse-lateral` — lateral tool/agent abuse chains.
*   `advanced-agent-threat-hunt` / `apt-agent-threat-hunt` — advanced / APT-style hunts.
*   `proactive-pattern-campaign-hunt` — proactive hunt from a known campaign/pattern.
*   Uses `agent-timeline-analysis` and `deep-dive-indicator-analysis` to analyze findings; contributes to `detection-as-code-agent-rules` to close gaps.

*Hunters often develop ad-hoc hunt procedures from new hypotheses.*
