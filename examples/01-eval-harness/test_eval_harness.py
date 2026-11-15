"""
Unit tests for Example 01: Eval Harness.
Verifies CLEAN, DEGRADED, HOLLOW, and FAILED classifications and golden set batch evaluation.
"""

import os
import unittest
from eval_runner import (
    Classification,
    evaluate_run,
    evaluate_batch,
    load_golden_cases,
)


class TestEvalHarness(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(__file__)
        self.golden_path = os.path.join(self.base_dir, "golden_cases.json")
        self.golden_cases = load_golden_cases(self.golden_path)

    def test_golden_cases_loaded(self):
        self.assertEqual(len(self.golden_cases), 5)
        case_ids = [c["id"] for c in self.golden_cases]
        self.assertIn("CASE-001", case_ids)

    def test_clean_classification(self):
        case = self.golden_cases[0]  # CASE-001
        payload = {
            "case_id": "CASE-001",
            "decision": "QUALIFY",
            "summary": "Acme Cloud is actively hiring DevOps engineers for Kubernetes migration.",
            "citations": ["https://careers.acmecloud.example/jobs"],
            "confidence": 0.95,
        }
        res = evaluate_run(payload, case)
        self.assertEqual(res.status, Classification.CLEAN)
        self.assertEqual(res.score, 1.0)
        self.assertTrue(res.checks["schema_valid"])
        self.assertTrue(res.checks["citations_valid"])
        self.assertTrue(res.checks["decision_matched"])

    def test_degraded_classification(self):
        # Degraded due to confidence below threshold or decision mismatch
        case = self.golden_cases[2]  # CASE-003: INVESTIGATE with min_confidence 0.50
        payload = {
            "case_id": "CASE-003",
            "decision": "INVESTIGATE",
            "summary": "Nexus Logistics contract renewal rumored on forums.",
            "citations": ["https://forum.logistics-tech.example/t/nexus-wms/992"],
            "confidence": 0.40,  # Below min_confidence (0.50) -> DEGRADED
        }
        res = evaluate_run(payload, case)
        self.assertEqual(res.status, Classification.DEGRADED)
        self.assertGreater(res.score, 0.0)

    def test_investigate_matching_golden_case(self):
        # When INVESTIGATE is the expected decision and confidence >= threshold, output is CLEAN
        case = self.golden_cases[2]  # CASE-003: expected INVESTIGATE, min_confidence 0.50
        payload = {
            "case_id": "CASE-003",
            "decision": "INVESTIGATE",
            "summary": "Nexus Logistics contract renewal rumored on forums.",
            "citations": ["https://forum.logistics-tech.example/t/nexus-wms/992"],
            "confidence": 0.55,
        }
        res = evaluate_run(payload, case)
        self.assertEqual(res.status, Classification.CLEAN)
        self.assertEqual(res.score, 1.0)

    def test_non_string_citations_rejected(self):
        # Citations must be strings starting with http:// or https://
        case = self.golden_cases[0]
        payload = {
            "case_id": "CASE-001",
            "decision": "QUALIFY",
            "summary": "Acme Cloud confirmed hiring DevOps engineers.",
            "citations": [123, None],  # Non-string citations
            "confidence": 0.95,
        }
        res = evaluate_run(payload, case)
        self.assertEqual(res.status, Classification.HOLLOW)

    def test_no_golden_case_requires_valid_url_citations(self):
        # When no golden case is supplied, expected_grounded defaults to True
        payload_no_citations = {
            "case_id": "AD-HOC-001",
            "decision": "QUALIFY",
            "summary": "Grounded claim without citations.",
            "citations": [],
            "confidence": 0.90,
        }
        res = evaluate_run(payload_no_citations, golden_case=None)
        self.assertEqual(res.status, Classification.HOLLOW)

        payload_valid = {
            "case_id": "AD-HOC-002",
            "decision": "QUALIFY",
            "summary": "Valid ad-hoc claim with URL citations.",
            "citations": ["https://example.com/verified-source"],
            "confidence": 0.85,
        }
        res_valid = evaluate_run(payload_valid, golden_case=None)
        self.assertEqual(res_valid.status, Classification.CLEAN)

    def test_hollow_classification(self):
        # Returned valid JSON with HTTP 200, but empty summary or missing required citation
        case = self.golden_cases[0]  # Expects grounded citation
        payload = {
            "case_id": "CASE-001",
            "decision": "QUALIFY",
            "summary": "Acme Cloud is hiring.",
            "citations": [],  # Missing citation on grounded claim
            "confidence": 0.90,
        }
        res = evaluate_run(payload, case)
        self.assertEqual(res.status, Classification.HOLLOW)

    def test_hollow_placeholder_summary(self):
        case = self.golden_cases[0]
        payload = {
            "case_id": "CASE-001",
            "decision": "QUALIFY",
            "summary": "N/A",  # Trivial placeholder
            "citations": ["https://careers.acmecloud.example/jobs"],
            "confidence": 0.90,
        }
        res = evaluate_run(payload, case)
        self.assertEqual(res.status, Classification.HOLLOW)

    def test_failed_classification(self):
        # Crash / malformed / missing schema fields
        malformed_payload = {"wrong_field": 123}
        res = evaluate_run(malformed_payload, self.golden_cases[0])
        self.assertEqual(res.status, Classification.FAILED)

        # None payload (crash)
        res_none = evaluate_run(None, self.golden_cases[0])
        self.assertEqual(res_none.status, Classification.FAILED)

    def test_batch_evaluation(self):
        # Construct simulated batch runs
        mock_outputs = {
            "CASE-001": {
                "case_id": "CASE-001",
                "decision": "QUALIFY",
                "summary": "Acme Cloud confirmed hiring DevOps.",
                "citations": ["https://careers.acmecloud.example/jobs"],
                "confidence": 0.95,
            },
            "CASE-002": {
                "case_id": "CASE-002",
                "decision": "QUALIFY",
                "summary": "DataVibe appointed new VP InfoSec.",
                "citations": ["https://datavibe.example/press/new-ciso-sarah-jenkins"],
                "confidence": 0.92,
            },
            "CASE-003": {
                "case_id": "CASE-003",
                "decision": "INVESTIGATE",
                "summary": "Nexus logistics forum unverified report.",
                "citations": ["https://forum.logistics-tech.example/t/nexus-wms/992"],
                "confidence": 0.40,  # Below min_confidence (0.50) -> DEGRADED
            },
            "CASE-004": {
                "case_id": "CASE-004",
                "decision": "DISQUALIFY",
                "summary": "BrightSolar cafeteria award has no sales intent.",
                "citations": ["https://brightsolar.example/news/green-building-award"],
                "confidence": 0.92,
            },
            "CASE-005": {
                "case_id": "CASE-005",
                "decision": "REJECT",
                "summary": "Fintech Horizon claim unverified, dropped.",
                "citations": [],
                "confidence": 0.25,
            },
        }

        report = evaluate_batch(self.golden_cases, mock_outputs)
        self.assertEqual(report["total"], 5)
        self.assertEqual(report["counts"][Classification.CLEAN], 4)
        self.assertEqual(report["counts"][Classification.DEGRADED], 1)
        self.assertEqual(report["counts"][Classification.HOLLOW], 0)
        self.assertEqual(report["counts"][Classification.FAILED], 0)
        self.assertAlmostEqual(report["clean_rate"], 0.8)


if __name__ == "__main__":
    unittest.main()
