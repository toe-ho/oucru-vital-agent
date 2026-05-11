"""Rule-based fallback when LLM inference is unavailable."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.agent.state import AgentState
from app.tools.signal_loader import load_signal_file
from app.tools.sqi_tools import compute_sqi_windowed


FALLBACK_NOTE = (
    "This report was generated in automated fallback mode (LLM unavailable). "
    "No AI interpretation is included. Results are based on direct rule evaluation only."
)


def run_fallback_assessment(state: AgentState, task_plan: dict) -> AgentState:
    """
    Run a deterministic rule-based assessment without the LLM.

    Executes load → windowed_sqi → verdict using plan thresholds.
    Sets agent_interpretation to a fallback notice.
    """
    thresholds = task_plan.get("interpretation", {})
    escalate_threshold = thresholds.get("escalate_if_acceptance_rate_below", 0.40)
    verdict_map = thresholds.get("verdict_thresholds", {"acceptable": 0.80, "marginal": 0.60, "poor": 0.0})

    try:
        loaded = load_signal_file(
            state["file_path"],
            column=state["signal_type"],
            fs=state["sampling_rate"],
        )
        signal = loaded["signal"]

        windowed = compute_sqi_windowed(
            signal=signal,
            fs=state["sampling_rate"],
            signal_type=state["signal_type"],
            window_sec=30,
        )
        acceptance_rate = windowed["acceptance_rate"]
        windows = windowed["windows"]

        if acceptance_rate >= verdict_map.get("acceptable", 0.80):
            verdict = "acceptable"
        elif acceptance_rate >= verdict_map.get("marginal", 0.60):
            verdict = "marginal"
        else:
            verdict = "poor"

        flagged = [w["window_idx"] for w in windows if w["classification"] == "reject"]

        state = {
            **state,
            "current_stage": "escalated" if acceptance_rate < escalate_threshold else "finalizing",
            "acceptance_rate": acceptance_rate,
            "overall_verdict": verdict,
            "flagged_segment_ids": [str(i) for i in flagged],
            "sqi_matrix": {str(w["window_idx"]): w["metrics"] for w in windows},
            "agent_interpretation": FALLBACK_NOTE,
            "key_findings": [f"Acceptance rate: {acceptance_rate:.1%}"],
            "recommendations": ["Review flagged segments manually."],
            "escalate": acceptance_rate < escalate_threshold,
            "escalation_reason": "Low acceptance rate" if acceptance_rate < escalate_threshold else None,
        }
    except Exception as e:
        state = {
            **state,
            "current_stage": "error",
            "error_message": f"Fallback assessment failed: {e}",
            "escalate": True,
            "escalation_reason": f"Fallback error: {e}",
            "agent_interpretation": FALLBACK_NOTE,
        }

    return state  # type: ignore[return-value]
