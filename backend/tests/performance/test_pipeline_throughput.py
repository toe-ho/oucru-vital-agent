"""
Performance tests — measure pipeline throughput targets.

These tests are slow and only run on main branch merges (skipped in PR CI).
Run manually:
  pytest tests/performance/ -v -s
"""
import time
import numpy as np
import pytest


def synthetic_signal(duration_sec: int, fs: int = 100, hr_bpm: float = 70) -> list:
    t = np.linspace(0, duration_sec, duration_sec * fs)
    hr_hz = hr_bpm / 60
    return (0.6 * np.sin(2 * np.pi * hr_hz * t) + 0.05 * np.random.randn(len(t))).tolist()


@pytest.mark.slow
def test_compute_sqi_windowed_1h_under_60s():
    """1-hour signal processed by compute_sqi_windowed in < 60 seconds."""
    from app.tools.sqi_tools import compute_sqi_windowed

    signal = synthetic_signal(3600, fs=100)
    start = time.perf_counter()
    result = compute_sqi_windowed(signal, fs=100, window_sec=30, step_sec=30)
    elapsed = time.perf_counter() - start

    assert elapsed < 60, f"compute_sqi_windowed took {elapsed:.1f}s for 1h signal, expected <60s"
    assert result["total_windows"] == 120  # 3600/30


@pytest.mark.slow
def test_per_segment_sqi_under_5s():
    """Single 30-second segment SQI computed in < 5 seconds."""
    from app.tools.sqi_tools import compute_sqi

    signal = synthetic_signal(30, fs=100)
    start = time.perf_counter()
    result = compute_sqi(signal, fs=100, signal_type="ppg")
    elapsed = time.perf_counter() - start

    assert elapsed < 5.0, f"compute_sqi took {elapsed:.2f}s per segment, expected <5s"
    assert "sqi_score" in result


@pytest.mark.slow
def test_preprocess_ppg_30s_under_2s():
    """30-second PPG preprocessing in < 2 seconds."""
    from app.tools.ppg_tools import preprocess_ppg

    signal = synthetic_signal(30, fs=100)
    start = time.perf_counter()
    result = preprocess_ppg(signal, fs=100)
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0, f"preprocess_ppg took {elapsed:.2f}s, expected <2s"
    assert result["n_peaks"] > 0
