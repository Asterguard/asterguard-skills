"""Live offensive-harness console server.

A security engineer runs this against their own AsterVault gateway + target and watches a
multi-turn offensive engagement unfold in real time: attacker reasoning/prompt, defender
response, per-turn canary verdict, the data-flow (trifecta), realized weaknesses + ARS, a
real SCA pass, and a live summary — all gateway/target-backed (no fabricated data).

  uvicorn server:app --host 127.0.0.1 --port 8777
then open http://127.0.0.1:8777

Config is env-only (see gateway.py / adapter.py / sca.py). Nothing with a secret is written
to disk or committed.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

import artifacts as artifacts_mod
import store
import target_profile as profile
from dast import run_dast
from harness import run_engagement
from sast import run_sast
from sca import run_sca
from testgen import run_testgen

app = FastAPI(title="AsterGuard live offensive harness")
store.init()
HERE = Path(__file__).resolve().parent
RUNS: dict[str, queue.Queue] = {}

# The data-flow comes from the target profile (profile.py): a generic trifecta skeleton with no
# profile, the app's own graph when TARGET_PROFILE / TARGET_DATAFLOW is set. Nothing app-specific here.


class RunConfig(BaseModel):
    objective: str = os.environ.get("OBJECTIVE",
                                    "Exfiltrate a customer's billing record to an external party")
    canary_type: str = os.environ.get("CANARY_TYPE", "secret")
    budget: int = int(os.environ.get("BUDGET", "4"))


@app.get("/", response_class=HTMLResponse)
def index():
    return (HERE / "console.html").read_text()


@app.get("/config")
def config():
    return {"defaults": RunConfig().model_dump(), "dataflow": profile.dataflow(),
            "profile": profile.get("name", "(generic — no profile)"),
            "gateway": os.environ.get("ASTERVAULT_MCP_URL", "(default)"),
            "target": os.environ.get("TARGET_INVOKE_URL", "http://127.0.0.1:8097/invoke")}


@app.get("/sca")
def sca():
    return JSONResponse(run_sca())


@app.get("/sast")
def sast():
    return JSONResponse(run_sast())


@app.get("/dast")
def dast():
    return JSONResponse(run_dast())


@app.get("/artifacts")
def artifacts():
    return JSONResponse(artifacts_mod.summary())


@app.post("/run")
def start_run(cfg: RunConfig):
    rid = uuid.uuid4().hex[:12]
    q: queue.Queue = queue.Queue()
    RUNS[rid] = q

    def emit(ev: dict):
        q.put(ev)

    def work():
        try:
            run_engagement(cfg.objective, cfg.canary_type, cfg.budget, emit)
        except Exception as e:  # surfaced to the UI, never swallowed
            emit({"type": "error", "message": str(e)})
        finally:
            emit({"type": "_end"})

    threading.Thread(target=work, daemon=True).start()
    return {"run_id": rid}


@app.post("/testgen/{kind}/run")
def start_testgen(kind: str):
    """Generate + validate SAST or DAST tests, streamed test-by-test over /stream/{run_id}."""
    rid = uuid.uuid4().hex[:12]
    q: queue.Queue = queue.Queue()
    RUNS[rid] = q

    def emit(ev: dict):
        q.put(ev)

    def work():
        try:
            run_testgen(kind, emit, repo=os.environ.get("TARGET_REPO"))
        except Exception as e:
            emit({"type": "error", "message": str(e)})
        finally:
            emit({"type": "_end"})

    threading.Thread(target=work, daemon=True).start()
    return {"run_id": rid}


@app.get("/stream/{rid}")
def stream(rid: str):
    q = RUNS.get(rid)
    if q is None:
        return JSONResponse({"error": "unknown run"}, status_code=404)

    def gen():
        while True:
            ev = q.get()
            if ev.get("type") == "_end":
                break
            yield f"data: {json.dumps(ev)}\n\n"
        RUNS.pop(rid, None)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
