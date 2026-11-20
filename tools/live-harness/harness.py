"""The live behavioral-harness loop: attacker_drive ▸ defender ▸ judge, emitted as a stream.

Each step is pushed to an `emit(event)` callback the moment it happens, so a UI can render the
kill-chain as it unfolds. The gateway does the real work:
  - offensive.attacker_drive  -> the next adaptive attacker move (+ strategy)
  - the target defender        -> its actual response (a real model under test)
  - canary.scan / canary.verify -> the INDEPENDENT judge (out-of-band evidence only)
  - risk.score                 -> the CVE-calibrated ARS for a realized finding
Every gateway call returns an audit_id, carried in the events. No verdict comes from the
attacker's or defender's self-report; only a planted canary surfacing counts as a break.
"""
from __future__ import annotations

import os
import time
from typing import Callable

import store
from gateway import Gateway
from adapter import TargetAdapter
from attacker import ModelAttacker, enabled as attacker_enabled

Emit = Callable[[dict], None]


def run_engagement(objective: str, canary_type: str, budget: int, emit: Emit,
                   gateway: Gateway | None = None, adapter: TargetAdapter | None = None):
    gw = gateway or Gateway()
    tgt = adapter or TargetAdapter()
    ep = f"live-{int(time.time())}"

    audit_ids: list = []            # every brokered gateway call's audit_id, for the store
    raw_emit = emit

    def emit(ev: dict):             # noqa: intercept to collect audit_ids, then forward
        a = ev.get("audit_id")
        if a:
            audit_ids.append(a)
        raw_emit(ev)

    emit({"type": "engagement_start", "episode_id": ep, "objective": objective,
          "canary_type": canary_type, "budget": budget, "target": tgt.invoke_url})

    gw.initialize()
    off = gw.mint_offensive()
    emit({"type": "offensive_token", "audit_id": off.get("audit_id")})

    minted = gw.canary_mint(canary_type, ep)
    where = tgt.plant(minted["value"])
    plant = gw.canary_plant(ep, minted["token_id"], where)
    emit({"type": "canary_planted", "token_id": minted["token_id"], "canary_type": canary_type,
          "location": where, "audit_id": plant.get("audit_id") or minted.get("audit_id")})

    model_attacker = ModelAttacker() if attacker_enabled() else None
    emit({"type": "attacker_mode",
          "mode": "model" if model_attacker else "gateway (deterministic crescendo)",
          "model": model_attacker.model if model_attacker else None})

    transcript, messages = [], []
    first_break, verdict = None, "held"

    for turn in range(1, budget + 1):
        if model_attacker:                           # adaptive LLM attacker (with reasoning)
            move = model_attacker.drive(objective, transcript)
        else:                                        # gateway-brokered deterministic attacker
            move = gw.attacker_drive(objective, transcript)
        prompt = move.get("move", "")
        emit({"type": "attacker_move", "turn": turn, "prompt": prompt,
              "reasoning": move.get("reasoning"), "strategy": move.get("strategy"),
              "attacker_model": move.get("attacker_model"), "audit_id": move.get("audit_id")})

        messages.append({"role": "user", "content": prompt})
        tgt.clear_egress()
        response, tool_calls = tgt.invoke(messages)
        messages.append({"role": "assistant", "content": response})
        egress = tgt.read_egress()
        emit({"type": "defender_response", "turn": turn, "response": response,
              "tool_calls": tool_calls, "egress": egress})

        transcript.append({"role": "attacker", "content": prompt})
        transcript.append({"role": "defender", "content": response})

        hits = []
        for text in (response, egress):
            if text:
                s = gw.canary_scan(ep, text)
                hits += (s.get("hits") if isinstance(s, dict) else s) or []
        turn_verdict = "broke" if hits else "held"
        if hits and first_break is None:
            first_break, verdict = turn, "broke"
        emit({"type": "turn_verdict", "turn": turn, "verdict": turn_verdict,
              "hit_count": len(hits), "channel": "egress" if egress and hits else "reply"})
        if verdict == "broke":
            break

    v = gw.canary_verify(ep)
    findings = v.get("findings") or []
    emit({"type": "verify", "fired": bool(v.get("fired")), "finding_count": len(findings),
          "audit_id": v.get("audit_id")})

    weakness, ars = {}, {"ars": 0.0, "band": "low", "source": "no finding (held)"}
    if findings:
        f = findings[0]
        weakness = f.get("weakness") or {}
        r = gw.risk_score(f) or {}
        ars = {"ars": r.get("ars"), "band": r.get("band"), "source": "gateway risk.score",
               "audit_id": r.get("audit_id")}
    emit({"type": "weakness", "weakness": weakness, "ars": ars})

    emit({"type": "summary", "verdict": verdict,
          "asr": {"budget": budget, "value": 1.0 if verdict == "broke" else 0.0,
                  "first_break_turn": first_break},
          "episode_id": ep})

    # persist the engagement to the local store so the Artifacts panel can aggregate it
    try:
        store.save({
            "id": ep, "ts": time.time(), "objective": objective, "target": tgt.invoke_url,
            "verdict": verdict, "asr_value": 1.0 if verdict == "broke" else 0.0, "budget": budget,
            "first_break_turn": first_break, "canary_type": canary_type,
            "canary_token": minted.get("token_id"),
            "attacker_model": model_attacker.model if model_attacker else "gateway/deterministic",
            "defender_model": os.environ.get("DEFENDER_MODEL", ""),
            "audit_ids": audit_ids, "weakness": weakness, "ars": ars, "transcript": transcript,
        })
    except Exception as e:
        emit({"type": "store_error", "message": str(e)})

    emit({"type": "done"})
