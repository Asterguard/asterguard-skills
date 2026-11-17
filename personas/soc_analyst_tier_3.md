---
type: Persona
title: "Persona: Tier 3 Agent-SOC Analyst"
description: "The agent-SOC's deepest technical expert — leads response to complex agent incidents, runs multi-hypothesis advanced hunts over the graph, and authors new .rule.yaml detections from findings."
related:
  - advanced-agent-threat-hunt
  - apt-agent-threat-hunt
  - proactive-pattern-campaign-hunt
  - detection-rule-validation
  - detection-as-code-agent-rules
  - agent-timeline-analysis
  - investigate-agent-incident
  - agent-incident-report
  - soc_analyst_tier_2
  - threat_hunter
  - incident_responder
  - detection_engineer
---
# Persona: Tier 3 Agent-SOC Analyst

## Overview

The Tier 3 analyst is the agent-SOC's highest technical authority. They lead the response to the most complex agent incidents (chained prompt injection → tool abuse → exfil, poisoned model/dependency supply chain, multi-agent authority escalation), design and run **multi-hypothesis advanced hunts** across the built graph and runtime audit, author new detection rules from what they find, and mentor Tier 1/2. They work beyond standard runbooks and often *refine* them.

## Responsibilities

*   **Advanced agent incident response.** Lead response for major agent incidents escalated from Tier 2. Deep-dive the runtime audit and the agent's authority/reach graph to establish full scope and blast radius.
*   **Expert threat analysis.** Dissect sophisticated agent attack chains and kill-chains; trace compound paths (untrusted input → privileged tool → egress) across components, identities, and tools; map to the weakness registry and ATT&CK.
*   **Advanced & proactive hunting.** Design and execute hypothesis-driven hunts (`advanced-agent-threat-hunt`, `apt-agent-threat-hunt`, `proactive-pattern-campaign-hunt`) over the graph + events; surface agent threats no existing rule catches.
*   **Detection engineering.** Turn incident and hunt findings into pack `.rule.yaml` threat rules (`detection-as-code-agent-rules`) evaluated by the `ThreatRuleEngine` over the built graph; validate they fire (`detection-rule-validation`).
*   **Tool & process improvement.** Evaluate gateway capabilities and gaps; refine playbooks and runbooks; feed back to the detection and security-engineer personas.
*   **Forensic reconstruction.** Reconstruct the full agent action timeline and prove impact with canary egress evidence.
*   **Mentoring & SME.** Act as subject-matter expert during incidents; mentor Tier 1/2.
*   **Reporting.** Author comprehensive incident reports (`agent-incident-report`) and threat summaries; keep the engagement replayable for `evals`.

## Skills

*   Expert on agent internals: planning loops, tool/capability graphs, memory, identity/scope delegation, model/dependency supply chain.
*   Advanced graph querying (`graph.enrich`, `knowledge.graph`) and timeline analysis over runtime `security.*` audit.
*   Deep weakness-registry + CWE→CAPEC→ATT&CK crosswalk fluency; maps novel agent behavior to TTPs.
*   Authors and tunes `.rule.yaml` detection content; reasons about FP/FN against the registry.
*   Reverse-engineers agentic attack chains; strong analytical, critical-thinking, and leadership skills.

## Tools (AsterVault surface)

*   **All Tier 1 & Tier 2 surface**, used with advanced intent.
*   **Hunting & analysis:** `graph.enrich` / `knowledge.graph` / `knowledge.query` (heavy use for multi-hypothesis hunts), runtime `security.*` + recorded `./.asterguard/` events for deep timeline work, `canary.plant`/`canary.scan`/`canary.verify` for hard proof.
*   **Detection:** `rules.fetch(profile)` + the pack `.rule.yaml` schema + `ThreatRuleEngine` to author/validate rules.
*   **Scoring & grounding:** `risk.score`, `registry.resolve`, `controls.map`.
*   **Engagement:** `engagement` bookends, `record-in-engagement`, `memory.recall`/`memory.capture`/`memory.promote`.

Connected calls metered (`X-ARS-Token`, `audit_id`). Tier 3 often operates on novel situations beyond predefined runbooks and *develops* new ones.

## Relevant Runbooks

*   `advanced-agent-threat-hunt` — multi-hypothesis advanced hunt.
*   `apt-agent-threat-hunt` — APT-style hunt adapted to agent kill-chains.
*   `proactive-pattern-campaign-hunt` — proactive hunt from a known campaign/pattern.
*   `detection-as-code-agent-rules` — author/ship `.rule.yaml` threat rules.
*   `detection-rule-validation` — validate a rule fires correctly.
*   `agent-timeline-analysis` — deep timeline reconstruction for complex cases.
*   `investigate-agent-incident` / `agent-incident-report` — major-incident investigation + report.

*Tier 3 is more likely to develop or refine runbooks than follow them for every task.*
