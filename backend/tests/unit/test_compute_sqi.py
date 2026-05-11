"""Unit tests for compute_sqi and compute_sqi_windowed."""
import numpy as np
import pytest
from app.tools.sqi_tools import compute_sqi, compute_sqi_windowed


@pytest.fixture
def clean_ppg(ppg_signal):
    return ppg_signal


@pytest.fixture
def clean_ecg(ecg_signal):
    return ecg_signal


@pytest.fixture
def flatline():
    return np.zeros(3000).tolist()


@pytest.fixture
def clipped():
    t = np.linspace(0, 30, 3000)
    sig = np.sin(2 * np.pi * 1.2 * t) * 5
    return np.clip(sig, -1, 1).tolist()


# ---------- compute_sqi ----------

def test_sqi_returns_score_between_0_and_1(clean_ppg):
    result = compute_sqi(clean_ppg, fs=100, signal_type="ppg")
    assert "sqi_score" in result
    assert 0.0 <= result["sqi_score"] <= 1.0


def test_sqi_returns_quality_label(clean_ppg):
    result = compute_sqi(clean_ppg, fs=100, signal_type="ppg")
    assert result["quality_label"] in ("good", "acceptable", "poor")


def test_sqi_flatline_is_poor(flatline):
    result = compute_sqi(flatline, fs=100, signal_type="ppg")
    assert result["sqi_score"] < 0.4
    assert result["quality_label"] == "poor"


def test_sqi_ecg_signal_type(clean_ecg):
    result = compute_sqi(clean_ecg, fs=500, signal_type="ecg")
    assert "sqi_score" in result
    assert "sub_scores" in result


def test_sqi_includes_recommendation(clean_ppg):
    result = compute_sqi(clean_ppg, fs=100, signal_type="ppg")
    assert isinstance(result["recommendation"], str)
    assert len(result["recommendation"]) > 0


def test_sqi_sub_scores_are_floats(clean_ppg):
    result = compute_sqi(clean_ppg, fs=100, signal_type="ppg")
    for k, v in result["sub_scores"].items():
        assert isinstance(v, float), f"Sub-score {k} is not a float"


# ---------- compute_sqi_windowed ----------

def test_windowed_sqi_returns_windows(clean_ppg):
    result = compute_sqi_windowed(clean_ppg, fs=100, window_sec=10)
    assert "windows" in result
    assert result["total_windows"] > 0


def test_windowed_sqi_window_fields(clean_ppg):
    result = compute_sqi_windowed(clean_ppg, fs=100, window_sec=10)
    for w in result["windows"]:
        assert "start_sec" in w
        assert "end_sec" in w
        assert "sqi_score" in w
        assert "classification" in w
        assert w["classification"] in ("accept", "reject")


def test_windowed_sqi_acceptance_rate_in_range(clean_ppg):
    result = compute_sqi_windowed(clean_ppg, fs=100, window_sec=10)
    assert 0.0 <= result["acceptance_rate"] <= 1.0


def test_windowed_sqi_short_signal_below_one_window():
    short = np.sin(np.linspace(0, 5, 500)).tolist()  # 5 seconds < 30s window
    result = compute_sqi_windowed(short, fs=100, window_sec=30)
    assert result["total_windows"] == 0
    assert result["acceptance_rate"] == 0.0


def test_windowed_sqi_mean_sqi_matches_windows(clean_ppg):
    result = compute_sqi_windowed(clean_ppg, fs=100, window_sec=10)
    if result["windows"]:
        manual_mean = sum(w["sqi_score"] for w in result["windows"]) / len(result["windows"])
        assert abs(result["mean_sqi"] - manual_mean) < 0.01
