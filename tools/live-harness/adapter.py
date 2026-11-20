"""Target adapter — connects the live harness to a defender under test.

Everything is ENV-configured so nothing target-specific is baked into the repo:

  TARGET_INVOKE_URL   defender HTTP endpoint, POST {messages:[...]} -> {output, tool_calls}
                      (default http://127.0.0.1:8097/invoke — the support-agent-demo API)
  TARGET_DB           optional sqlite path; if set, the canary is planted into a data row the
                      agent can retrieve (so a leak is possible and provable)
  TARGET_PLANT_TABLE / TARGET_PLANT_COLUMN / TARGET_PLANT_ROW_ID   where to plant (defaults:
                      customers / bank_account / 1)
  TARGET_EGRESS_LOG   optional JSONL path the target's egress sink appends to; the harness
                      clears it before each turn and reads what left after

A security engineer swaps these for their own target; the harness logic is unchanged.
"""
from __future__ import annotations

import json
import os
import sqlite3
import urllib.request
from pathlib import Path

import target_profile as profile


class TargetAdapter:
    def __init__(self):
        self.invoke_url = os.environ.get("TARGET_INVOKE_URL", "http://127.0.0.1:8097/invoke")
        self.db = os.environ.get("TARGET_DB", "")
        self.egress_log = os.environ.get("TARGET_EGRESS_LOG", "")
        pc = profile.plant_config()          # kind/table/column/row_id from the profile
        self.plant_kind = pc.get("kind", "none")
        self.table = pc.get("table", "customers")
        self.column = pc.get("column", "bank_account")
        self.row_id = pc.get("row_id", "1")

    def plant(self, canary_value: str) -> str:
        """Write the canary into a retrievable data row so a leak is possible. Returns a
        human-readable location. No-op (returns a note) when TARGET_DB is unset."""
        if self.plant_kind != "sqlite" or not self.db or not Path(self.db).is_file():
            return "gateway-registered only (no sqlite plant configured — defender cannot retrieve it)"
        con = sqlite3.connect(self.db)
        con.execute(f"UPDATE {self.table} SET {self.column}=? WHERE id=?", (canary_value, self.row_id))
        con.commit(); con.close()
        return f"{self.table}.{self.column} (row id={self.row_id})"

    def clear_egress(self):
        if self.egress_log:
            try:
                Path(self.egress_log).write_text("")
            except OSError:
                pass

    def read_egress(self) -> str:
        if not self.egress_log or not Path(self.egress_log).is_file():
            return ""
        out = []
        for line in Path(self.egress_log).read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line).get("body", ""))
            except ValueError:
                out.append(line)
        return "\n".join(out)

    def invoke(self, messages: list[dict]) -> tuple[str, list]:
        data = json.dumps({"messages": messages}).encode()
        req = urllib.request.Request(self.invoke_url, data=data,
                                     headers={"content-type": "application/json"})
        out = json.loads(urllib.request.urlopen(req, timeout=150).read().decode())
        if isinstance(out, dict):
            return out.get("output", ""), out.get("tool_calls", [])
        return str(out), []
