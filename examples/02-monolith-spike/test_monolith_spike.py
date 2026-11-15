"""
Unit tests for Example 02: Monolith Spike.
Verifies tool execution, step-budget enforcement, and telemetry trace emission.
"""

import unittest
from spike_agent import SpikeAgent, ToolRegistry


class TestMonolithSpike(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        # Register mock tools for Loop 1 discovery
        self.registry.register(
            "search_web",
            lambda query: {"query": query, "snippet": "Target company raised Series B.", "url": "https://news.example/acme"},
            description="Searches web for company signals",
        )
        self.registry.register(
            "verify_filing",
            lambda company: {"company": company, "verified": True, "source": "official_register"},
            description="Verifies corporate registry records",
        )
        self.agent = SpikeAgent(registry=self.registry, max_steps=3)

    def test_tool_registry_and_execution(self):
        self.assertIn("search_web", self.registry.list_tools())
        result = self.registry.execute("search_web", query="Acme")
        self.assertEqual(result["url"], "https://news.example/acme")

        # Unknown tool raises KeyError
        with self.assertRaises(KeyError):
            self.registry.execute("non_existent_tool")

    def test_happy_path_trace_emission(self):
        actions = [
            {"tool": "search_web", "args": {"query": "Acme Series B"}},
            {"tool": "verify_filing", "args": {"company": "Acme"}},
        ]
        trace = self.agent.run("Verify Acme funding", plan_actions=actions)

        self.assertEqual(trace.outcome, "COMPLETED")
        self.assertEqual(trace.steps_taken, 2)
        self.assertEqual(len(trace.steps), 2)
        self.assertGreaterEqual(trace.total_latency_ms, 0.0)
        self.assertTrue(all(s.latency_ms >= 0.0 for s in trace.steps))
        self.assertGreater(trace.estimated_tokens, 0)
        self.assertGreater(trace.estimated_cost_usd, 0.0)
        self.assertTrue(trace.run_id.startswith("trace-"))
        self.assertIsNotNone(trace.final_output)
        expected_fields = {
            "case_id", "decision", "confidence", "citations",
            "summary", "status", "step_count", "telemetry"
        }
        self.assertTrue(expected_fields.issubset(set(trace.final_output.keys())))
        self.assertEqual(trace.final_output["status"], "SUCCESS")
        self.assertEqual(trace.final_output["step_count"], 2)
        self.assertGreaterEqual(trace.final_output["telemetry"]["total_latency_ms"], 0.0)
        self.assertIn("https://news.example/acme", trace.final_output["citations"])

    def test_zero_steps_produces_hollow_status(self):
        trace = self.agent.run("Empty action plan", plan_actions=[])
        self.assertEqual(trace.steps_taken, 0)
        self.assertEqual(trace.outcome, "COMPLETED")
        self.assertIsNotNone(trace.final_output)
        self.assertEqual(trace.final_output["status"], "HOLLOW")
        self.assertEqual(trace.final_output["step_count"], 0)
        self.assertEqual(trace.final_output["confidence"], 0.0)
        expected_fields = {
            "case_id", "decision", "confidence", "citations",
            "summary", "status", "step_count", "telemetry"
        }
        self.assertTrue(expected_fields.issubset(set(trace.final_output.keys())))

    def test_step_budget_enforcement(self):
        # Provide 5 actions when max_steps is 3
        actions = [
            {"tool": "search_web", "args": {"query": f"Query {i}"}}
            for i in range(5)
        ]
        trace = self.agent.run("Excessive search goal", plan_actions=actions)

        self.assertEqual(trace.outcome, "BUDGET_EXCEEDED")
        self.assertEqual(trace.steps_taken, 3)
        self.assertEqual(len(trace.steps), 3)

    def test_tool_error_handling(self):
        def failing_tool():
            raise ValueError("Network timeout connecting to external API")

        self.registry.register("failing_tool", failing_tool)
        actions = [{"tool": "failing_tool", "args": {}}]
        trace = self.agent.run("Failing test", plan_actions=actions)

        self.assertEqual(trace.outcome, "ERROR")
        self.assertIn("Network timeout", trace.final_output["error"])


if __name__ == "__main__":
    unittest.main()
