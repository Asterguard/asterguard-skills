"""Hermetic tests for the DAST probe engine — against a throwaway localhost server (no external net)."""
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dast  # noqa: E402

_LEAK = {"customers": [{"id": 1, "bank_account": "XXXX"} for _ in range(10)]}  # >80 bytes of json
_OPENAPI = {"paths": {"/invoke": {}, "/admin/export": {}, "/debug": {}}}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        payload = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/admin/export":
            self._send(200, json.dumps(_LEAK))
        elif self.path == "/openapi.json":
            self._send(200, json.dumps(_OPENAPI))
        else:
            self._send(404, "{}")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        # malformed-body probe -> emulate an unhandled 500 with a python traceback
        self._send(500, 'Traceback (most recent call last):\n  File "app.py", line 1\nValueError',
                   ctype="text/plain")


class DAST(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("TARGET_INVOKE_URL", "TARGET_PROFILE",
                                                       "TARGET_BASE_URL")}
        os.environ.pop("TARGET_PROFILE", None)
        os.environ.pop("TARGET_BASE_URL", None)
        os.environ["TARGET_INVOKE_URL"] = f"{self.base}/invoke"

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_detects_all_three_probe_classes(self):
        res = dast.run_dast(self.base)
        self.assertTrue(res["ok"])
        self.assertTrue(res["reachable"])
        ids = {f["id"] for f in res["findings"]}
        self.assertIn("dast.unauth-data-endpoint", ids)      # /admin/export returns data unauthenticated
        self.assertIn("dast.exposed-sensitive-routes", ids)  # openapi advertises admin/debug
        self.assertIn("dast.error-stacktrace-leak", ids)     # malformed POST -> 500 + traceback

    def test_findings_carry_evidence_and_cwe(self):
        res = dast.run_dast(self.base)
        unauth = next(f for f in res["findings"] if f["id"] == "dast.unauth-data-endpoint")
        self.assertEqual(unauth["cwe"], "CWE-306")
        self.assertEqual(unauth["status"], 200)
        self.assertIn("no auth", unauth["evidence"])

    def test_base_derivation_from_invoke_url(self):
        os.environ.pop("TARGET_BASE_URL", None)
        os.environ["TARGET_INVOKE_URL"] = "http://host.example:9000/invoke"
        self.assertEqual(dast._base(), "http://host.example:9000")


if __name__ == "__main__":
    unittest.main()
