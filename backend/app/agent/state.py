from __future__ import annotations

from typing import Any, Literal, TypedDict


class AgentState(TypedDict, total=False):
    # Input
    recording_id: str
    file_path: str
    signal_type: Literal["ecg", "ppg"]
    sampling_rate: int
    subject_id: str | None

    # Processing stage
    current_stage: Literal[
        "initialized", "preprocessing", "assessing",
        "interpreting", "fetching_details", "generating_report",
        "finalizing", "escalated", "completed", "error",
    ]
    needs_preprocessing: bool

    # Intermediate results (signal arrays stay in-process, never logged)
    preprocessed_file_path: str | None
    assessment_result: dict | None
    sqi_matrix: dict | None
    flagged_segment_ids: list[str]
    segment_details: dict[str, dict]

    # Agent reasoning
    agent_interpretation: str | None
    key_findings: list[str]
    recommendations: list[str]

    # Decisions
    overall_verdict: Literal["acceptable", "marginal", "poor"] | None
    acceptance_rate: float | None
    escalate: bool
    escalation_reason: str | None

    # Output
    report_id: str | None
    error_message: str | None
    tool_call_count: int


VALID_TRANSITIONS: dict[str, list[str]] = {
    "initialized": ["preprocessing", "assessing", "error"],
    "preprocessing": ["assessing", "error"],
    "assessing": ["interpreting", "escalated", "error"],
    "interpreting": ["fetching_details", "generating_report", "escalated", "error"],
    "fetching_details": ["generating_report", "error"],
    "generating_report": ["finalizing", "error"],
    "finalizing": ["completed"],
    "escalated": ["completed"],
    "error": [],
    "completed": [],
}


def transition(state: AgentState, to: str) -> AgentState:
    current = state.get("current_stage", "initialized")
    allowed = VALID_TRANSITIONS.get(current, [])
    if to not in allowed:
        raise ValueError(f"Invalid transition: {current} → {to}. Allowed: {allowed}")
    return {**state, "current_stage": to}  # type: ignore[return-value]


def serialize_state_for_log(state: AgentState) -> dict:
    """Return a DB-safe snapshot — strips any raw signal arrays."""
    safe = {}
    for key, value in state.items():
        if key in ("assessment_result", "sqi_matrix", "segment_details"):
            # Keep only scalar summaries, not nested arrays
            if isinstance(value, dict):
                safe[key] = {k: v for k, v in value.items() if not isinstance(v, list)}
            else:
                safe[key] = value
        else:
            safe[key] = value
    return safe
