"""
AI-Native Engineering Framework - Example 03: Hardened Vertical Slice.
Unit tests verifying happy-path CLEAN emission, fail-closed HOLLOW prevention, FAILED input rejection,
type safety, and decision classification.
"""

import unittest
from pipeline import HardenedPipeline


class TestHardenedSlice(unittest.TestCase):
    def setUp(self):
        self.evidence_db = {
            "https://press.acme.example/k8s": "Acme Cloud announces complete migration of core infrastructure to Kubernetes.",
            "https://careers.globex.example/vp": "Globex Corp is hiring a Vice President of Enterprise Security.",
            "https://news.example/cafeteria": "BrightSolar won a green building cafeteria award.",
            "https://forums.example/eval": "Rumor that Nexus is evaluating new warehouse systems.",
        }
        self.pipeline = HardenedPipeline(evidence_store=self.evidence_db)

    def test_happy_path_clean_emission(self):
        raw_input = {
            "case_id": "CASE-101",
            "company": "  acme cloud  ",
            "signal": "Migrating core infrastructure to Kubernetes.",
            "source_url": "https://press.acme.example/k8s",
        }
        result = self.pipeline.run(raw_input)

        self.assertEqual(result.status, "CLEAN")
        self.assertIsNotNone(result.final_payload)
        self.assertEqual(result.final_payload["company"], "Acme Cloud")
        self.assertEqual(result.final_payload["decision"], "QUALIFY")
        self.assertIn("https://press.acme.example/k8s", result.final_payload["citations"])
        self.assertTrue(result.human_signoff_required)
        self.assertEqual(result.final_payload["human_approval_status"], "PENDING_REVIEW")

        # Verify all 6 stages recorded
        stage_names = [s.stage for s in result.stage_traces]
        self.assertEqual(stage_names, ["ingest", "normalize", "retrieve", "judge", "verify", "emit"])
        self.assertTrue(all(s.success for s in result.stage_traces))

    def test_fail_closed_missing_evidence(self):
        # Source URL has no matching evidence in store (e.g. 404 or unverified claim)
        raw_input = {
            "case_id": "CASE-102",
            "company": "Mystery Corp",
            "signal": "Rumored acquisition talks ongoing.",
            "source_url": "https://unverified-rumor.example/leak",
        }
        result = self.pipeline.run(raw_input)

        # Must trigger fail-closed gate and return FAILED with reason hollow_prevented
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.reason, "hollow_prevented")
        self.assertIsNone(result.final_payload)
        self.assertIn("Fail-closed gate triggered", result.error_message)

        # Stage trace stops at verify failure
        stages = {s.stage: s for s in result.stage_traces}
        self.assertTrue(stages["retrieve"].success)
        self.assertFalse(stages["retrieve"].data["has_evidence"])
        self.assertFalse(stages["verify"].success)
        self.assertNotIn("emit", stages)

    def test_fail_closed_empty_citation(self):
        raw_input = {
            "case_id": "CASE-103",
            "company": "Globex Corp",
            "signal": "Globex is hiring VP Security",
            "source_url": "",  # Empty citation
        }
        result = self.pipeline.run(raw_input)

        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.reason, "hollow_prevented")
        self.assertIsNone(result.final_payload)

    def test_failed_ingest_schema(self):
        # Malformed raw input (missing signal key)
        raw_input = {"company": "Acme Cloud"}
        result = self.pipeline.run(raw_input)

        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.reason, "invalid_schema")
        self.assertIsNone(result.final_payload)
        self.assertIn("Ingest validation failed", result.error_message)

    def test_ingest_type_safety_non_strings(self):
        # Non-string company
        result1 = self.pipeline.run({"company": 12345, "signal": "Valid signal"})
        self.assertEqual(result1.status, "FAILED")
        self.assertEqual(result1.reason, "invalid_schema")

        # Non-string or empty signal
        result2 = self.pipeline.run({"company": "Acme", "signal": None})
        self.assertEqual(result2.status, "FAILED")
        self.assertEqual(result2.reason, "invalid_schema")

        result3 = self.pipeline.run({"company": "Acme", "signal": "   "})
        self.assertEqual(result3.status, "FAILED")
        self.assertEqual(result3.reason, "invalid_schema")

        # Non-dict payload
        result4 = self.pipeline.run(["not", "a", "dict"])
        self.assertEqual(result4.status, "FAILED")
        self.assertEqual(result4.reason, "invalid_schema")

    def test_source_url_none_handled_safely(self):
        # source_url is explicitly None; must not crash in normalize and fail closed in verify
        raw_input = {
            "case_id": "CASE-104",
            "company": "Globex Corp",
            "signal": "Globex is hiring VP Security",
            "source_url": None,
        }
        result = self.pipeline.run(raw_input)
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.reason, "hollow_prevented")
        self.assertIsNone(result.final_payload)

    def test_decision_investigate_and_reject_supported(self):
        # Signal indicating unverified / rumor with verified source -> INVESTIGATE decision, DEGRADED status
        investigate_input = {
            "case_id": "CASE-105",
            "company": "Nexus Logistics",
            "signal": "Forum post mentions evaluating alternative vendors (unverified rumor).",
            "source_url": "https://forums.example/eval",
        }
        res_inv = self.pipeline.run(investigate_input)
        self.assertEqual(res_inv.status, "DEGRADED")
        self.assertIsNotNone(res_inv.final_payload)
        self.assertEqual(res_inv.final_payload["decision"], "INVESTIGATE")

        # Signal indicating irrelevant / cafeteria award -> REJECT decision, CLEAN status
        reject_input = {
            "case_id": "CASE-106",
            "company": "BrightSolar",
            "signal": "Won cafeteria green award, irrelevant to sales.",
            "source_url": "https://news.example/cafeteria",
        }
        res_rej = self.pipeline.run(reject_input)
        self.assertEqual(res_rej.status, "CLEAN")
        self.assertIsNotNone(res_rej.final_payload)
        self.assertEqual(res_rej.final_payload["decision"], "REJECT")


if __name__ == "__main__":
    unittest.main()
