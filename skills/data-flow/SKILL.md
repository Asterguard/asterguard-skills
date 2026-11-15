---
name: data-flow
description: Build the data-flow architecture — how data moves from stores and fields through functions and tools to endpoints and egress. Produces data_store/data_field/function/mcp_tool/endpoint nodes joined by reads/writes/calls/flows_to edges. Use when a security engineer needs to see where regulated data lives and how it travels through an app or agent.
---

# Data-Flow Architecture

Construct the data-movement spine of the target: what data exists, where it lives, and every path it
takes to an exit. This is the substrate the information-flow (IFC) overlay labels.

## When to Activate

- The engineer asks where sensitive data lives or how it reaches an endpoint / tool / egress.
- Before `information-flow` — the IFC overlay needs this spine.
- For code targets (from AST/handlers), infra targets (from IAM + inventory), or traffic targets
  (from recorded tool calls + responses).

## Core Concepts

- **Stores & fields:** a `data_store` node per table/collection/file store; a `data_field` child per
  column/field with its `data_class` (PII/PCI/PHI/SECRET/…) when evidenced. Fields link to their
  parent store.
- **Movers:** `function` and `mcp_tool` nodes that read/write stores, and `endpoint` nodes that
  expose them.
- **The spine:** `reads` / `writes` edges (mover↔store), `calls` / `uses_tool` edges (handler→tool),
  `exposes` (endpoint→handler), and `flows_to` edges that chain a concrete data path end to end.

## Method

By source type:
- **code** — from handlers/ORM/queries: stores & fields from models/migrations; reads/writes from
  query sites; endpoints from routes; tools from tool/@tool registrations.
- **infra** — stores from the data inventory; reach from IAM grants (role→store) instead of call
  sites; endpoints from the service's exposed routes.
- **traffic** — stores & fields inferred from recorded tool arguments/results; movers from the tools
  actually invoked; endpoints from the ingress that triggered each turn.

Then: 1) emit store + field nodes (classes only where evidenced — never fabricate); 2) emit movers
and endpoints; 3) draw `reads`/`writes`/`calls`/`exposes`; 4) thread `flows_to` for each path a
field can travel to an endpoint or egress; 5) write into `./.asterguard/graph.json`.

## Practical Guidance

- **Non-code data (medium freedom):** stores often come from knowledge/PowerBI/schema files, not
  code — ingest those too; carry any declared `dataCategory` verbatim onto the field.
- Collapse a field to its parent store for store-level views; keep field granularity in the graph.
- A store reachable by an **external or anonymous** identity is the signal information-flow will
  escalate — make sure the identity/endpoint that reaches it is in the spine.

## Integration

- local-scan / proxy-recon / agent-profiling — sources of stores, movers, endpoints
- information-flow — labels this spine into integrity/confidentiality flows
- weakness-graph — a mover with a weakness becomes a violation when it sits on a flow

## References

- [Graph schema (SSOT)](../../docs/graph-schema.md)
