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

## Practical Guidance

- **Ground every test (low freedom):** no test without a node/flow it targets — that's what keeps the
  suite precise and the findings explainable.
- Prefer a web/API engine (ZAP-style) for HTTP endpoints; an agent-DAST driver for tool/prompt surface.
- Keep payloads out of the SKILL — they come from `testgen.patterns`, so the corpus stays current and server-side.

## Integration

- information-flow, agent-profiling — provide the targets
- AsterVault `testgen.patterns` — the attack corpus
- security-judge — scores the run
- behavioral-redteam — the multi-turn counterpart (this skill is single-shot dynamic probes)

## References

- [AsterVault MCP tools](../weakness-graph/references/astervault-tools.md)
- [Graph schema (SSOT)](../../docs/graph-schema.md)
