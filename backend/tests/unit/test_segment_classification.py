"""Unit tests for segment_classification_service — no DB, no HTTP."""

import pytest

from app.services.segment_classification_service import classify_segment


_RULE_DICT = {
    "snr": {"required": True, "min": 8.0, "max": None},
    "kurtosis": {"required": False, "min": -1.5, "max": 10.0},
}


def _sqi(metric: str, value, passed):
    return {"metric_name": metric, "metric_value": value, "passed": passed}


# ---------------------------------------------------------------------------
# Classification tests
# ---------------------------------------------------------------------------

def test_all_required_pass_returns_accept():
    sqi_results = [
        _sqi("snr", 12.5, True),
        _sqi("kurtosis", 2.0, True),
    ]
    classification, score = classify_segment(sqi_results, _RULE_DICT)
    assert classification == "accept"
    assert score == 1.0


def test_required_fail_returns_reject():
    sqi_results = [
        _sqi("snr", 3.0, False),   # required, fails threshold
        _sqi("kurtosis", 2.0, True),
    ]
    classification, score = classify_segment(sqi_results, _RULE_DICT)
    assert classification == "reject"


def test_uncomputable_required_metric_returns_uncomputable():
    # snr value is None → uncomputable
    sqi_results = [
        _sqi("snr", None, None),
        _sqi("kurtosis", 2.0, True),
    ]
    classification, score = classify_segment(sqi_results, _RULE_DICT)
    assert classification == "uncomputable"


def test_quality_score_fraction():
    # 1 of 2 metrics passed → score = 0.5
    sqi_results = [
        _sqi("snr", 12.5, True),
        _sqi("kurtosis", 15.0, False),  # exceeds max=10
    ]
    classification, score = classify_segment(sqi_results, _RULE_DICT)
    # snr required and passes → accept; quality_score = 1/2
    assert classification == "accept"
    assert abs(score - 0.5) < 1e-6


def test_empty_sqi_returns_uncomputable():
    classification, score = classify_segment([], _RULE_DICT)
    assert classification == "uncomputable"
    assert score == 0.0


def test_optional_metric_fail_does_not_change_accept():
    """Non-required metric failure should not change classification to reject."""
    sqi_results = [
        _sqi("snr", 10.0, True),
        _sqi("kurtosis", 12.0, False),  # optional, fails
    ]
    classification, _ = classify_segment(sqi_results, _RULE_DICT)
    assert classification == "accept"
