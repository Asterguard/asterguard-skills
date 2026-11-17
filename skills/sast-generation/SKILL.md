---
name: sast-generation
description: Generate SAST tests from the built security graph — target-grounded semgrep rules (and static assertions) that prove each weakness's code/config sink is present or absent. Use when a security engineer needs static tests derived from the structure of an app or agent, not a generic registry scan. The static counterpart to dast-generation.
---

# SAST Generation

Turn the graph into concrete **static** tests. Every test is grounded in a real sink the scan found, so
the suite proves *this* target's actual weaknesses, not a generic ruleset. This is the static twin of
`dast-generation`: where DAST emits a dynamic probe per exposed flow, SAST emits a **grounded semgrep
rule** (plus a static assertion) per weakness sink. Emits the platform's `TestDefinition` schema so
results are ingestible later.

## When to Activate

- After the graph is built (weakness nodes with their code/config sinks present).
- The engineer wants *generated, target-specific* static tests — not the generic community rulesets
  `local-scan` runs. (local-scan = collection with `p/python` etc.; this skill = generation from the graph.)
- Any code or IaC target. For a live-only agent with no source, there is no static surface — skip to DAST.

## Core Concepts

- **Grounded generation:** each weakness node → a static test targeting the exact sink its evidence
  points at (an injection call, a wildcard IAM action, a `0.0.0.0/0`, an MD5 call, a hardcoded key).
  No test without a node/sink it targets — that is what keeps the suite precise and explainable.
- **Rules come from the pack + AsterVault, not fitted here:** take the sink shape from the target's
  **static pack facet** (`semgrep_rules_path`) when a pack matched, and call `testgen.patterns(weakness_id)`
  for the sink/boundary metadata that seeds the rule. The agent writes the rule *for this sink*; it does
  not hand-fit rules to pass.
- **Posture = fixed-by-default:** the oracle asserts the sink is **absent** (the weakness is remediated).
  A rule match therefore means the vuln is still present → `broke`; no match → `held`. (Flip to
  `static_present` only for a regression test that asserts a known-bad sink stays caught.)
- The agent writes the rule + assertion; the semgrep engine (or a pluggable SAST adapter) produces the
  hard, file:line evidence a `security-judge` trusts.

## Method

1. Enumerate targets from the graph: weakness nodes and the component/sink each is bound to (from
   `weakness-graph` / `data-flow` / `information-flow`).
2. For each, call `testgen.patterns(weakness_id)` to get the sink/boundary metadata (same corpus DAST
   uses), and pull the pack's `semgrep_rules_path` entry for that CWE when a pack matched.
3. Emit a grounded **semgrep rule** per code sink → `./.asterguard/rules/<weakness_id>.semgrep.yaml`
   (`id`, `languages`, `patterns`, `metadata: {cwe, weakness_id}`, `message`). For config/IaC sinks with
   no code pattern, emit the static assertion only.
4. Emit `TestDefinition` entries: `{id, kind:"sast", target, weakness_id, cwe, objective, steps,
   oracle:{type:"static_absent", sink_regex|rule_id, assertion}, grounded_in, execution_mode:"static"}`.
5. Write the suite to `./.asterguard/tests.sast.json`.
6. **Execute through a configured adapter, not a built-in engine** — same seam as `dast-generation`.
   Execution runs through a pluggable **SAST harness** (the customer's own SAST, CodeQL, or semgrep)
   behind one adapter interface. The adapter takes the `TestDefinition`s + generated rules, runs them
   over the source, and returns results to `security-judge`. Swapping the harness never changes the skill.
   - **`semgrep` reference adapter (real execution):** run the generated rules —
     `semgrep --config .asterguard/rules/ --json <path>` — not the generic registry rulesets. A rule hit
     is hard, code-checkable evidence (file:line sink) a `security-judge` can trust: a hit on a
     fixed-posture rule is `broke`, no hit is `held`. Worked example: `demo-apps/vuln-agent-gateway/scan/`
     (semgrep → 11 grounded sinks → normalize → report).
   - **IaC / HCL targets (e.g. Terraform):** the code `patterns` do not apply; assert the config sink
     statically (grep/HCL-parse for the sink the `checkov` finding already located — `s3:*`, `iam:PassRole`,
     `0.0.0.0/0`), cross-checked against the `check_id`s on that resource. Worked example:
     `demo-apps/terraform-agent-platform/out/tests.sast.json`.

## Practical Guidance

- **Ground every rule (low freedom):** the rule's pattern comes from the sink in the evidence, mapped by
  CWE to the registry `weakness_id`, so the static sink lines up with the control crosswalk **and** the
  DAST probe for the same CWE. Never author a rule fitted to make the suite pass.
- **Semantic sinks degrade honestly:** a weakness whose assertion is semantic ("encryption-at-rest
  removed", "approval gate deleted") with no code/regex sink has **no** static match — mark it
  `inconclusive`, never `broke`. That is the model-backed `security-judge`'s job (AST/HCL reason), not a
  generation gap. Do not force a regex.
- Keep rule payloads out of the SKILL — the sink shapes come from `testgen.patterns` + the static pack,
  so the corpus stays current and server-side.
- Keep the native semgrep JSON alongside the normalized suite for audit (`./.asterguard/raw/`).

## Integration

- weakness-graph, data-flow, information-flow — provide the sinks each test targets
- local-scan — the **collection** counterpart (generic registry rulesets); this skill **generates**
  target-grounded rules from the graph. Run local-scan first for coverage, this for precision.
- dast-generation — the **dynamic** counterpart (same `testgen.patterns` corpus, same adapter seam);
  pair them so every CWE has both a static and a runtime test.
- AsterVault `testgen.patterns` — the sink/boundary corpus
- security-judge — scores the run (broke/held/inconclusive)
- remediation — consumes the confirmed sinks

## References

- [AsterVault MCP tools](../weakness-graph/references/astervault-tools.md)
- [Graph schema (SSOT)](../../docs/graph-schema.md)
