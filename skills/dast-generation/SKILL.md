---
name: dast-generation
description: Generate DAST tests from the built security graph — web/API and agent dynamic probes targeting the exposed endpoints, tools and violating flows. Use when a security engineer needs active dynamic tests derived from the structure of an app or agent, not a generic scan.
---

# DAST Generation

Turn the graph into concrete dynamic tests. Every test is grounded in a real node or flow, so the
suite probes *this* target's actual surface, not a generic checklist. Emits the platform's
`TestDefinition` schema so results are ingestible later.

## When to Activate

- After the graph is built (endpoints, tools, information-flow violations present).
- The engineer wants active probes (web/API DAST, agent tool-abuse) rather than static findings.

## Core Concepts

- **Grounded generation:** each endpoint node → auth/authz/input probes; each violating
  confidentiality flow → an exfiltration probe against its sink; each effectful tool → an abuse probe.
- **Attack patterns come from AsterVault:** call `testgen.patterns(weakness_id)` for the corpus that
  seeds each test — the patterns are server-side knowledge, not bundled here.
- The agent writes the test spec; the harness model fills payloads from the returned patterns.

## Method

1. Enumerate targets from the graph: endpoints, effectful tools, violating flows (from information-flow).
2. For each, call `testgen.patterns` with the relevant `weakness_id` to get attack patterns.
3. Emit `TestDefinition` entries: `{id, kind:"dast", target, weakness_id, objective, steps, oracle}`.
4. Write to `./.asterguard/tests.dast.json`.
5. **Execute through a configured adapter, not a built-in engine.** This skill generates and targets;
   execution runs through a pluggable **HTTP-layer / DAST harness** — the customer's own internal
   implementation configured for DAST/behavioral testing, or ZAP / AgentDojo — behind one adapter
   interface (the same pattern as AsterVault's resource adapters). The adapter takes the
   `TestDefinition`s, drives the target over HTTP, and returns results to `security-judge`. Swapping the
   harness never changes the skill.
   - **`nuclei` reference adapter (real execution):** emit one grounded nuclei template per probe —
     endpoint + `weakness_id` + a **proof-matcher** that asserts exploitation, not a 200 (cross-tenant
     row leak for SQLi, `/etc/passwd` for cmd-injection/traversal, a leaked secret for authz/SSRF, the
     reflected payload for XSS). Run `nuclei -u <base> -t templates/ -jsonl`; a hit is hard,
     code-checkable evidence a `security-judge` can trust. A matcher that fires is `broke`; no hit is
     `held`. Worked example: `demo-apps/vuln-agent-gateway/scan/` (generate → run → normalize).

## Practical Guidance

- **Ground every test (low freedom):** no test without a node/flow it targets — that's what keeps the
  suite precise and the findings explainable.
- **The engine is pluggable:** assume a configured HTTP-layer harness exists; generate to its adapter.
  A web/API harness drives HTTP endpoints; an agent-DAST driver drives the tool/prompt surface.
- Keep payloads out of the SKILL — they come from `testgen.patterns`, so the corpus stays current and server-side.

## Integration

- information-flow, agent-profiling — provide the targets
- sast-generation — the **static** counterpart (same `testgen.patterns` corpus, same adapter seam):
  generates grounded semgrep rules so every CWE has both a static and a runtime test
- AsterVault `testgen.patterns` — the attack corpus
- security-judge — scores the run
- behavioral-redteam — the multi-turn counterpart (this skill is single-shot dynamic probes)

## References

- [AsterVault MCP tools](../weakness-graph/references/astervault-tools.md)
- [Graph schema (SSOT)](../../docs/graph-schema.md)
