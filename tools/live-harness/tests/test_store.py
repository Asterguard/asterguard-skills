"""Hermetic tests for the engagement store (SQLite round-trip)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store  # noqa: E402


def _rec(id="eng_1", verdict="broke", **over):
    base = {
        "id": id, "ts": 1700000000.0, "objective": "exfil", "target": "http://t/invoke",
        "verdict": verdict, "asr_value": 1.0, "budget": 5, "first_break_turn": 2,
        "canary_type": "egress", "canary_token": "tok_1", "attacker_model": "gw/det",
        "defender_model": "gpt-4o-mini", "audit_ids": ["a1", "a2"],
        "weakness": {"weakness_id": "llm_pii_exfil"}, "ars": {"ars": 8.1, "band": "high"},
        "transcript": [{"role": "attacker", "content": "hi"}],
    }
    base.update(over)
    return base


class Store(unittest.TestCase):
    def setUp(self):
        t = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        t.close()
        self.path = t.name
        self._orig = store.DB
        store.DB = self.path

    def tearDown(self):
        store.DB = self._orig
        os.unlink(self.path)

    def test_save_and_roundtrip_json_columns(self):
        store.save(_rec())
        rows = store.all_engagements()
        self.assertEqual(len(rows), 1)
        r = rows[0]
        # json columns come back as parsed python, not strings
        self.assertEqual(r["audit_ids"], ["a1", "a2"])
        self.assertEqual(r["weakness"]["weakness_id"], "llm_pii_exfil")
        self.assertEqual(r["ars"]["band"], "high")
        self.assertEqual(r["transcript"][0]["role"], "attacker")
        self.assertEqual(r["verdict"], "broke")

    def test_insert_or_replace_dedups_by_id(self):
        store.save(_rec(id="eng_x", verdict="held"))
        store.save(_rec(id="eng_x", verdict="broke"))  # same id -> replace
        rows = store.all_engagements()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["verdict"], "broke")

    def test_ordered_newest_first(self):
        store.save(_rec(id="old", ts=100.0))
        store.save(_rec(id="new", ts=200.0))
        ids = [r["id"] for r in store.all_engagements()]
        self.assertEqual(ids, ["new", "old"])

    def test_all_on_empty_db_is_empty_list(self):
        self.assertEqual(store.all_engagements(), [])


if __name__ == "__main__":
    unittest.main()
