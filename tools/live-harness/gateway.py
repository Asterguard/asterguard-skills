"""Portable AsterVault gateway client (MCP Streamable-HTTP over JSON-RPC).

Connects to a running AsterVault gateway and drives the behavioral-harness tools
(offensive.* + canary.*) brokered and audited — every call returns an audit_id, and
canary.verify is the gateway's INDEPENDENT verifier (never the attacker's or defender's
self-report).

Configuration is ENV-ONLY — no secrets in code:
  ASTERVAULT_MCP_URL     gateway MCP endpoint (default: https://astervault.agenticrisklabs.io/mcp)
  ASTERVAULT_BEARER      base-identity bearer JWT (must carry the offensive entitlement), OR
  ASTERVAULT_BEARER_FILE path to a file containing that bearer (read at runtime)

Nothing here is written back to disk; the bearer is read once at construction and never logged.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request

DEFAULT_URL = "https://astervault.agenticrisklabs.io/mcp"

# Verify TLS against certifi's CA bundle when available (some venvs lack a system CA store),
# else the platform default. Never disables verification.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:  # certifi absent -> platform default trust store
    _SSL_CTX = ssl.create_default_context()


def _load_bearer() -> str:
    tok = os.environ.get("ASTERVAULT_BEARER")
    if tok:
        return tok.strip()
    path = os.environ.get("ASTERVAULT_BEARER_FILE")
    if path and os.path.isfile(path):
        with open(path) as fh:
            return fh.read().strip()
    raise RuntimeError("set ASTERVAULT_BEARER or ASTERVAULT_BEARER_FILE (gateway bearer JWT)")


class GatewayError(RuntimeError):
    pass


class Gateway:
    def __init__(self, url: str | None = None):
        self.url = url or os.environ.get("ASTERVAULT_MCP_URL") or DEFAULT_URL
        self._bearer = _load_bearer()
        self._session_id: str | None = None
        self._offensive: str | None = None
        self._id = 0
        self._names: dict[str, str] = {}

    # ---- MCP Streamable-HTTP ----
    def _post(self, payload: dict, extra_headers: dict | None = None):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self._bearer}",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode(), headers=headers)
        try:
            resp = urllib.request.urlopen(req, timeout=90, context=_SSL_CTX)
        except urllib.error.HTTPError as e:
            raise GatewayError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}") from None
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            self._session_id = sid
        raw = resp.read().decode("utf-8", "replace")
        if not raw.strip():
            return None
        if "text/event-stream" in resp.headers.get("Content-Type", ""):
            out = None
            for line in raw.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    chunk = line[5:].strip()
                    if chunk and chunk != "[DONE]":
                        out = json.loads(chunk)
            return out
        return json.loads(raw)

    def _rpc(self, method: str, params: dict | None = None, extra_headers: dict | None = None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        res = self._post(msg, extra_headers)
        if res and isinstance(res, dict) and res.get("error"):
            raise GatewayError(f"{method}: {json.dumps(res['error'])[:400]}")
        return (res or {}).get("result")

    @staticmethod
    def _unwrap(env):
        if isinstance(env, dict) and "data" in env and ("ok" in env or "denied_reason" in env):
            aid = env.get("audit_id")
            inner = env.get("data")
            if isinstance(inner, dict):
                m = dict(inner)
                if not m.get("audit_id") and aid:
                    m["audit_id"] = aid
                m.setdefault("_ok", env.get("ok"))
                m.setdefault("_denied", env.get("denied_reason"))
                return m
            return {"_ok": env.get("ok"), "_denied": env.get("denied_reason"), "audit_id": aid, "data": inner}
        return env

    def _parse(self, result: dict):
        if not result:
            return None
        if isinstance(result.get("structuredContent"), dict):
            sc = result["structuredContent"]
            return sc.get("result", sc)
        for item in (result.get("content") or []):
            if item.get("type") == "text":
                try:
                    return json.loads(item["text"])
                except (ValueError, KeyError):
                    return item.get("text")
        return result

    # ---- lifecycle ----
    def initialize(self):
        r = self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "live-harness", "version": "0.1"}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self._resolve_names([t["name"] for t in (self._rpc("tools/list", {}) or {}).get("tools", [])])
        return r

    def _resolve_names(self, names: list[str]):
        def find(*cands):
            for c in cands:
                if c in names:
                    return c
            for n in names:
                if any(n.replace(".", "_").endswith(c.replace(".", "_")) for c in cands):
                    return n
            return None
        for logical, dotted in [("offensive_token", "offensive.token"),
                                ("attacker_drive", "offensive.attacker_drive"),
                                ("defender_respond", "offensive.defender_respond"),
                                ("judge_verdict", "offensive.judge_verdict"),
                                ("canary_mint", "canary.mint"), ("canary_plant", "canary.plant"),
                                ("canary_scan", "canary.scan"), ("canary_verify", "canary.verify"),
                                ("risk_score", "risk.score")]:
            self._names[logical] = find(dotted, logical.replace("_", "."))

    def _n(self, logical: str) -> str:
        n = self._names.get(logical)
        if not n:
            raise GatewayError(f"tool {logical!r} not exposed by gateway")
        return n

    def tool(self, name: str, args: dict | None = None, *, offensive: bool = False):
        extra = {}
        if offensive:
            if not self._offensive:
                raise GatewayError("offensive token not minted")
            extra["X-ARS-Offensive-Token"] = self._offensive
        return self._unwrap(self._parse(self._rpc("tools/call", {"name": name, "arguments": args or {}}, extra)))

    # ---- behavioral-harness primitives ----
    def mint_offensive(self, ttl_seconds: int | None = None) -> dict:
        out = self.tool(self._n("offensive_token"), {"ttl_seconds": ttl_seconds} if ttl_seconds else {})
        tok = (out or {}).get("token") or (out or {}).get("value")
        if not tok or not str(tok).startswith("asg_off_"):
            raise GatewayError(f"offensive.token denied: {json.dumps(out)[:300]}")
        self._offensive = tok
        return out

    def attacker_drive(self, objective: str, transcript: list) -> dict:
        return self.tool(self._n("attacker_drive"), {"objective": objective, "transcript": transcript}, offensive=True)

    def judge_verdict(self, transcript: list, episode_id: str, canary_markers: list | None = None) -> dict:
        return self.tool(self._n("judge_verdict"),
                         {"transcript": transcript, "episode_id": episode_id,
                          "canary_markers": canary_markers or []}, offensive=True)

    def canary_mint(self, ctype: str, episode_id: str) -> dict:
        return self.tool(self._n("canary_mint"), {"type": ctype, "episode_id": episode_id}, offensive=True)

    def canary_plant(self, episode_id: str, token_id: str, location: str) -> dict:
        return self.tool(self._n("canary_plant"), {"episode_id": episode_id, "token_id": token_id, "location": location}, offensive=True)

    def canary_scan(self, episode_id: str, text: str) -> dict:
        return self.tool(self._n("canary_scan"), {"episode_id": episode_id, "text": text}, offensive=True)

    def canary_verify(self, episode_id: str) -> dict:
        return self.tool(self._n("canary_verify"), {"episode_id": episode_id}, offensive=True)

    def risk_score(self, finding: dict) -> dict:
        return self.tool(self._n("risk_score"), {"target": finding}, offensive=True)
