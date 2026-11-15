# Framework extraction patterns

How to find agents, tools, and the graph structure in common agent frameworks — from code or from
recorded traffic. Public, non-proprietary heuristics (safe to keep client-side).

## From code

| Framework | Agents / nodes | Tools | System prompt | Reach (per tool) |
|---|---|---|---|---|
| LangGraph | `StateGraph`/`add_node`, compiled graph | `@tool`, `ToolNode`, `bind_tools` | prompt templates / `SystemMessage` | the tool fn body (DB/HTTP/FS calls) |
| LangChain | `AgentExecutor`, `create_*_agent` | `Tool(...)`, `@tool`, toolkits | prompt in the chain | tool `func` implementation |
| OpenAI / ADK | assistant / agent defs | function-tool schemas | instructions field | the registered function |
| Custom loop | the loop + role prompts | the dispatch table of callables | the seed/system message | each callable's body |

Steps: locate the agent/graph construction → enumerate registered tools → read each tool's
implementation to derive `reads`/`writes`/`reaches` targets and `side_effect` → capture the system
prompt as the instruction surface → find any HITL/guard gate.

## From traffic (no code)

- **Tools** = the distinct function names in `tool_calls`.
- **Signatures** = inferred from the arguments seen across calls.
- **Reach** = stores/fields/services evident in tool arguments and results (e.g. a SQL string, a URL,
  a returned record's fields).
- **System prompt** = the recorded system message on the model request.
- **Side-effect** = whether the tool's result reflects a mutation (write/charge/send) vs a read.

## Guidance

- One tool node per logical tool even if wrapped several ways.
- Mark `side_effect: effectful` for anything that writes, sends, charges, or calls out — those are the
  integrity sinks information-flow cares about.
- Over-broad reach (a tool that can touch more than its purpose) → hand to weakness-graph as
  `over_privileged_agent`.
