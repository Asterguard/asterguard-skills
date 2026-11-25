"""Hermetic tests for the grounded (dependency-free) SAST ruleset — real matches, no semgrep."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sast  # noqa: E402

VULN = '''\
import subprocess
def run(cmd):
    subprocess.run(cmd, shell=True)          # CWE-78
def danger(code):
    eval(code)                               # CWE-95
def fetch():
    import requests
    requests.get(url, verify=False)          # CWE-295
# eval(ignored_in_comment)                   <- comment, must NOT match

@app.get("/admin/export")                    # CWE-306 sensitive route
def export():
    return dump()
'''


class Grounded(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        (Path(self.dir) / "app.py").write_text(VULN)
        # a file inside a skipped dir must be ignored
        skip = Path(self.dir) / "node_modules"
        skip.mkdir()
        (skip / "bad.py").write_text("eval(x)\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_grounded_finds_real_sinks_with_cwes(self):
        res = sast._grounded(Path(self.dir))
        self.assertEqual(res["scanner"], "grounded-rules")
        ids = {f["id"] for f in res["findings"]}
        self.assertIn("py.subprocess.shell", ids)
        self.assertIn("py.exec.dynamic", ids)
        self.assertIn("py.tls.verify-disabled", ids)
        self.assertIn("web.route.unauth-sensitive", ids)
        cwes = {f["cwe"] for f in res["findings"]}
        self.assertTrue({"CWE-78", "CWE-95", "CWE-295", "CWE-306"} <= cwes)

    def test_comment_line_not_flagged_and_skip_dirs_ignored(self):
        res = sast._grounded(Path(self.dir))
        # only the eval in app.py (line inside def danger), not the comment and not node_modules
        evals = [f for f in res["findings"] if f["id"] == "py.exec.dynamic"]
        self.assertEqual(len(evals), 1)
        self.assertEqual(evals[0]["file"], "app.py")

    def test_findings_sorted_critical_first(self):
        res = sast._grounded(Path(self.dir))
        sevs = [f["severity"] for f in res["findings"]]
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.assertEqual(sevs, sorted(sevs, key=lambda s: order.get(s, 9)))

    def test_run_sast_missing_repo(self):
        res = sast.run_sast("/no/such/path/xyz")
        self.assertFalse(res["ok"])
        self.assertEqual(res["findings"], [])

    def test_cwe_helper_normalizes(self):
        self.assertEqual(sast._cwe({"cwe": ["CWE-89: SQLi"]}), "CWE-89")
        self.assertEqual(sast._cwe({"cwe": "CWE-78"}), "CWE-78")
        self.assertEqual(sast._cwe({}), "")


if __name__ == "__main__":
    unittest.main()
