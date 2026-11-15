---
name: information-flow
description: Build the information-flow (IFC) overlay on the data-flow spine — label integrity and confidentiality flows with their data classes and the missing control that would stop each one. Produces the FIDES-style flows and attack paths. Use when a security engineer needs to know which untrusted input reaches a privileged sink, or which regulated data can be exfiltrated, and what control is missing.
---

# Information-Flow (IFC)

Overlay labeled flows on the data-flow spine. A flow is the security-meaningful statement: *this
source reaches that sink carrying these data classes, and this control is missing.* This is the
FIDES-style overlay the platform persists as `informationFlow.flows` + `ifcEdges`.

## When to Activate

- After `data-flow` has built the spine.
- The engineer asks: can untrusted input reach a tool/shell? can regulated data leave? what control
  is missing? what are the attack paths?

## Core Concepts

Two flow kinds (see schema):
- **Integrity** — an untrusted source (`SYSTEM_PROMPT` injection point, user input, tool result
  from an untrusted service) reaches a **privileged sink** (a side-effecting tool, shell, write,
  provider call). The risk is the agent being steered.
- **Confidentiality** — a **regulated store/field** reaches an **exfiltration sink** (an external
  service, an anonymous/over-broad endpoint, a log). The risk is data leaving.

Each flow records `source_label`, `sink_label`, ordered `path_labels`, `data_classes` gathered along
the path, and `missing_control` (the guard that would cut it — or null if controlled). A flow with a
non-null `missing_control` is a **violation**.

## Method

1. Enumerate sources (ingress + untrusted inputs) and sinks (privileged tools / egress / regulated
   stores) from the spine.
2. For each source→sink reachable over `flows_to`/`calls`/`reads`/`writes`, record the path.
3. Classify integrity vs confidentiality by the sink/source polarity above.
4. Gather `data_classes` from `data_field` nodes on the path.
5. Determine `missing_control`: check for a `policy`/guard node `governs`-ing any hop; if none cuts
   the flow, name the control that would (authz on the endpoint, output filter, tool allow-list,
   taint check). Null only when a control genuinely covers it.
6. Write `flows` into the envelope and mark the carrying edges as `ifcEdges`.

## Practical Guidance

- **Reach escalates by identity:** a confidentiality flow whose source store is reachable by an
  **anonymous/external** identity is critical regardless of class — surface it first.
- **Don't fake controls.** If you cannot see a control, the flow is a violation with a named missing
  control; never assume an unseen guard.
- The attack-surface facets (`reach`, `tools_violated`, `sinks`, `paths`) are **derived** from these
  flows — don't store them separately; `risk-report` computes them on read.

## Integration

- data-flow — the spine this labels
- weakness-graph — a weakness on a flow's path raises its severity
- behavioral-redteam / dast-generation — each violating flow seeds a concrete test
- risk-report — renders flows as attack paths + the three attack-surface boxes

## References

- [Graph schema (SSOT)](../../docs/graph-schema.md)
