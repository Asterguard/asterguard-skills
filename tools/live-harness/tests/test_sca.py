"""Hermetic tests for SCA manifest parsing and run_sca's no-network branches.

The OSV query (_osv) hits the network and is NOT exercised here; these cover the pure
manifest parsing and the early-return branches that never reach the network.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sca  # noqa: E402

_ENV = ("TARGET_REQUIREMENTS", "TARGET_PROFILE", "TARGET_REPO")


class SCA(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in _ENV}
        for k in _ENV:
            os.environ.pop(k, None)
        self._tmp = []

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for f in self._tmp:
            try:
                os.unlink(f)
            except OSError:
                pass

    def _manifest(self, text):
        t = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
        t.write(text)
        t.close()
        self._tmp.append(t.name)
        return t.name

    def test_parse_pins_only(self):
        m = self._manifest(
            "flask==2.0.1\n"
            "requests==2.31.0  # with a comment\n"
            "\n"
            "unpinned-package\n"            # not pinned -> ignored
            "other>=1.0\n"                  # range -> ignored
            "Jinja2==3.1.2\n")
        pins = sca._parse(m)
        self.assertEqual(pins, [("flask", "2.0.1"), ("requests", "2.31.0"), ("Jinja2", "3.1.2")])

    def test_run_sca_no_manifest_configured(self):
        res = sca.run_sca(None)          # nothing in env/profile -> clean empty result
        self.assertTrue(res["ok"])
        self.assertEqual(res["package_count"], 0)
        self.assertEqual(res["findings"], [])

    def test_run_sca_manifest_not_found(self):
        res = sca.run_sca("/no/such/requirements.txt")
        self.assertFalse(res["ok"])
        self.assertIn("not found", res["reason"])

    def test_run_sca_no_pins_short_circuits_before_network(self):
        m = self._manifest("unpinned\nalso-unpinned>=2\n")
        res = sca.run_sca(m)             # returns before any OSV call
        self.assertFalse(res["ok"])
        self.assertIn("no pinned", res["reason"])


if __name__ == "__main__":
    unittest.main()
