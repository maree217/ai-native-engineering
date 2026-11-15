"""
AI-Native Engineering Framework - Example 02: Monolith Spike
Loop 1 Single-Container Open Agent Loop with Tool Registry, Step Budget, and Telemetry.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Dict, List, Optional
import uuid


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._schemas: Dict[str, str] = {}

    def register(self, name: str, func: Callable[..., Any], description: str = "") -> None:
        self._tools[name] = func
        self._schemas[name] = description

    def execute(self, name: str, **kwargs: Any) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")
        return self._tools[name](**kwargs)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())


@dataclass
class StepTrace:
    step: int
    tool: str
    args: Dict[str, Any]
    result: Any
    latency_ms: float


@dataclass
class AgentTrace:
    run_id: str
    goal: str
    steps_taken: int
    max_steps: int
    outcome: str  # "COMPLETED", "BUDGET_EXCEEDED", "ERROR"
    steps: List[StepTrace] = field(default_factory=list)
    total_latency_ms: float = 0.0
    estimated_tokens: int = 0
    estimated_cost_usd: float = 0.0
    final_output: Optional[Dict[str, Any]] = None


class SpikeAgent:
    """
    Loop 1 Monolithic Spike Agent:
    An exploratory open agent loop bounded by a strict step budget and instrumented with Day-1 telemetry.
    """

    def __init__(self, registry: ToolRegistry, max_steps: int = 5):
        self.registry = registry
        self.max_steps = max_steps

    def run(
        self,
        goal: str,
        plan_actions: Optional[List[Dict[str, Any]]] = None,
        case_id: Optional[str] = None,
    ) -> AgentTrace:
        start_time = time.perf_counter()
        run_id = f"trace-{uuid.uuid4().hex[:12]}"
        trace = AgentTrace(
            run_id=run_id,
            goal=goal,
            steps_taken=0,
            max_steps=self.max_steps,
            outcome="COMPLETED",
        )

        # In discovery mode, actions can be simulated, scripted, or model-driven
        actions = plan_actions or []
        step_count = 0
        tokens_accumulated = 150  # Base prompt tokens

        for action in actions:
            if step_count >= self.max_steps:
                trace.outcome = "BUDGET_EXCEEDED"
                break

            tool_name = action.get("tool")
            tool_args = action.get("args", {})
            step_start = time.perf_counter()

            try:
                res = self.registry.execute(tool_name, **tool_args)
                step_latency = (time.perf_counter() - step_start) * 1000.0
                tokens_accumulated += 200

                trace.steps.append(
                    StepTrace(
                        step=step_count + 1,
                        tool=tool_name,
                        args=tool_args,
                        result=res,
                        latency_ms=round(step_latency, 2),
                    )
                )
                step_count += 1
            except Exception as e:
                trace.outcome = "ERROR"
                step_latency = (time.perf_counter() - start_time) * 1000.0
                telemetry = {
                    "total_latency_ms": round(step_latency, 2),
                    "estimated_tokens": tokens_accumulated,
                    "estimated_cost_usd": round((tokens_accumulated / 1_000_000) * 3.0, 5),
                }
                trace.final_output = {
                    "case_id": case_id or run_id,
                    "decision": "REJECT",
                    "confidence": 0.0,
                    "citations": [],
                    "summary": f"Execution error: {str(e)}",
                    "status": "FAILED",
                    "step_count": step_count,
                    "telemetry": telemetry,
                    "error": str(e),
                }
                break

        total_latency = (time.perf_counter() - start_time) * 1000.0
        trace.steps_taken = step_count
        trace.total_latency_ms = round(total_latency, 2)
        trace.estimated_tokens = tokens_accumulated
        trace.estimated_cost_usd = round((tokens_accumulated / 1_000_000) * 3.0, 5)

        citations = [
            s.result.get("url") for s in trace.steps
            if isinstance(s.result, dict) and isinstance(s.result.get("url"), str) and s.result.get("url").startswith(("http://", "https://"))
        ]
        telemetry = {
            "total_latency_ms": trace.total_latency_ms,
            "estimated_tokens": trace.estimated_tokens,
            "estimated_cost_usd": trace.estimated_cost_usd,
        }

        if trace.outcome == "COMPLETED":
            status = "HOLLOW" if step_count == 0 else "SUCCESS"
            summary = (
                "No steps executed"
                if step_count == 0
                else f"Completed {step_count} step(s) towards goal: {goal}"
            )
            decision = "QUALIFY" if (step_count > 0 and citations) else "INVESTIGATE"
            confidence = 0.85 if (step_count > 0 and citations) else (0.50 if step_count > 0 else 0.0)

            trace.final_output = {
                "case_id": case_id or run_id,
                "decision": decision,
                "confidence": confidence,
                "citations": citations,
                "summary": summary,
                "status": status,
                "step_count": step_count,
                "telemetry": telemetry,
            }
        elif trace.outcome == "BUDGET_EXCEEDED":
            trace.final_output = {
                "case_id": case_id or run_id,
                "decision": "INVESTIGATE",
                "confidence": 0.40,
                "citations": citations,
                "summary": f"Step budget exceeded ({self.max_steps} steps) before goal completed: {goal}",
                "status": "DEGRADED",
                "step_count": step_count,
                "telemetry": telemetry,
            }

        return trace
