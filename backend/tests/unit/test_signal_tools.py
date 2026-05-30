"""Unit tests for signal tool wrappers (no DB, no HTTP)."""

import pathlib
import uuid
from unittest.mock import patch

import numpy as np
import pytest

from app.tools.clinical_threshold_tools import evaluate_thresholds
from app.tools.load_signal_file_tool import load_signal_file
from app.tools.sqi_tools import (
    check_clinical_thresholds,
    compute_sqi,
    compute_sqi_windowed,
)

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"
_ECG_CSV = _FIXTURES / "sample_ecg.csv"


def _make_ref(path: pathlib.Path | None = None) -> dict:
    """Build a signal_ref dict pointing at the ECG fixture."""
    p = path or _ECG_CSV
    return {
        "recording_id": str(uuid.uuid4()),
        "storage_uri": str(p),
        "signal_column": "ecg",
        "sampling_rate": 250,
        "file_format": "csv",
    }


# ---------------------------------------------------------------------------
# load_signal_file
# ---------------------------------------------------------------------------

def test_load_signal_file_returns_metadata_not_array():
    """Result must contain stats keys and must NOT contain raw sample array."""
    ref = _make_ref()
    result = load_signal_file(
        recording_id=ref["recording_id"],
        storage_uri=ref["storage_uri"],
        signal_column=ref["signal_column"],
        sampling_rate=ref["sampling_rate"],
        file_format=ref["file_format"],
    )
    assert "samples" not in result, "raw sample array must not be in result"
    assert result["sample_count"] == 7500
    assert result["sampling_rate"] == 250
    assert abs(result["duration_seconds"] - 30.0) < 0.01
    assert "mean" in result and "std" in result
    assert "signal_ref" in result


# ---------------------------------------------------------------------------
# compute_sqi
# ---------------------------------------------------------------------------

def test_compute_sqi_snr_returns_dict():
    ref = _make_ref()
    result = compute_sqi(ref, metric="snr")
    assert result["status"] == "ok"
    assert result["metric_name"] == "snr"
    assert isinstance(result["value"], float)
    assert result["error"] is None


def test_compute_sqi_unknown_metric_returns_error():
    ref = _make_ref()
    result = compute_sqi(ref, metric="unknown_metric")
    assert result["status"] == "error"
    assert result["value"] is None


# ---------------------------------------------------------------------------
# compute_sqi_windowed
# ---------------------------------------------------------------------------

def test_compute_sqi_windowed_returns_list():
    ref = _make_ref()
    result = compute_sqi_windowed(ref, window_s=10, metric="snr")
    assert result["status"] == "ok"
    assert isinstance(result["windows"], list)
    assert len(result["windows"]) > 0
    first = result["windows"][0]
    assert "window_index" in first and "value" in first


# ---------------------------------------------------------------------------
# check_clinical_thresholds (sqi_tools wrapper)
# ---------------------------------------------------------------------------

def test_check_clinical_thresholds_pass():
    metrics = {"hr": 72.0, "spo2": 98.0}
    thresholds = {"hr": {"min": 50.0, "max": 100.0}, "spo2": {"min": 95.0, "max": None}}
    result = check_clinical_thresholds(metrics, thresholds)
    assert result["passed"] is True
    assert result["violations"] == []


def test_check_clinical_thresholds_fail():
    metrics = {"hr": 30.0, "spo2": 98.0}
    thresholds = {"hr": {"min": 50.0, "max": 100.0}}
    result = check_clinical_thresholds(metrics, thresholds)
    assert result["passed"] is False
    assert len(result["violations"]) == 1
    assert result["violations"][0]["metric"] == "hr"
    assert result["violations"][0]["bound"] == "min"


# ---------------------------------------------------------------------------
# evaluate_thresholds (clinical_threshold_tools)
# ---------------------------------------------------------------------------

def test_evaluate_thresholds_all_pass():
    values = {"sdnn": 45.0, "rmssd": 30.0}
    config = {"sdnn": {"min": 20.0, "max": 100.0}, "rmssd": {"min": 10.0, "max": 80.0}}
    result = evaluate_thresholds(values, config)
    assert result["overall_pass"] is True
    assert result["results"]["sdnn"]["passed"] is True


def test_evaluate_thresholds_missing_value_fails():
    values = {}
    config = {"sdnn": {"min": 20.0, "max": 100.0}}
    result = evaluate_thresholds(values, config)
    assert result["overall_pass"] is False
    assert result["results"]["sdnn"]["passed"] is False
