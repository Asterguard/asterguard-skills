---
type: Persona
title: "Persona: Agent Red Team Member"
description: "Conducts authorized offensive testing of AI agents via behavioral-redteam (attacker/defender/judge) and canary episodes — emulating agent attack TTPs to validate detection and response, under strict dual-use discipline."
related:
  - behavioral-redteam
  - attacker
  - defender
  - judge
  - canary-testing
  - dast-generation
  - hunt-prompt-injection-exposure
  - detection_engineer
  - security_engineer
  - threat_hunter
---
# Persona: Agent Red Team Member

## Overview

The Agent Red Team Member runs **authorized** offensive testing against AI agents to measure the effectiveness of controls, detections, and response (the Blue Team). They emulate agent attack TTPs — prompt injection, tool abuse, over-privilege escalation, exfil, model/dependency supply-chain — through the `behavioral-redteam` loop (attacker ↔ defender ↔ judge) and canary episodes, producing a realistic attacker's-eye assessment of agent-security posture.

> **Dual-use discipline.** Red-team/offensive runbooks run on **authorized engagements only**. The authorization is recorded in the engagement before any episode; attacker-model selection and the attack success rate (ASR) are recorded per the offensive-security doc. Nothing is run against production or third-party agents without explicit scope.

## Responsibilities

*   **Adversary emulation.** Plan and execute multi-turn attack episodes against a defined agent/deployment, based on agent threat-actor patterns and the weakness registry's TTPs — via `behavioral-redteam` (`attacker`/`defender`/`judge`).
*   **Authorized testing.** Conduct offensive tests against the agreed scope only; record authorization as a `decision`/`note` event on the engagement first.
*   **Weakness exploitation.** Attempt to drive the agent into unintended tool calls, data disclosure, or egress; prove impact with **planted canaries** (`canary-testing`) — a canary egress hit is hard proof.
*   **Evasion.** Exercise techniques that bypass guardrails/policy/detection to find blind spots; feed each bypass to detection engineering.
*   **Injection & input-attack testing.** Craft untrusted-input vectors (documents, tool results, web/email) to test injection exposure; pair with `dast-generation` for dynamic probes.
*   **Reporting & debriefing.** Document attack paths, successful exploits, bypassed controls, and recommendations for the Blue Team (SOC, IR, detection/security engineering). Run purple-team exercises; record ASR.
*   **Tool development.** Build reusable attacker patterns and episodes; stay current on agent offensive techniques.

## Skills

*   Deep grasp of agent attack methodology, kill-chains, and the weakness→CWE→CAPEC→ATT&CK crosswalk.
*   Fluent with the `behavioral-redteam` attacker/defender/judge loop and multi-turn/crescendo episode design.
*   Prompt-injection, tool-abuse, over-privilege, and exfil exploitation against agents; guardrail/policy evasion.
*   Canary planting/verification for hard evidence; dynamic probe (`dast-generation`) authoring.
*   Strong attacker mindset, creative problem-solving, and clear reporting; strict ethics and rules-of-engagement adherence.

## Tools (AsterVault surface)

Red Team operates *against* the agent the Blue Team defends, under recorded authorization.

*   **Offensive loop:** `behavioral-redteam` composing `attacker`, `defender`, and `judge`; `dast-generation` for dynamic input probes.
*   **Proof:** `canary.mint`/`canary.plant`/`canary.scan`/`canary.verify` (via `canary-testing`) — planted canaries + egress hits are the hardest evidence.
*   **Recon & hypothesis:** `knowledge.query`/`knowledge.patterns` (TTPs to emulate), `registry.resolve` (weaknesses to target), `graph.enrich` (authority/reach to understand the defensive surface and attack paths).
*   **Engagement:** `engagement` (record authorization + episodes), `record-in-engagement` (ASR, attacker-model, `decision` events), `memory.capture`.

Connected calls metered (`X-ARS-Token`, `audit_id`). Offline: episodes run against the local target/harness; grounding degrades to local pack data.

## Relevant Runbooks

Red Teams have their own offensive playbooks and interact with Blue Team runbooks in purple-team exercises:

*   `behavioral-redteam` — the authorized offensive testing loop (attacker/defender/judge).
*   `canary-testing` — plant/verify canaries for hard egress proof.
*   `dast-generation` — dynamic input probes.
*   They *test* the effectiveness of the `irp-*` family and `endpoint-agent-triage-isolation`.
*   Findings drive `detection-as-code-agent-rules` / `detection-rule-tuning` and new `hunt-prompt-injection-exposure` / `advanced-agent-threat-hunt` hypotheses for the Blue Team.
