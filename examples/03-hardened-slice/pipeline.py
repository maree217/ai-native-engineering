"""
AI-Native Engineering Framework - Example 03: Hardened Vertical Slice
Loop 2 Fixed 6-Stage Pipeline: ingest -> normalize -> retrieve -> judge -> verify -> emit.
Demonstrates fail-closed policy, deterministic citation gating, and telemetry classification.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class StageOutput:
    stage: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class PipelineResult:
    run_id: str
    status: str  # "CLEAN", "DEGRADED", "HOLLOW", "FAILED"
    final_payload: Optional[Dict[str, Any]] = None
    stage_traces: List[StageOutput] = field(default_factory=list)
    human_signoff_required: bool = True
    error_message: Optional[str] = None
    reason: Optional[str] = None


class HardenedPipeline:
    """
    Fixed 6-stage production pipeline implementing fail-closed architectural rails.
    Stages:
      1. ingest: validate incoming raw payload schema and string types
      2. normalize: whitespace and type normalization (case title-formatting, url sanitization)
      3. retrieve: fetch authoritative context from evidence store
      4. judge: evaluate relevance and categorize claim (QUALIFY, INVESTIGATE, REJECT)
      5. verify: deterministic fail-closed gate (URL-in-store verification)
      6. emit: format final delivery envelope with human-in-the-loop review flag
    """

    def __init__(self, evidence_store: Optional[Dict[str, str]] = None):
        # Simulated store: url -> authoritative body text
        self.evidence_store = evidence_store or {}

    def run(self, raw_input: Dict[str, Any]) -> PipelineResult:
        run_id = f"pipe-{uuid.uuid4().hex[:12]}"
        stages: List[StageOutput] = []

        # -------------------------------------------------------------
        # Stage 1: Ingest
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        if not isinstance(raw_input, dict):
            dur = (time.perf_counter() - t0) * 1000.0
            stages.append(StageOutput("ingest", False, {}, "Payload must be a dictionary", dur))
            return PipelineResult(
                run_id=run_id,
                status="FAILED",
                stage_traces=stages,
                error_message="Ingest validation failed: payload must be a dictionary",
                reason="invalid_schema",
            )

        company_val = raw_input.get("company")
        signal_val = raw_input.get("signal")
        if not (isinstance(company_val, str) and bool(company_val.strip())) or not (isinstance(signal_val, str) and bool(signal_val.strip())):
            dur = (time.perf_counter() - t0) * 1000.0
            stages.append(StageOutput("ingest", False, {}, "Missing or non-string company or signal in raw input", dur))
            return PipelineResult(
                run_id=run_id,
                status="FAILED",
                stage_traces=stages,
                error_message="Ingest validation failed: company and signal must be non-empty strings",
                reason="invalid_schema",
            )
        stages.append(StageOutput(
            "ingest",
            True,
            {"company": company_val, "signal": signal_val},
            duration_ms=(time.perf_counter() - t0) * 1000.0,
        ))

        # -------------------------------------------------------------
        # Stage 2: Normalize (whitespace/type normalization)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        normalized_company = company_val.strip().title()
        normalized_signal = " ".join(signal_val.strip().split())
        raw_source_url = raw_input.get("source_url") or ""
        source_url = raw_source_url.strip() if isinstance(raw_source_url, str) else ""
        stages.append(StageOutput("normalize", True, {
            "company": normalized_company,
            "signal": normalized_signal,
            "source_url": source_url,
        }, duration_ms=(time.perf_counter() - t0) * 1000.0))

        # -------------------------------------------------------------
        # Stage 3: Retrieve
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        retrieved_text = self.evidence_store.get(source_url) if source_url else None
        has_evidence = retrieved_text is not None and len(retrieved_text) > 0
        stages.append(StageOutput("retrieve", True, {
            "source_url": source_url,
            "has_evidence": has_evidence,
            "retrieved_snippet": retrieved_text[:120] if retrieved_text else None,
        }, duration_ms=(time.perf_counter() - t0) * 1000.0))

        # -------------------------------------------------------------
        # Stage 4: Judge (determine QUALIFY / INVESTIGATE / REJECT based on signal & evidence)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        explicit_decision = raw_input.get("decision")
        if explicit_decision in {"QUALIFY", "INVESTIGATE", "DISQUALIFY", "REJECT"}:
            decision = explicit_decision
            confidence = float(raw_input.get("confidence", 0.90 if decision != "INVESTIGATE" else 0.60))
            claim_status = "confirmed" if has_evidence else "unverified"
        else:
            combined_text = (normalized_signal + " " + (retrieved_text or "")).lower()
            if any(w in combined_text for w in ["rumor", "unverified", "investigate", "evaluating", "tentative"]):
                decision = "INVESTIGATE"
                confidence = 0.65
                claim_status = "inconclusive"
            elif any(w in combined_text for w in ["false", "disqualif", "reject", "cafeteria", "irrelevant", "unrelated"]):
                decision = "REJECT"
                confidence = 0.90
                claim_status = "refuted"
            else:
                decision = "QUALIFY"
                confidence = 0.95
                claim_status = "confirmed"

        stages.append(StageOutput("judge", True, {
            "decision": decision,
            "claim_status": claim_status,
            "confidence": confidence,
        }, duration_ms=(time.perf_counter() - t0) * 1000.0))

        # -------------------------------------------------------------
        # Stage 5: Verify (Deterministic Fail-Closed Gate: URL-in-store verification)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        # Fail-closed rule: citation must exist and be verified in authoritative evidence store;
        # otherwise refuse to emit outward-facing payload to prevent silent HOLLOW failure.
        if not has_evidence or not source_url:
            dur = (time.perf_counter() - t0) * 1000.0
            stages.append(StageOutput("verify", False, {
                "gate": "fail-closed",
                "reason": "Missing or unconfirmed evidence citation in store",
            }, "Citation verification failed", dur))

            return PipelineResult(
                run_id=run_id,
                status="FAILED",
                final_payload=None,
                stage_traces=stages,
                human_signoff_required=True,
                error_message="Fail-closed gate triggered: claim not grounded in verified evidence",
                reason="hollow_prevented",
            )

        stages.append(StageOutput("verify", True, {
            "gate": "passed",
            "citation": source_url,
        }, duration_ms=(time.perf_counter() - t0) * 1000.0))

        # -------------------------------------------------------------
        # Stage 6: Emit
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        final_payload = {
            "case_id": raw_input.get("case_id", run_id),
            "company": normalized_company,
            "summary": f"{normalized_company}: {normalized_signal}",
            "decision": decision,
            "confidence": confidence,
            "citations": [source_url],
            "human_approval_status": "PENDING_REVIEW",  # Criterion 6: Human sign-off required
        }
        stages.append(StageOutput("emit", True, final_payload, duration_ms=(time.perf_counter() - t0) * 1000.0))

        pipeline_status = "DEGRADED" if decision == "INVESTIGATE" else "CLEAN"
        return PipelineResult(
            run_id=run_id,
            status=pipeline_status,
            final_payload=final_payload,
            stage_traces=stages,
            human_signoff_required=True,
        )
