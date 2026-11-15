# Proxy — primary path is AsterVault

Recon does **not** require a bundled daemon. The agent routes its tool-calls through the **AsterVault
MCP gateway** (run by AsterGuard), which already authenticates, guard-checks (prompt-injection /
egress), brokers the call, and writes an append-only audit trail. **Recon = that audit trail.**

- Point the client at the gateway per AsterVault's MCP connection docs.
- `agent-profiling` / `data-flow` read the gateway's audit export instead of a local capture file.

A minimal local-only `proxy.py` (provider base-URL shim) may be added as an offline fallback for
environments that cannot reach the gateway; it records to `./.asterguard/traffic.jsonl` in the same
shape. The gateway path is primary.
