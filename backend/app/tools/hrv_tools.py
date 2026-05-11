"""Tool 5: extract_hrv_features — vitalDSP HRV wrapper."""
from __future__ import annotations

import numpy as np

try:
    from smolagents import tool
except ImportError:
    def tool(fn):
        return fn


@tool
def extract_hrv_features(rr_intervals_ms: list, fs: int = 100) -> dict:
    """
    Extract time-domain and frequency-domain HRV features from RR intervals.

    Args:
        rr_intervals_ms: List of RR intervals in milliseconds.
        fs: Original signal sampling frequency.

    Returns:
        dict with time-domain (mean_rr_ms, sdnn_ms, rmssd_ms, pnn50_pct,
        mean_hr_bpm) and frequency-domain (lf_power, hf_power, lf_hf_ratio,
        vlf_power) metrics, n_intervals, analysis_duration_sec.
    """
    from vitaldsp.hrv_analysis import HRVAnalysis

    rr = np.array(rr_intervals_ms)
    hrv = HRVAnalysis(rr)
    time_domain = hrv.compute_time_domain()

    try:
        freq_domain = hrv.compute_frequency_domain()
    except Exception:
        freq_domain = {"lf_power": None, "hf_power": None, "lf_hf_ratio": None, "vlf_power": None}

    return {
        "mean_rr_ms": round(float(time_domain.get("mean_rr", 0)), 2),
        "sdnn_ms": round(float(time_domain.get("sdnn", 0)), 2),
        "rmssd_ms": round(float(time_domain.get("rmssd", 0)), 2),
        "pnn50_pct": round(float(time_domain.get("pnn50", 0)), 2),
        "mean_hr_bpm": round(60000 / float(time_domain.get("mean_rr", 1)), 1),
        "lf_power": freq_domain.get("lf_power"),
        "hf_power": freq_domain.get("hf_power"),
        "lf_hf_ratio": freq_domain.get("lf_hf_ratio"),
        "vlf_power": freq_domain.get("vlf_power"),
        "n_intervals": len(rr),
        "analysis_duration_sec": round(float(np.sum(rr)) / 1000, 1),
    }
