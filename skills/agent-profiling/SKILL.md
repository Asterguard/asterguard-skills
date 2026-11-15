---
name: agent-profiling
description: Build the agent AI-BOM and authority boundaries — the agents, tools, models, datasets and the trust/authority edges between them — from source code or recorded traffic. Use when a security engineer needs to know what an agent can do, what it can touch, and where its authority boundaries are.
---

# Agent Profiling

Produce the agentic layer of the graph: the AI-BOM (agents, tools, models, datasets) plus the
**authority boundaries** — which principal may invoke which tool, and what each tool can reach. This
is what makes the integrity/confidentiality flows meaningful for an agent.

## When to Activate

- The target is agentic (LangGraph / LangChain / ADK / custom agent loop), from code or traffic.
- Before `information-flow` for agent targets — flows need the agent/tool/authority nodes.
- The engineer asks what an agent can do or where its trust boundaries are.

## Core Concepts

- **AI-BOM nodes:** `agent_node` (role + framework), `mcp_tool` (signature + side-effect),
  `llm_app` (root), model/dataset assets.
- **Authority boundaries:** `uses_tool` edges (agent→tool) gated by the principal/role that may do
  so; a tool's reach (`reads`/`writes`/`reaches` to stores/services) defines its blast radius.
- **Framework extraction patterns:** see `references/framework-extraction.md` — how to find agents,
  tools, and the graph structure in LangGraph, LangChain, OpenAI/ADK, and from raw traffic.

## Method

- **From code:** locate agent/graph construction, `@tool`/tool registrations, the system prompt,
  and each tool's implementation to derive its reach. Build agent/tool/model nodes + authority edges.
- **From traffic:** every distinct tool in `tool_calls` is a tool node; its arguments/results reveal
  the stores/fields and services it touches; the recorded system prompt is the agent's instruction
  surface. Build the same nodes from observed behavior.
- Mark each tool's `side_effect` (read-only vs effectful) and whether a HITL/guard gates it.

## Practical Guidance

- **Effectful + ungated = the integrity sink** information-flow will flag. Tag it precisely.
- **Over-broad reach:** a tool that can touch more than its purpose needs is `over_privileged_agent` —
  hand that to weakness-graph.
- Prefer one tool node per logical tool even if the code wraps it several ways.

## Integration

- proxy-recon / local-scan — sources (traffic / code)
- information-flow — consumes agents, tools, authority edges
- weakness-graph — over-privilege / excessive-agency weaknesses attach to these nodes
- behavioral-redteam — tools + boundaries seed the attack suites

## References

- [Framework extraction patterns](./references/framework-extraction.md)
- [Graph schema (SSOT)](../../docs/graph-schema.md)
