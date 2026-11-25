"""Regression tests for the drift toolkit — the v1 (safe) -> v2 (regressed) fixture must
produce the expected signals, the cause->effect links must fire, and the aggregate must
land in critical-regression. Pure stdlib unittest; no network.

Run:  python -m unittest discover -s tools/drift/tests
  or: python tools/drift/tests/test_drift.py
"""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)  # import the comparators as top-level modules

import behavior_drift  # noqa: E402
import controls_drift  # noqa: E402
import drift  # noqa: E402
import explain  # noqa: E402
import model_drift  # noqa: E402
import prompt_drift  # noqa: E402
import sbom_drift  # noqa: E402
import surface_drift  # noqa: E402
import tool_drift  # noqa: E402
from common import load_json, load_runs, load_signals  # noqa: E402

V1 = os.path.join(HERE, "fixtures", "v1")
V2 = os.path.join(HERE, "fixtures", "v2")


def _sig(delta):
    return set(delta["signals"])


class SignalsConfig(unittest.TestCase):
    def test_ssot_loads_and_has_core_keys(self):
        cfg = load_signals()
        self.assertIn("signals", cfg)
        self.assertIn("links", cfg)
        self.assertIn("bands", cfg)
        # a representative signal carries direction + weight
        self.assertEqual(cfg["signals"]["approval_disabled"]["direction"], "worse")
        self.assertGreater(float(cfg["signals"]["approval_disabled"]["weight"]), 0)
        # a link is a mapping with cause list + effect
        link = cfg["links"][0]
        self.assertIsInstance(link["cause"], list)
        self.assertIn("effect", link)


class Comparators(unittest.TestCase):
    def setUp(self):
        self.pa = load_json(os.path.join(V1, "profile.json"))
        self.pb = load_json(os.path.join(V2, "profile.json"))

    def test_prompt_drift_flags_weakened_guardrail_and_injection(self):
        d = prompt_drift.compare(self.pa["system_prompt"], self.pb["system_prompt"])
        self.assertIn("weakened_guardrail", _sig(d))
        self.assertIn("new_injectable_surface", _sig(d))
        self.assertEqual(d["direction"], "worse")

    def test_tool_drift_flags_egress_approval_scope_privilege(self):
        d = tool_drift.compare(self.pa, self.pb)
        self.assertIn("new_egress_tool", _sig(d))        # send_webhook
        self.assertIn("approval_disabled", _sig(d))       # export_record gate off
        self.assertIn("tool_scope_broadened", _sig(d))    # export_record reach grew
        self.assertIn("over_privileged_appeared", _sig(d))

    def test_controls_drift_flags_removed_loosened_widened_reopened(self):
        d = controls_drift.compare(self.pa, self.pb)
        self.assertIn("control_removed", _sig(d))             # approval-gate gone
        self.assertIn("control_loosened", _sig(d))            # egress-allowlist -> advisory
        self.assertIn("allowlist_widened", _sig(d))
        self.assertIn("missing_control_reappeared", _sig(d))

    def test_model_drift_flags_less_restricted(self):
        d = model_drift.compare(self.pa, self.pb)
        self.assertIn("model_changed", _sig(d))
        self.assertIn("model_less_restricted", _sig(d))

    def test_surface_drift_flags_path_reach_sink_and_ars(self):
        d = surface_drift.compare(load_json(os.path.join(V1, "surface.json")),
                                  load_json(os.path.join(V2, "surface.json")))
        self.assertIn("new_attack_path", _sig(d))
        self.assertIn("new_reach_regulated", _sig(d))   # financial class
        self.assertIn("new_egress_sink", _sig(d))
        self.assertAlmostEqual(d["ars_delta"]["change"], 2.9, places=2)

    def test_behavior_drift_flags_new_break_and_asr(self):
        d = behavior_drift.compare(load_runs(os.path.join(V1, "runs")),
                                   load_runs(os.path.join(V2, "runs")))
        self.assertIn("new_break", _sig(d))
        self.assertIn("asr_increased", _sig(d))
        self.assertIn("refusal_dropped", _sig(d))
        self.assertGreater(d["asr_posterior"]["b"]["mean"], d["asr_posterior"]["a"]["mean"])

    def test_sbom_drift_flags_kev_and_growth(self):
        d = sbom_drift.compare(load_json(os.path.join(V1, "sbom.json")),
                               load_json(os.path.join(V2, "sbom.json")))
        self.assertIn("new_kev", _sig(d))
        self.assertIn("cve_surface_grew", _sig(d))
        self.assertIn("dependency_added", _sig(d))


class Composer(unittest.TestCase):
    def setUp(self):
        self.report = drift.build_report(V1, V2)

    def test_aggregate_is_critical_regression(self):
        self.assertEqual(self.report["aggregate"]["direction"], "worse")
        self.assertEqual(self.report["aggregate"]["band"], "critical-regression")

    def test_causes_and_effects_grouped(self):
        cause_facets = {d["facet"] for d in self.report["causes"]}
        effect_facets = {d["facet"] for d in self.report["effects"]}
        self.assertTrue({"prompt", "tools", "controls", "model"} <= cause_facets)
        self.assertTrue({"surface", "behavior", "sbom"} <= effect_facets)

    def test_cause_effect_links_fire(self):
        fired = {(tuple(l["cause"]), l["effect"]) for l in self.report["links_fired"]}
        # removed approval + new egress tool -> new attack path
        self.assertIn((("new_egress_tool", "approval_disabled"), "new_attack_path"), fired)
        # weakened guardrail -> new behavioral break
        self.assertIn((("weakened_guardrail",), "new_break"), fired)
        self.assertTrue(self.report["narrative"], "expected at least one narrative line")

    def test_offline_mode_has_no_calibrated_index(self):
        self.assertEqual(self.report["calibration"]["mode"], "offline")
        self.assertIsNone(self.report["calibration"]["index"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
