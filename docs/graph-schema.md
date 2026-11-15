# AsterGuard Security Graph — canonical schema (SSOT)

Every graph a skill builds locally uses **this** shape, so a graph Claude assembles on a
laptop is byte-compatible with one the AsterGuard platform persists (`bronze_graph_render.graph`)
and can be pushed back later without translation. Do not invent node kinds, edge relations, or
flow fields outside this document.

## Graph envelope

```jsonc
{
  "nodes": [ /* Node */ ],
  "edges": [ /* Edge */ ],
  "informationFlow": { "flows": [ /* Flow */ ] },   // IFC overlay (see information-flow skill)
  "ifcEdges": [ /* Edge */ ],                        // edges that carry a labeled flow
  "meta": { "app": "<slug>", "source": "code|traffic|infra", "built_by": "skill:<name>", "built_at": "<iso8601>" }
}
```

## Node

```jsonc
{
  "id": "comp:<kind>:<slug>",   // id PREFIX encodes the kind — never reuse a slug across kinds
  "kind": "<kind>",
  "label": "human name",
  "meta": { /* kind-specific, see below */ }
}
```

### Node kinds (the closed set)

| kind | id prefix | represents | key meta |
|---|---|---|---|
| `endpoint` | `comp:endpoint:` | an ingress route / handler | `method`, `path`, `auth` |
| `function` | `comp:function:` | a code function / handler | `file`, `line` |
| `mcp_tool` | `comp:mcp_tool:` | an agent tool / MCP tool | `signature`, `side_effect` |
| `agent_node` | `comp:agent_node:` | an agent / graph node (LangGraph etc.) | `framework`, `role` |
| `llm_app` | `comp:llm_app:` | the application root | `name` |
| `data_store` | `comp:data_store:` | a table / collection / file store | `engine`, `kind` |
| `data_field` | `comp:data_field:` | a column / field (child of a store) | `parent`, `data_class` |
| `service_account` | `comp:service_account:` | a machine identity | `provider` |
| `role` | `comp:role:` | an IAM role / grant | `permissions` |
| `policy` | `comp:policy:` | a guard / control / policy | `effect` |
| `service` | `comp:service:` | an external service / egress target | `host` |
| `package` | `comp:package:` | an SBOM dependency (name==version) | `ecosystem`, `version`, `transitive` |
| `cve` | `comp:cve:` | a vulnerability | `cve_id`, `severity`, `cvss`, `kev`, `epss` |
| `weakness` | `comp:weakness:` | a weakness class (CWE / registry id) | `registry_id`, `cwe`, `owasp_llm` |

## Edge

```jsonc
{ "src": "comp:…", "dst": "comp:…", "rel": "<relation>", "meta": { } }
```

Relations (closed set): `flows_to` (data movement — the data-flow spine), `calls`, `reads`,
`writes`, `exposes` (endpoint→handler), `uses_tool`, `reaches` (identity→store, the attack-surface
reach), `assumes` (principal→role), `governs` (policy→target), `depends_on` (package→package, the
SCA tree), `affected_by` (package/component→cve), `manifests` (component→weakness).

## Flow (IFC overlay — FIDES-style)

```jsonc
{
  "kind": "integrity | confidentiality",
  "source_label": "e.g. SYSTEM_PROMPT | GET /admin/export | untrusted_input",
  "sink_label":   "e.g. admin_export_records.email | shell | provider_api",
  "path_labels":  ["ordered node labels from source to sink"],
  "data_classes": ["PII","PCI","PHI","SECRET", …],   // from data_field.meta.data_class along the path
  "missing_control": "the control that would break the flow (or null if controlled)"
}
```

- **integrity** flow = untrusted input reaches a privileged sink (prompt-injection → tool/shell).
- **confidentiality** flow = regulated data reaches an exfiltration sink (store → external/anon caller).
- A flow is a **violation** when `missing_control` is non-null.

## Attack-surface facets (derived from the graph — do not store separately)

Computed on read from nodes + edges + flows (see `risk-report`):

```jsonc
{
  "reach":          [ { "store": "…", "classes": [...], "via": ["identity/service"], "columns": [...] } ],
  "tools_violated": [ "tool ids that sink an integrity flow" ],
  "sinks":          [ "confidentiality sink labels" ],
  "paths":          [ { "kind": "...", "hops": N, "sink": "...", "classes": [...], "missing_control": "..." } ]
}
```

## Data classes (closed vocabulary)

`PII`, `PCI`, `PHI`, `SECRET`, `CREDENTIAL`, `FINANCIAL`, `INTERNAL`, `PUBLIC`.
A field with no evidence of a class carries none — **never fabricate a class** (carry `dataCategory`
verbatim when a source file declares one).

## Weakness vocabulary

Weakness ids use the registry vocabulary; LLM/agentic weaknesses use `llm_*` ids and alias to the
OWASP-LLM top-10 where applicable. CWE is attached when known. (Mirror of the platform's
weakness→control crosswalk.)
