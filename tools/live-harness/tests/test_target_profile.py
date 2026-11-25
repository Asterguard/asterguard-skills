"""Hermetic tests for target_profile — env/profile resolution and generic defaults."""
import importlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ENV = ("TARGET_PROFILE", "TARGET_TOOLS", "TARGET_DB", "TARGET_REQUIREMENTS",
        "TARGET_PLANT_TABLE", "TARGET_PLANT_COLUMN", "TARGET_PLANT_ROW_ID", "TARGET_REPO",
        "TARGET_DATAFLOW")


class TargetProfile(unittest.TestCase):
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

    def _tmp(self, text, suffix=""):
        t = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w")
        t.write(text)
        t.close()
        self._tmpfiles.append(t.name)
        return t.name

    def _mod(self):
        import target_profile
        return importlib.reload(target_profile)   # re-read env at import

    def test_defaults_without_profile(self):
        p = self._mod()
        self.assertEqual(p.tools(), [])
        self.assertEqual(p.dataflow(), p.GENERIC_DATAFLOW)
        self.assertEqual(p.sensitive_paths(), p.GENERIC_SENSITIVE_PATHS)
        self.assertIsNone(p.requirements())

    def test_plant_config_none_then_sqlite(self):
        p = self._mod()
        self.assertEqual(p.plant_config()["kind"], "none")
        os.environ["TARGET_DB"] = "/tmp/whatever.db"
        self.assertEqual(p.plant_config()["kind"], "sqlite")

    def test_plant_config_honors_env_overrides(self):
        os.environ["TARGET_PLANT_TABLE"] = "accounts"
        os.environ["TARGET_PLANT_COLUMN"] = "iban"
        os.environ["TARGET_PLANT_ROW_ID"] = "7"
        cfg = self._mod().plant_config()
        self.assertEqual((cfg["table"], cfg["column"], cfg["row_id"]), ("accounts", "iban", "7"))

    def test_tools_from_env_csv(self):
        os.environ["TARGET_TOOLS"] = "search, send_email ,, export_record"
        self.assertEqual(self._mod().tools(), ["search", "send_email", "export_record"])

    def test_profile_json_drives_tools_and_paths(self):
        prof = self._tmp(json.dumps({"tools": ["lookup", "pay"],
                                     "sensitive_paths": ["/secret"]}), ".json")
        os.environ["TARGET_PROFILE"] = prof
        p = self._mod()
        self.assertEqual(p.tools(), ["lookup", "pay"])
        self.assertEqual(p.sensitive_paths(), ["/secret"])

    def test_bad_profile_json_falls_back_to_defaults(self):
        prof = self._tmp("{not valid json", ".json")
        os.environ["TARGET_PROFILE"] = prof
        p = self._mod()
        self.assertEqual(p.tools(), [])
        self.assertEqual(p.dataflow(), p.GENERIC_DATAFLOW)

    def test_requirements_env_wins(self):
        req = self._tmp("flask==2.0.0\n", ".txt")
        os.environ["TARGET_REQUIREMENTS"] = req
        self.assertEqual(self._mod().requirements(), req)


if __name__ == "__main__":
    unittest.main()
