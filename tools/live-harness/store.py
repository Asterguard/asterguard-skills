"""Local engagement store (SQLite) — the scans/runs populate it; the artifacts panel reads it.

Every offensive engagement the harness runs is persisted here (verdict, ASR, canary, realized
weakness + ARS, audit_ids, full transcript). The Artifacts panel's Findings / Security graph /
Archived reviews are aggregated from this store plus the live SCA — nothing is hand-entered.

  ENGAGEMENT_DB   path to the sqlite file (default: ./engagements.db next to this module)
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DB = os.environ.get("ENGAGEMENT_DB") or str(Path(__file__).resolve().parent / "engagements.db")
_JSON_COLS = ("audit_ids", "weakness", "ars", "transcript")


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = _conn()
    c.execute("""CREATE TABLE IF NOT EXISTS engagements(
        id TEXT PRIMARY KEY, ts REAL, objective TEXT, target TEXT, verdict TEXT,
        asr_value REAL, budget INTEGER, first_break_turn INTEGER,
        canary_type TEXT, canary_token TEXT, attacker_model TEXT, defender_model TEXT,
        audit_ids TEXT, weakness TEXT, ars TEXT, transcript TEXT)""")
    c.commit()
    c.close()


def save(rec: dict):
    init()
    c = _conn()
    c.execute("""INSERT OR REPLACE INTO engagements VALUES
        (:id,:ts,:objective,:target,:verdict,:asr_value,:budget,:first_break_turn,
         :canary_type,:canary_token,:attacker_model,:defender_model,:audit_ids,:weakness,:ars,:transcript)""",
              {**rec, **{k: json.dumps(rec.get(k)) for k in _JSON_COLS}})
    c.commit()
    c.close()


def all_engagements() -> list[dict]:
    init()
    c = _conn()
    rows = [dict(r) for r in c.execute("SELECT * FROM engagements ORDER BY ts DESC")]
    c.close()
    for r in rows:
        for k in _JSON_COLS:
            try:
                r[k] = json.loads(r[k]) if r[k] else None
            except (ValueError, TypeError):
                pass
    return rows
