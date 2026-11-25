"""Hermetic tests for the artifacts aggregators (pure roll-ups over scan + engagement dicts)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import artifacts  # noqa: E402


class Aggregators(unittest.TestCase):
    def test_findings_rolls_up_severity_across_sources_and_behavioral(self):
        scan = {"findings": [{"severity": "critical"}, {"severity": "high"}]}      # sca
        sast = {"findings": [{"severity": "high"}, {"severity": "low"}]}
        dast = {"findings": [{"severity": "medium"}]}
        engagements = [
            {"id": "e1", "verdict": "broke", "ars": {"band": "critical"},
             "weakness": {"weakness_id": "llm_pii_exfil"}},
            {"id": "e2", "verdict": "held"},                                        # ignored
        ]
        f = artifacts.findings(engagements, scan, sast, dast)
        self.assertEqual(f["sca"], 2)
        self.assertEqual(f["sast"], 2)
        self.assertEqual(f["dast"], 1)
        self.assertEqual(f["behavioral"], 1)          # only the broke one
        self.assertEqual(f["total"], 2 + 2 + 1 + 1)
        self.assertEqual(f["crit"], 2)                # one sca critical + one behavioral critical band
        self.assertEqual(f["high"], 2)

    def test_behavioral_band_defaults_to_high_without_ars(self):
        f = artifacts.findings([{"id": "e", "verdict": "broke"}], {}, {}, {})
        self.assertEqual(f["high"], 1)
        self.assertEqual(f["behavioral"], 1)

    def test_security_graph_counts_unique_cwes_and_runtime_weaknesses(self):
        bom = {"count": 4}
        scan = {"findings": [{"cwe": "CWE-79"}, {"cwes": ["CWE-89", "CWE-79"]}]}    # CWE-79 dup
        engagements = [{"weakness": {"weakness_id": "llm_pii_exfil"}},
                       {"weakness": {"weakness_id": "llm_pii_exfil"}}]              # dup weakness
        g = artifacts.security_graph(bom, scan, {}, {}, engagements)
        self.assertEqual(sorted(g["cwes"]), ["CWE-79", "CWE-89"])
        self.assertEqual(g["runtime_weaknesses"], ["llm_pii_exfil"])
        self.assertEqual(g["components"], 4 + 6)       # bom + trifecta nodes
        self.assertEqual(g["weaknesses"], 2 + 1)       # unique cwes + unique runtime weaknesses

    def test_archived_reviews_caps_at_25(self):
        engs = [{"id": f"e{i}", "verdict": "held", "objective": "o", "asr_value": 0.0,
                 "attacker_model": "m", "ts": float(i)} for i in range(40)]
        a = artifacts.archived_reviews(engs)
        self.assertEqual(a["count"], 40)
        self.assertEqual(len(a["items"]), 25)

    def test_host_extraction(self):
        self.assertEqual(artifacts._host("https://gw.example.com/mcp"), "gw.example.com")
        self.assertEqual(artifacts._host("127.0.0.1:8097"), "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
