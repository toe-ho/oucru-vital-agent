import pytest
from app.agent.state import AgentState, serialize_state_for_log, transition


def make_state(**kwargs) -> AgentState:
    base: AgentState = {
        "recording_id": "rec-1",
        "file_path": "/tmp/test.csv",
        "signal_type": "ppg",
        "sampling_rate": 100,
        "subject_id": None,
        "current_stage": "initialized",
        "needs_preprocessing": False,
        "preprocessed_file_path": None,
        "assessment_result": None,
        "sqi_matrix": None,
        "flagged_segment_ids": [],
        "segment_details": {},
        "agent_interpretation": None,
        "key_findings": [],
        "recommendations": [],
        "overall_verdict": None,
        "acceptance_rate": None,
        "escalate": False,
        "escalation_reason": None,
        "report_id": None,
        "error_message": None,
        "tool_call_count": 0,
    }
    return {**base, **kwargs}


def test_valid_transition():
    state = make_state(current_stage="initialized")
    new_state = transition(state, "assessing")
    assert new_state["current_stage"] == "assessing"


def test_invalid_transition():
    state = make_state(current_stage="completed")
    with pytest.raises(ValueError, match="Invalid transition"):
        transition(state, "assessing")


def test_serialize_strips_arrays():
    state = make_state(
        sqi_matrix={"0": {"kurtosis": 3.1, "signal_data": [1.0, 2.0, 3.0]}},
        assessment_result={"windows": [{"data": [0.1] * 100}, {"sqi_score": 0.8}]},
    )
    serialized = serialize_state_for_log(state)
    # Arrays inside dicts should be stripped
    if serialized.get("sqi_matrix"):
        for v in serialized["sqi_matrix"].values():
            if isinstance(v, dict):
                for inner_v in v.values():
                    assert not isinstance(inner_v, list), "Raw arrays should not be in log"
