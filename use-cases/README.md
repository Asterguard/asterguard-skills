# Offensive use-cases — multi-turn, proven, on camera

Real authorized pentests run with the offensive skills against deliberately-vulnerable demo agents.
Each use-case is one documented scenario **and** one video: the `pentest` playbook driving a **multi-turn**
campaign to a **canary-proven** break, then the kill-chain and the fix. These are the proof the skills
work — and the scripts to reproduce each on camera.

> **Authorized engagements only.** Every target here is one we own (the demo agents). The runs are
> scoped and audited through the gateway, on a recorded authorization — exactly the discipline the
> `offensive-engineer` RoE step enforces.

## The loop (every use-case)

Claude Code (offensive skills installed) runs the **`pentest`** playbook against a live agent:

```
recon ─► attack-planner ─► attacker-model ─► behavioral-redteam (multi-turn) ─► exploit-chain ─► pentest-report
 (map)   (MCP: what to test   (govern the        (crescendo / decomposition /     (foothold →       (PoC + ASR +
          + canary types)      attacker model)    indirect injection)             compromise)        kill-chain)
```

The **proof** is a canary on the wire, verified by the gateway — never the model's say-so. Each video
follows the same beats: **recon map → the plan → the multi-turn turns landing → the canary hit → the
kill-chain + report.**

## The scenarios

| # | Use-case | Target | Attack class | Canary types | Video |
|---|---|---|---|---|---|
| [S1](s1-prompt-injection-pii-exfil.md) | Indirect prompt-injection → PII exfil | `support-agent-demo` | injection · exfil | document · injection · egress | [▶ MP4](https://agenticrisklabs.io/videos/s1.mp4) |
| [S2](s2-over-privilege-money-movement.md) | Over-privilege + cross-tenant → money movement | `payment-agent-demo` (bad branch) | excessive-agency · authz | secret · workload-identity · egress | [▶ MP4](https://agenticrisklabs.io/videos/s2.mp4) |
| [S3](s3-identity-spoof-cross-tenant.md) | Caller spoofing → cross-tenant PII | `hr-agent-demo` | authz · identity | credential · workload-identity | [▶ MP4](https://agenticrisklabs.io/videos/s3.mp4) |
| [S4](s4-memory-poisoning-context-bleed.md) | Memory poisoning + context bleed | `agentic-workflow-demo` | memory-poisoning · context-bleed | memory · context | [▶ MP4](https://agenticrisklabs.io/videos/s4.mp4) |

## Prerequisites

1. **Offensive tier deployed** — the privileged `offensive:run` gate + the forge-behind-MCP engine
   (astervault offensive-tier). Mint the org's **offensive token** (`ASTERGUARD_OFFENSIVE_TOKEN`); without
   it the gateway blocks execution (`403 offensive privilege required`) and only planning runs.
2. **Demo agents stood up** — on the box under `/opt/asterix/demo-apps/` (langgraph 0.2 venv), launched
   via `demo_launch.sh <app> <port> <model>`, reached from the laptop over an SSH tunnel. They run on
   **OpenAI gpt-4o-mini** (the box can't reach DeepSeek). **Never public** — `/admin/export` dumps
   synthetic PII; the planted secret is `SSN-900-55-DEMO`.
3. **Skills installed** in Claude Code (the `asterguard-security` plugin), connected to the gateway.

## Running one

```text
You ▸ Run the `pentest` playbook on <target>. <paste the scenario's engagement brief>.
```

The playbook elicits/confirms the RoE, acquires the offensive token, then runs the loop. See each
scenario doc for the exact brief, the expected proven break, and the video beats.

## Adding the video

After a run, record the Claude Code session with the helper — it prints the scenario's beats and
keeps the capture local:

```bash
scripts/record-usecase.sh s1     # (s2, s3, s4)
```

Then **upload the cut to the video host** as `videos/s<N>.mp4` (the docs already link
`https://agenticrisklabs.io/videos/s<N>.mp4`) and fill the scenario doc's **Result** with the real
ASR + the canary hit. Videos are hosted, **not committed** — no binary churn in history; see
[`media/README.md`](media/README.md). (These videos also feed the site's film grid and the social posts.)
