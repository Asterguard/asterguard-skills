"""Hermetic tests for the target adapter — egress parsing and the sqlite canary plant."""
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ENV = ("TARGET_INVOKE_URL", "TARGET_DB", "TARGET_EGRESS_LOG", "TARGET_PROFILE",
        "TARGET_PLANT_TABLE", "TARGET_PLANT_COLUMN", "TARGET_PLANT_ROW_ID")


class Adapter(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in _ENV}
        for k in _ENV:
            os.environ.pop(k, None)
        self._tmpfiles = []

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for f in self._tmpfiles:
            try:
                os.unlink(f)
            except OSError:
                pass

    def _tmp(self, suffix=""):
        t = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        t.close()
        self._tmpfiles.append(t.name)
        return t.name

    def _adapter(self):
        import importlib
        import target_profile
        importlib.reload(target_profile)   # re-read env-driven profile
        import adapter
        importlib.reload(adapter)
        return adapter.TargetAdapter()

    def test_read_egress_parses_jsonl_bodies_and_plain_lines(self):
        log = self._tmp(".jsonl")
        with open(log, "w") as fh:
            fh.write(json.dumps({"body": "first leak"}) + "\n")
            fh.write("\n")                      # blank line ignored
            fh.write("raw non-json line\n")     # kept verbatim
            fh.write(json.dumps({"body": "second leak"}) + "\n")
        os.environ["TARGET_EGRESS_LOG"] = log
        a = self._adapter()
        out = a.read_egress()
        self.assertIn("first leak", out)
        self.assertIn("second leak", out)
        self.assertIn("raw non-json line", out)

    def test_read_egress_empty_when_unset(self):
        self.assertEqual(self._adapter().read_egress(), "")

    def test_clear_egress_truncates(self):
        log = self._tmp(".jsonl")
        with open(log, "w") as fh:
            fh.write(json.dumps({"body": "leak"}) + "\n")
        os.environ["TARGET_EGRESS_LOG"] = log
        a = self._adapter()
        self.assertIn("leak", a.read_egress())
        a.clear_egress()
        self.assertEqual(a.read_egress(), "")

    def test_plant_writes_canary_into_sqlite_row(self):
        db = self._tmp(".db")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE customers(id INTEGER PRIMARY KEY, bank_account TEXT)")
        con.execute("INSERT INTO customers(id, bank_account) VALUES (1, 'original')")
        con.commit()
        con.close()
        os.environ["TARGET_DB"] = db           # presence selects the sqlite plant kind
        a = self._adapter()
        where = a.plant("CANARY-XYZ")
        self.assertIn("customers.bank_account", where)
        con = sqlite3.connect(db)
        val = con.execute("SELECT bank_account FROM customers WHERE id=1").fetchone()[0]
        con.close()
        self.assertEqual(val, "CANARY-XYZ")

    def test_plant_is_noop_without_db(self):
        a = self._adapter()                    # no TARGET_DB -> kind 'none'
        msg = a.plant("CANARY-XYZ")
        self.assertIn("gateway-registered only", msg)


if __name__ == "__main__":
    unittest.main()
