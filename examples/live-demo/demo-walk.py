"""Live demo walk — the self-improving AppSec playbook on `support-agent`, driven
over the live AsterVault MCP connection (localhost:8080), generation via the
asterguard-remediation SSOT. Screenshot-ready narrated transcript."""
import asyncio, base64, json, sys
SP="/private/tmp/claude-501/-Users-sameermangalampalli-Nexcraft-Astherixguard/c09e3174-d882-43e5-9960-04e0aa0c571f/scratchpad"
sys.path.insert(0, "/Users/sameermangalampalli/Nexcraft/asterguard-remediation")
import asterguard_remediation as AR
TOK=open(SP+"/dev_jwt.txt").read().strip()
URL="http://localhost:8080/mcp"
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession

def d(r):
    t=" ".join(getattr(c,"text","") for c in (r.content or []))
    try: return json.loads(t).get("data", json.loads(t))
    except Exception: return t
def hdr(n,title): print(f"\n{'─'*72}\n  STEP {n} · {title}\n{'─'*72}")

async def main():
    async with streamablehttp_client(URL, headers={"Authorization":f"Bearer {TOK}"}) as (r,w,_):
        async with ClientSession(r,w) as s:
            await s.initialize()
            print("  ✦ Claude Code ↔ AsterVault MCP — connected.  App under assessment: support-agent")

            hdr(1,"RECALL (cold start) — what does the team already know?")
            m=d(await s.call_tool("memory.recall",{"context":{"app":"support-agent","query":"PII egress"}}))
            print(f"    memory.recall(support-agent) → {m.get('count',0)} prior memories  (cold: none yet)")
            p=d(await s.call_tool("knowledge.patterns",{"context":{"query":"PII egress"}}))
            pats=[x.get('title') for x in (p.get('patterns') or [])]
            print(f"    knowledge.patterns → approved house rules: {pats}")

            hdr(2,"RESOLVE — the finding → canonical weakness + controls")
            w1=d(await s.call_tool("registry.resolve",{"finding":{"lane":"sca","title":"effectful egress tool with no DLP","cwe":"CWE-200","weakness_id":"llm_cfg_egress_no_dlp"}}))
            print(f"    registry.resolve → {w1.get('weakness_id')} · {w1.get('base_severity')} · {w1.get('category')} · OWASP {w1.get('owasp_llm_refs')}")
            c=d(await s.call_tool("controls.map",{"weakness_id":"llm_cfg_egress_no_dlp"}))
            print(f"    controls.map → " + ", ".join(f"{x['framework']}:{x['id']}" for x in c.get('controls',[])[:5]))

            hdr(3,"RED-TEAM — plant a canary, prove the leak on egress")
            cm=d(await s.call_tool("canary.mint",{"type":"secret","episode_id":"demo"}))
            print(f"    canary.mint → {cm.get('value')}  (token {cm.get('token_id')})")
            await s.call_tool("canary.plant",{"episode_id":"demo","token_id":cm.get('token_id'),"location":"admin_export_records"})
            leak="GET /admin/export leaked: "+base64.b64encode(cm['value'].encode()).decode()  # base64 evasion
            sc=d(await s.call_tool("canary.scan",{"episode_id":"demo","text":leak}))
            hit=(sc.get('hits') or [{}])[0]
            print(f"    attacker exfiltrates (base64-encoded)… canary.scan → HIT: {hit.get('type')} via {hit.get('encoding')} encoding")
            v=d(await s.call_tool("canary.verify",{"episode_id":"demo"}))
            print(f"    canary.verify → fired={v.get('fired')}  ⇒ PROVEN PII exfiltration (not a guess)")

            hdr(4,"REMEDIATE — generate the fix as a PR (asterguard-remediation SSOT)")
            plan=AR.from_episode(json.load(open("/Users/sameermangalampalli/Nexcraft/asterguard-skills/examples/live-demo/support-agent-episode.json")))
            bundle=AR.emit("astervault", plan); pr=AR.to_pr(plan,"astervault")
            print(f"    from_episode → {len(plan.mapped)} control gaps · emit(astervault) → {len(bundle.get('rules',[]))} rules")
            print(f"    to_pr → {pr['title']}")
            print(f"      branch {pr['branch']} · file {pr['files'][0]['path']}")
            for ln in pr['files'][0]['diff'].splitlines()[3:9]: print("      "+ln)

            hdr(5,"ENFORCE — AsterVault applies the policy (review-gated)")
            g=d(await s.call_tool("policy.apply",{"bundle":bundle,"approved":False}))
            print(f"    policy.apply(approved=False) → review_required={g.get('review_required')}")
            a=d(await s.call_tool("policy.apply",{"bundle":bundle,"approved":True}))
            print(f"    policy.apply(approved=True)  → applied={a.get('applied')} enforced_at={a.get('enforced_at')} egress={a.get('egress',{}).get('hosts')}")

            hdr(6,"CAPTURE — write the decision back to shared memory")
            cap=d(await s.call_tool("memory.capture",{"record":{"app":"support-agent","weakness_id":"llm_cfg_egress_no_dlp","topic":"PII egress","kind":"decision","summary":"anon admin export forbidden; tokenize + egress-allowlist","why":"canary-proven PII exfil reachable anonymously","provenance":{"pr":pr['branch']}}}))
            print(f"    memory.capture → {cap.get('memory_id')} captured (scope {cap.get('scope')})")

            hdr(7,"RECALL (warm) — the next engineer/session starts informed")
            m2=d(await s.call_tool("memory.recall",{"context":{"app":"support-agent","query":"PII egress"}}))
            rec=(m2.get('memories') or [{}])[0]
            print(f"    memory.recall → {m2.get('count')} memory now: \"{rec.get('summary')}\"")
            print(f"\n  ✦ Loop closed. The system is now smarter about support-agent than it was 60 seconds ago.")

asyncio.run(main())
