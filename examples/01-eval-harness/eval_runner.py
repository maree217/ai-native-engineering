"""
AI-Native Engineering Framework - Example 01: Eval Harness
Tier 1 Deterministic Rails + Tier 2 Proxy Judgment & Run Classification.
"""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional


class Classification:
    CLEAN = "CLEAN"
    DEGRADED = "DEGRADED"
    HOLLOW = "HOLLOW"
    FAILED = "FAILED"


REQUIRED_FIELDS = {"case_id", "decision", "summary", "citations", "confidence"}
VALID_DECISIONS = {"QUALIFY", "INVESTIGATE", "DISQUALIFY", "REJECT"}


@dataclass
class EvalResult:
    status: str
    score: float
    checks: Dict[str, bool] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def validate_tier1_schema(payload: Dict[str, Any]) -> List[str]:
    """Tier 1: Deterministic schema and field validation."""
    issues = []
    if not isinstance(payload, dict):
        return ["Payload must be a dictionary"]

    missing = REQUIRED_FIELDS - set(payload.keys())
    if missing:
        issues.append(f"Missing required fields: {sorted(list(missing))}")

    if "decision" in payload and payload["decision"] not in VALID_DECISIONS:
        issues.append(f"Invalid decision: {payload['decision']}")

    if "confidence" in payload:
        conf = payload["confidence"]
        if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
            issues.append(f"Confidence must be float in [0.0, 1.0], got: {conf}")

    return issues


def validate_tier1_citations(
    payload: Dict[str, Any],
    evidence_url: Optional[str] = None,
    expected_grounded: bool = True,
) -> List[str]:
    """Tier 1: Deterministic citation format and presence check."""
    issues = []
    citations = payload.get("citations")
    if not isinstance(citations, list):
        return ["Citations must be a list of URLs or document references"]

    decision = payload.get("decision")
    if expected_grounded and decision != "REJECT":
        if not citations:
            issues.append("Missing citations for non-rejected claim")
        elif not all(isinstance(c, str) and c.startswith(("http://", "https://")) for c in citations):
            issues.append("All citations must be non-empty strings starting with http:// or https://")
        elif evidence_url and evidence_url not in citations:
            issues.append(f"Required evidence URL not found in citations: {evidence_url}")
    else:
        if not all(isinstance(c, str) and c.startswith(("http://", "https://")) for c in citations):
            issues.append("All citations must be non-empty strings starting with http:// or https://")

    return issues


def evaluate_run(payload: Any, golden_case: Optional[Dict[str, Any]] = None) -> EvalResult:
    """
    Evaluates a system run payload against Tier 1 & Tier 2 checks.
    Classifies the outcome as CLEAN, DEGRADED, HOLLOW, or FAILED.
    """
    checks = {
        "schema_valid": False,
        "citations_valid": False,
        "groundedness_valid": False,
        "decision_matched": False,
    }
    issues: List[str] = []

    # 1. Hard crash / invalid type -> FAILED
    if payload is None or not isinstance(payload, dict):
        return EvalResult(
            status=Classification.FAILED,
            score=0.0,
            checks=checks,
            issues=["Payload is None or non-dict; process crash or malformed return"],
        )

    # If payload explicitly signals runtime failure
    if payload.get("error"):
        return EvalResult(
            status=Classification.FAILED,
            score=0.0,
            checks=checks,
            issues=[f"Execution error reported: {payload['error']}"],
        )

    # 2. Schema validation
    schema_issues = validate_tier1_schema(payload)
    if schema_issues:
        return EvalResult(
            status=Classification.FAILED,
            score=0.0,
            checks=checks,
            issues=schema_issues,
        )
    checks["schema_valid"] = True

    # 3. Detect HOLLOW silent failure:
    # Process returned schema-valid response (HTTP 200 / code 0),
    # but summary is empty, dummy placeholder, or claims grounded without any citations
    summary = str(payload.get("summary", "")).strip()
    if len(summary) < 5 or summary.lower() in {"n/a", "none", "null", "no summary"}:
        return EvalResult(
            status=Classification.HOLLOW,
            score=0.0,
            checks=checks,
            issues=["Hollow output: summary is trivial or placeholder"],
        )

    expected_grounded = golden_case.get("expected_grounded", True) if golden_case else True
    evidence_url = golden_case.get("source_url") if golden_case else None
    citation_issues = validate_tier1_citations(payload, evidence_url, expected_grounded=expected_grounded)

    if expected_grounded and citation_issues:
        return EvalResult(
            status=Classification.HOLLOW,
            score=0.2,
            checks=checks,
            issues=citation_issues + ["Hollow output: claim made without verifiable citations"],
        )

    if citation_issues:
        issues.extend(citation_issues)
    else:
        checks["citations_valid"] = True

    # 4. Tier 2: Groundedness & Proxy Judgment
    expected_decision = golden_case.get("expected_decision") if golden_case else None
    actual_decision = payload.get("decision")
    confidence = payload.get("confidence", 0.0)

    if expected_decision:
        checks["decision_matched"] = (actual_decision == expected_decision)
        if not checks["decision_matched"]:
            issues.append(f"Decision mismatch: expected {expected_decision}, got {actual_decision}")
    else:
        checks["decision_matched"] = True

    checks["groundedness_valid"] = checks["citations_valid"] if expected_grounded else True

    # Degraded: decision mismatch or deliberate investigate/fallback state
    if not checks["decision_matched"]:
        return EvalResult(
            status=Classification.DEGRADED,
            score=0.5,
            checks=checks,
            issues=issues,
        )

    min_confidence = golden_case.get("min_confidence", 0.7) if golden_case else 0.7
    if confidence < min_confidence or (actual_decision == "INVESTIGATE" and expected_decision != "INVESTIGATE"):
        return EvalResult(
            status=Classification.DEGRADED,
            score=0.75,
            checks=checks,
            issues=issues if issues else ["Confidence below ideal threshold or partial signal"],
        )

    # 5. Clean pass
    return EvalResult(
        status=Classification.CLEAN,
        score=1.0,
        checks=checks,
        issues=[],
    )


def evaluate_batch(golden_cases: List[Dict[str, Any]], outputs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Runs batch evaluation over golden cases and calculates summary metrics."""
    results: Dict[str, EvalResult] = {}
    counts = {
        Classification.CLEAN: 0,
        Classification.DEGRADED: 0,
        Classification.HOLLOW: 0,
        Classification.FAILED: 0,
    }

    for case in golden_cases:
        cid = case["id"]
        output = outputs.get(cid)
        res = evaluate_run(output, case)
        results[cid] = res
        counts[res.status] += 1

    total = len(golden_cases)
    clean_rate = counts[Classification.CLEAN] / total if total > 0 else 0.0

    return {
        "total": total,
        "counts": counts,
        "clean_rate": clean_rate,
        "results": {cid: r.status for cid, r in results.items()},
    }


def load_golden_cases(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
