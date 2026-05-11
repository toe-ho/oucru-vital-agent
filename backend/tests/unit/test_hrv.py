"""Unit tests for extract_hrv_features."""
import numpy as np
import pytest
from app.tools.hrv_tools import extract_hrv_features


@pytest.fixture
def normal_rr():
    """~70 bpm: ~857ms mean RR with small variation."""
    rng = np.random.default_rng(42)
    return (857 + rng.normal(0, 20, 60)).tolist()


@pytest.fixture
def irregular_rr():
    """Highly irregular RR intervals."""
    rng = np.random.default_rng(0)
    return (800 + rng.normal(0, 150, 30)).tolist()


def test_hrv_returns_time_domain_fields(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    for field in ("mean_rr_ms", "sdnn_ms", "rmssd_ms", "pnn50_pct", "mean_hr_bpm"):
        assert field in result, f"Missing field: {field}"


def test_hrv_mean_rr_in_physiological_range(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    assert 300 <= result["mean_rr_ms"] <= 2000


def test_hrv_mean_hr_matches_mean_rr(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    expected_hr = 60000 / result["mean_rr_ms"]
    assert abs(result["mean_hr_bpm"] - expected_hr) < 1.0


def test_hrv_sdnn_positive(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    assert result["sdnn_ms"] >= 0


def test_hrv_rmssd_positive(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    assert result["rmssd_ms"] >= 0


def test_hrv_n_intervals_correct(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    assert result["n_intervals"] == len(normal_rr)


def test_hrv_analysis_duration(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    expected_sec = sum(normal_rr) / 1000
    assert abs(result["analysis_duration_sec"] - expected_sec) < 1.0


def test_hrv_freq_domain_fields_present(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    for field in ("lf_power", "hf_power", "lf_hf_ratio", "vlf_power"):
        assert field in result


def test_hrv_irregular_rr_does_not_crash(irregular_rr):
    result = extract_hrv_features(irregular_rr, fs=100)
    assert "mean_rr_ms" in result


def test_hrv_pnn50_between_0_and_100(normal_rr):
    result = extract_hrv_features(normal_rr, fs=100)
    assert 0.0 <= result["pnn50_pct"] <= 100.0
