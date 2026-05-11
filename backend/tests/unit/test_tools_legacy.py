"""
tests/unit/test_tools_legacy.py

Standalone tool tests — no LLM required.
Ported from the original tests/test_tools.py; imports updated to app.tools.*.

Run:
  pytest tests/unit/test_tools_legacy.py -v
"""

import numpy as np
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------------------------
# Synthetic test signal helpers
# ---------------------------------------------------------------------------

def synthetic_ppg(duration_sec: int = 30, fs: int = 100, hr_bpm: float = 70) -> list:
    t = np.linspace(0, duration_sec, duration_sec * fs)
    hr_hz = hr_bpm / 60
    signal = (
        0.6 * np.sin(2 * np.pi * hr_hz * t)
        + 0.2 * np.sin(2 * np.pi * 2 * hr_hz * t)
        + 0.05 * np.random.randn(len(t))
    )
    return signal.tolist()


def save_test_csv(tmp_path: Path, filename: str = "test_ppg.csv") -> str:
    path = tmp_path / filename
    sig = synthetic_ppg()
    pd.DataFrame({"ppg": sig}).to_csv(path, index=False)
    return str(path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_load_signal_file(tmp_path):
    from app.tools.signal_loader import load_signal_file

    csv_path = save_test_csv(tmp_path)
    result = load_signal_file(csv_path, column="ppg", fs=100)

    assert "signal" in result
    assert result["fs"] == 100
    assert result["n_samples"] == 3000
    assert result["duration_sec"] == 30.0


def test_preprocess_ppg():
    from app.tools.ppg_tools import preprocess_ppg

    signal = synthetic_ppg(duration_sec=30, fs=100, hr_bpm=70)
    result = preprocess_ppg(signal, fs=100)

    assert "filtered_signal" in result
    assert "peaks_indices" in result
    assert result["n_peaks"] > 0
    assert result["heart_rate_bpm"] is not None


def test_extract_hrv_features():
    from app.tools.ppg_tools import preprocess_ppg
    from app.tools.hrv_tools import extract_hrv_features

    signal = synthetic_ppg(duration_sec=60, fs=100, hr_bpm=70)
    pp = preprocess_ppg(signal, fs=100)
    result = extract_hrv_features(pp["rr_intervals_ms"], fs=100)

    assert "sdnn_ms" in result
    assert result["n_intervals"] > 10


def test_check_clinical_thresholds_normal():
    from app.tools.threshold_tools import check_clinical_thresholds

    result = check_clinical_thresholds(heart_rate_bpm=72.0, spo2_pct=98.0, sqi_score=0.8)
    assert result["flags"] == []
    assert not result["any_critical"]
    assert not result["any_warning"]


def test_check_clinical_thresholds_flagged():
    from app.tools.threshold_tools import check_clinical_thresholds

    result = check_clinical_thresholds(heart_rate_bpm=35.0, spo2_pct=85.0, sqi_score=0.9)
    assert len(result["flags"]) >= 2
    assert result["any_critical"]


def test_extract_ppg_dc_layer():
    from app.tools.ppg_tools import extract_ppg_dc_layer

    signal = synthetic_ppg(duration_sec=30, fs=100)
    result = extract_ppg_dc_layer(signal, fs=100)

    assert "dc_trend" in result
    assert len(result["dc_trend"]) < len(signal)  # downsampled
