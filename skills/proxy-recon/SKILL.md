---
name: proxy-recon
description: Record a live agent by routing its LLM or ingress traffic through the local AsterGuard proxy, producing a traffic corpus to profile and attack — no source code required. Use when a security engineer needs to assess a black-box agent, or capture real tool-calls and data flows from a running system.
---

# Proxy Recon

Put the AsterGuard proxy in front of a running agent and record. The corpus it produces is the
no-code substrate for `agent-profiling`, `data-flow`, and the test skills. Nothing is uploaded; the
proxy forwards to the real upstream and returns the real response (transparent).

## When to Activate

- The target is a **live agent** (black-box) rather than a repo or image.
- You need real tool-calls, system prompts, data accessed, and responses — captured from traffic.
- Before `agent-profiling` / `data-flow` when source is unavailable.

## Core Concepts

Two proxy positions (pick per the orchestrator's source-type):
- **Provider proxy** — the agent's LLM base-URL points at the proxy; observe the agent's *model*
  calls (messages, tool schemas, tool calls, tool results). Lowest-friction, zero client change.
- **Ingress proxy** — the proxy sits in front of the agent's HTTP endpoint; drive *user* turns
  through it to exercise the whole agent.

The proxy streams SSE through untouched while tee-ing a copy to parse tool calls. Observe-and-record
by default (advisory posture); an optional inline-guard mode can block/annotate in the hot path.

## Method

Primary path — route through the **AsterVault MCP gateway** (it already proxies, guards, and audits):
1. Connect the client to the gateway per AsterVault's MCP connection docs; exercise the agent.
2. Pull the gateway's audit export → `./.asterguard/traffic.jsonl` (`{ts, system, messages, tools,
   tool_calls, tool_results, response, upstream}`). **Recon = the audit trail.**
3. Hand `traffic.jsonl` to `agent-profiling` / `data-flow`.

Offline fallback (no gateway reachable) — a local provider base-URL shim records the same shape; see
`scripts/README.md`.

## Practical Guidance

- **Provider vs ingress (low freedom):** provider proxy for model-layer recon; ingress when you must
  attack the full agent or there is no separable model call.
- **Secrets:** redact Authorization/API-key headers in the recorded corpus; never persist upstream keys.
- **Inline-guard is opt-in:** default is passthrough. Guard mode must fail-open (never drop a real
  response on proxy error) and is advisory unless the engineer explicitly wants enforcement.

## Integration

- agent-profiling, data-flow — consume `traffic.jsonl`
- behavioral-redteam, dast-generation — drive generated tests back through the proxy
- security-engineer — selects proxy-recon for traffic-source targets

## References

- [Proxy (recon via the gateway; optional local shim)](./scripts/README.md)
- [Graph schema (SSOT)](../../docs/graph-schema.md)
