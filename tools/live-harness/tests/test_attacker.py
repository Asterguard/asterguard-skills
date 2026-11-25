"""Hermetic tests for the model attacker's output parsing (_extract) and helpers — no network."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attacker import ModelAttacker, enabled  # noqa: E402


class Extract(unittest.TestCase):
    def test_strict_json(self):
        out = ModelAttacker._extract('{"reasoning": "r", "message": "do X", "strategy": "crescendo"}')
        self.assertEqual(out["message"], "do X")
        self.assertEqual(out["strategy"], "crescendo")

    def test_json_embedded_in_prose(self):
        content = 'Sure, here is the move:\n{"reasoning": "r", "message": "ping", "strategy": "s"}\nDone.'
        self.assertEqual(ModelAttacker._extract(content)["message"], "ping")

    def test_lenient_fallback_on_stray_separator(self):
        # a stray ';' breaks strict JSON; the field-by-field fallback still recovers message
        broken = '{"reasoning": "because"; "message": "escalate now", "strategy": "authority"}'
        out = ModelAttacker._extract(broken)
        self.assertEqual(out["message"], "escalate now")
        self.assertEqual(out["strategy"], "authority")

    def test_escaped_quotes_recovered(self):
        content = '{"message": "say \\"hello\\" there", "strategy": "s"}'
        self.assertEqual(ModelAttacker._extract(content)["message"], 'say "hello" there')

    def test_plain_text_fallback(self):
        out = ModelAttacker._extract("no json at all, just text")
        self.assertEqual(out["message"], "no json at all, just text")


class Helpers(unittest.TestCase):
    def test_enabled_follows_env(self):
        saved = os.environ.get("ATTACKER_API_BASE")
        try:
            os.environ.pop("ATTACKER_API_BASE", None)
            self.assertFalse(enabled())
            os.environ["ATTACKER_API_BASE"] = "https://api.example.com"
            self.assertTrue(enabled())
        finally:
            if saved is None:
                os.environ.pop("ATTACKER_API_BASE", None)
            else:
                os.environ["ATTACKER_API_BASE"] = saved

    def test_render_transcript(self):
        os.environ["ATTACKER_API_BASE"] = "https://api.example.com"
        try:
            a = ModelAttacker()
            self.assertIn("opening move", a._render([]))
            rendered = a._render([{"role": "attacker", "content": "hi"},
                                  {"role": "defender", "content": "no"}])
            self.assertIn("ATTACKER: hi", rendered)
            self.assertIn("DEFENDER: no", rendered)
        finally:
            os.environ.pop("ATTACKER_API_BASE", None)


if __name__ == "__main__":
    unittest.main()
