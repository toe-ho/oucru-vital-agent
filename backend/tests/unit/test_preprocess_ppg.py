"""Unit tests for preprocess_ppg and extract_ppg_dc_layer."""
import numpy as np
import pytest
from app.tools.ppg_tools import preprocess_ppg, extract_ppg_dc_layer


@pytest.fixture
def clean_ppg(ppg_signal):
    return ppg_signal


@pytest.fixture
def noisy_ppg():
    t = np.linspace(0, 30, 3000)
    hr_hz = 70 / 60
    return (0.6 * np.sin(2 * np.pi * hr_hz * t) + 0.5 * np.random.randn(3000)).tolist()


@pytest.fixture
def baseline_wander_ppg():
    t = np.linspace(0, 30, 3000)
    hr_hz = 70 / 60
    baseline = 0.5 * np.sin(2 * np.pi * 0.1 * t)
    return (0.6 * np.sin(2 * np.pi * hr_hz * t) + baseline).tolist()


# ---------- preprocess_ppg ----------

def test_preprocess_returns_filtered_signal(clean_ppg):
    result = preprocess_ppg(clean_ppg, fs=100)
    assert "filtered_signal" in result
    assert len(result["filtered_signal"]) == len(clean_ppg)


def test_preprocess_detects_peaks(clean_ppg):
    result = preprocess_ppg(clean_ppg, fs=100)
    assert result["n_peaks"] > 0
    assert len(result["peaks_indices"]) == result["n_peaks"]


def test_preprocess_returns_rr_intervals(clean_ppg):
    result = preprocess_ppg(clean_ppg, fs=100)
    assert "rr_intervals_ms" in result
    assert len(result["rr_intervals_ms"]) == result["n_peaks"] - 1


def test_preprocess_heart_rate_physiological(clean_ppg):
    result = preprocess_ppg(clean_ppg, fs=100)
    if result["heart_rate_bpm"] is not None:
        assert 20 <= result["heart_rate_bpm"] <= 300


def test_preprocess_noisy_signal_does_not_crash(noisy_ppg):
    result = preprocess_ppg(noisy_ppg, fs=100)
    assert "filtered_signal" in result


def test_preprocess_baseline_wander_signal(baseline_wander_ppg):
    result = preprocess_ppg(baseline_wander_ppg, fs=100)
    assert "filtered_signal" in result
    assert result["n_peaks"] >= 0


# ---------- extract_ppg_dc_layer ----------

def test_dc_layer_returns_trend(clean_ppg):
    result = extract_ppg_dc_layer(clean_ppg, fs=100)
    assert "dc_trend" in result
    assert len(result["dc_trend"]) > 0


def test_dc_layer_is_downsampled(clean_ppg):
    result = extract_ppg_dc_layer(clean_ppg, fs=100)
    assert len(result["dc_trend"]) < len(clean_ppg)


def test_dc_layer_returns_mean_and_variance(clean_ppg):
    result = extract_ppg_dc_layer(clean_ppg, fs=100)
    assert "mean_dc" in result
    assert "dc_variance" in result
    assert isinstance(result["mean_dc"], float)
    assert result["dc_variance"] >= 0.0
