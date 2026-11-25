# Live Offensive Harness

A small server that runs a **multi-turn offensive engagement against an agent and streams it
live** — attacker reasoning → the next prompt applied → the defender's real response →
per-turn canary verdict — plus the free analysis tier (SCA, SAST, DAST), the data-flow
(trifecta), realized weaknesses + ARS, and a running summary. A security engineer points it at
their own AsterVault gateway and target and watches the kill-chain unfold in the browser.

The free analysis panels run locally: **SCA** (OSV CVEs for the declared manifest), **SAST**
(semgrep with the bundled offline ruleset `semgrep-rules.yaml` over `TARGET_REPO`; grounded-regex
fallback if semgrep isn't installed), and **DAST** (read-only live probes of the target's HTTP
surface — the harness's own engine, no external tool). Their findings roll into the Artifacts
panel's severity totals alongside the subscription behavioral findings.

Install the SAST engine with `pip install semgrep` (included in `requirements.txt`). The bundled
ruleset runs fully offline — no semgrep registry login or network needed.

## Generic by design — target profiles

Nothing about any one application is baked into the engines. A target is described by a **profile**
JSON — its tool list, data-flow graph, how to plant a canary, which manifest to scan, which paths to
probe. With no profile the library uses neutral generic defaults; point `TARGET_PROFILE` at a profile
to describe your app. The bundled `targets/support-agent-demo.json` is one **example**, not a default.

The split is deliberate: the **profile is the app's structure** (committable, portable), the
**environment is where it runs** (machine-specific locations — invoke URL, DB path, repo path, egress
log, bearer, gateway URL). To point the harness at your own agent, copy the example profile, fill in
your tools/data-flow/plant strategy, and set the env locations.

Everything shown is **gateway- or scanner-backed** — no fabricated verdicts, CVEs, or risk
numbers. The gateway is the independent judge: a turn only counts as a break when a *planted
canary* surfaces on an out-of-band channel (the defender's reply or an egress sink), never
from the attacker's or defender's self-report.

## How it works

```
attacker move ──────────────▶ target defender (your agent) ──▶ canary.scan / canary.verify
(gateway offensive.attacker_drive,   (its real response)          (independent judge, audited)
 or a configured ATTACKER_MODEL
 with per-move reasoning)
```

The attacker is either the gateway's deterministic crescendo (`offensive.attacker_drive`) or, when
`ATTACKER_API_BASE`/`ATTACKER_MODEL` are set, an adaptive LLM that emits its reasoning plus the next
prompt (the gateway canary stays the sole judge either way). Each step is pushed over Server-Sent
Events to `console.html`, which builds the engagement
card-by-card as it happens. `risk.score` gives the CVE-calibrated ARS for a realized finding;
the OSV advisory DB (queried directly) gives the component-layer SCA.

## Run it

1. **A running AsterVault gateway** and a base-identity **bearer JWT** carrying the
   `offensive:entitled` claim (the harness mints the privileged `asg_off_…` token itself).
2. **A target defender** exposing `POST /invoke {messages:[{role,content}]} → {output, tool_calls}`
   (the `support-agent-demo` API is one; bring your own by matching that shape).

```bash
pip install -r requirements.txt

# gateway
export ASTERVAULT_MCP_URL="https://your-gateway/mcp"
export ASTERVAULT_BEARER_FILE="/path/to/bearer.jwt"        # or ASTERVAULT_BEARER="<jwt>"

# target defender
export TARGET_INVOKE_URL="http://127.0.0.1:8097/invoke"
export TARGET_DB="/path/to/target.sqlite"                  # optional: lets the canary be planted in retrievable data
export TARGET_EGRESS_LOG="/path/to/egress.log.jsonl"       # optional: egress sink the harness reads per turn
export TARGET_REQUIREMENTS="/path/to/your/requirements.txt" # optional: what SCA scans (defaults to the demo manifest)

uvicorn server:app --host 127.0.0.1 --port 8777
# open http://127.0.0.1:8777
```

Set the objective, canary type, and turn budget, press **Run engagement**, and watch it live.

## Configuration (all env, no secrets in code)

| Var | Purpose |
|---|---|
| `ASTERVAULT_MCP_URL` | gateway MCP endpoint |
| `ASTERVAULT_BEARER` / `ASTERVAULT_BEARER_FILE` | base bearer JWT (offensive-entitled), value or file |
| `TARGET_PROFILE` | path to a target profile JSON describing the app (tools, data-flow, plant, manifest, paths) — none → generic defaults |
| `TARGET_INVOKE_URL` | defender `/invoke` endpoint |
| `TARGET_DB` / `TARGET_PLANT_TABLE` / `TARGET_PLANT_COLUMN` / `TARGET_PLANT_ROW_ID` | where to plant the canary so it's retrievable |
| `TARGET_EGRESS_LOG` | JSONL egress sink the harness reads each turn |
| `TARGET_REQUIREMENTS` | dependency manifest for the SCA panel |
| `TARGET_REPO` | repo path for the SAST panel (grounded static rules) |
| `TARGET_BASE_URL` | base to probe for the DAST panel (defaults to `TARGET_INVOKE_URL` with the path stripped) |
| `TARGET_DATAFLOW` | JSON data-flow graph to render (overrides the profile; else a generic skeleton) |
| `TARGET_TOOLS` | comma list of tool names for the AI-BOM (overrides the profile's `tools`) |
| `ATTACKER_API_BASE` / `ATTACKER_API_KEY` / `ATTACKER_MODEL` | adaptive model attacker (OpenAI-compatible); unset → gateway deterministic crescendo |
| `DEFENDER_MODEL` | defender model name shown in the AI-BOM / stored with each engagement |
| `ENGAGEMENT_DB` | SQLite path for the engagement store (default `./engagements.db`) |
| `OBJECTIVE` / `CANARY_TYPE` / `BUDGET` | engagement defaults |

The bearer and any model keys live in the environment or the target's own process — this tool
writes nothing with a secret to disk. See `../../skills/behavioral-redteam` and
`../../skills/canary-testing` for the methodology this operationalizes.

## Tests

Hermetic unit tests live in [`tests/`](tests/) — no gateway, target, or network. They cover the
engagement loop (via injected fakes), the store, the target adapter, target-profile resolution, the
artifacts aggregators, the attacker's output parsing, and the SAST/SCA/DAST engines (DAST against a
throwaway localhost server). Run them directly, or via the pack's smoke gate:

```bash
python -m unittest discover -s tools/live-harness/tests -v
python scripts/smoke.py          # also runs them (discovers every tools/*/tests)
```
