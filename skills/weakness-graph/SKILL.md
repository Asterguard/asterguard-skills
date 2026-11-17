---
name: weakness-graph
description: Build the weakness graph (WRG) — weakness classes linked to the components that manifest them, and each weakness mapped to the control that mitigates it. Ties CVEs, SAST/IaC/secret findings and agentic weaknesses to the data-flow and information-flow graphs. Use when a security engineer needs to know which components are weak, how a weakness becomes an attack path, and which control closes it.
---

# Weakness Graph (WRG)

Connect weaknesses to the things that have them and to the controls that fix them. This is the layer
that turns scattered findings into "this component manifests this weakness, which enables this flow,
and this control would stop it."

## When to Activate

- After `local-scan` (findings) and at least one of `data-flow` / `information-flow` (components).
- The engineer asks which components are weak, how a weakness chains into an attack path, or what
  control to apply.
- Mapping findings to a framework (OWASP-LLM, CWE, a compliance control family).

## Core Concepts

- A **weakness** node per distinct weakness class (`comp:weakness:`, `registry_id` + `cwe`/`owasp_llm`).
- A **`manifests`** edge from each component (function, mcp_tool, package, endpoint) to the weakness
  it carries — sourced from SAST/IaC/secret findings, CVE categories, and agentic weakness detection.
- Each weakness carries its **control** mapping (the crosswalk) in `meta.controls`.
- A weakness on a component that sits on an **information-flow path** escalates that flow's severity —
  cross-link, don't duplicate.

## Method

1. For each finding in `scan.json` + each cve in the SCA graph, call the AsterVault MCP tool
   `registry.resolve` to get its canonical `weakness_id`, severity, OWASP/CWE refs.
2. Emit one weakness node per resolved id; add `manifests` edges to the affected components.
3. Call `controls.map` for each weakness; set `meta.controls` from the response.
4. Cross-reference information-flow: if a weakness's component is on a violating flow, tag the flow
   with the weakness id and raise its priority.
5. Write into `./.asterguard/graph.json`.

## Practical Guidance

- **Resolution is server-side (low freedom):** the registry and crosswalk live in the AsterVault MCP
  gateway, not in this plugin — resolve per finding via `registry.resolve` / `controls.map`
  (`references/astervault-tools.md`). Never bundle or cache the knowledge locally.
- A generic lane label (CVE/IaC/secret/SAST) is not a weakness identity on its own — pass the
  finding's own identity (rule/check id, CWE) to `registry.resolve` so distinct weaknesses stay distinct.
- Prefer one comprehensive weakness node with many `manifests` edges over many near-duplicate nodes.
- If the gateway is unreachable, keep the structural node with its public CWE/OWASP and mark controls
  `unresolved` — never invent an id or a control citation.

## Added detectors & crosswalk

**Instruction / obfuscation / taint detectors.** Beyond code CWEs, the graph carries agent-specific
detector rules evaluated via the `ThreatRuleEngine` (`rules.fetch`): hidden-unicode / whitespace-padding
(obfuscated instructions), taint (untrusted-input → privileged-sink), and injection-in-instructions —
the **same** rule content `skill-scan` uses, so a weakness found when *building* and when *vetting*
resolves to the same `weakness_id`.

**OWASP Agentic crosswalk.** Each weakness crosswalks to **OWASP LLM Top-10** *and* **OWASP Agentic AI
Threats & Mitigations** (alongside CWE → CAPEC → ATT&CK + controls), so findings map to both frameworks
in the report.

## Integration

- local-scan, sca-graph — findings + CVEs to classify
- information-flow — weaknesses escalate flows on their path
- security-judge — a confirmed broke test attaches its weakness here
- risk-report — renders weakness→component→control rows and the crosswalk

## References

- [AsterVault MCP tools — registry.resolve / controls.map](./references/astervault-tools.md)
- [OWASP-LLM mapping (public, safe to keep local)](./references/owasp-llm.md)
- [Graph schema (SSOT)](../../docs/graph-schema.md)
- [Two-sided architecture](../../docs/ARCHITECTURE.md)
