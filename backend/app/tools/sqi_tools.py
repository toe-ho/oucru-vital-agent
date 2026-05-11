"""Tools 2–3: compute_sqi and compute_sqi_windowed — vital-sqi wrappers."""
from __future__ import annotations

import numpy as np

try:
    from smolagents import tool
except ImportError:
    def tool(fn):
        return fn


@tool
def compute_sqi(signal: list, fs: int = 100, signal_type: str = "ppg") -> dict:
    """
    Compute overall Signal Quality Index (SQI) for a physiological signal.

    Args:
        signal: Signal as list of floats.
        fs: Sampling frequency in Hz.
        signal_type: "ppg" or "ecg".

    Returns:
        dict with: sqi_score (float 0–1), quality_label (str),
        sub_scores (dict), recommendation (str).
    """
    from vital_sqi.signal_quality.quality_assessment import SignalQualityAssessment

    sig = np.array(signal)
    sqa = SignalQualityAssessment(sig, fs, signal_type=signal_type)
    scores = sqa.compute_all()
    overall = float(scores.get("overall_sqi", 0.0))

    if overall >= 0.7:
        label, rec = "good", "Signal is suitable for clinical analysis."
    elif overall >= 0.5:
        label = "acceptable"
        rec = "Signal is usable but interpret results with caution."
    else:
        label = "poor"
        rec = "Signal quality is too low for reliable analysis. Check sensor placement."

    return {
        "sqi_score": round(overall, 3),
        "quality_label": label,
        "sub_scores": {k: round(float(v), 3) for k, v in scores.items() if k != "overall_sqi"},
        "recommendation": rec,
    }


@tool
def compute_sqi_windowed(
    signal: list,
    fs: int = 100,
    signal_type: str = "ppg",
    window_sec: int = 30,
    step_sec: int | None = None,
    rule_dict: dict | None = None,
) -> dict:
    """
    Compute SQI over fixed windows of a long signal, classifying each window.

    Args:
        signal: Signal as list of floats.
        fs: Sampling frequency in Hz.
        signal_type: "ppg" or "ecg".
        window_sec: Window length in seconds.
        step_sec: Step between windows (defaults to window_sec — no overlap).
        rule_dict: Dict of {metric: {min, max}} thresholds. Uses defaults if None.

    Returns:
        dict with: windows (list of classified windows), total_windows (int),
        accepted (int), rejected (int), acceptance_rate (float), mean_sqi (float).
    """
    from vital_sqi.signal_quality.quality_assessment import SignalQualityAssessment

    sig = np.array(signal)
    step = step_sec if step_sec is not None else window_sec
    win_samples = int(window_sec * fs)
    step_samples = int(step * fs)

    # Load default thresholds if not provided
    if rule_dict is None:
        try:
            from app.services.settings_service import get_threshold_cache
            rule_dict = get_threshold_cache()
        except Exception:
            rule_dict = {}

    windows = []
    i = 0
    while i + win_samples <= len(sig):
        segment = sig[i: i + win_samples]
        sqa = SignalQualityAssessment(segment, fs, signal_type=signal_type)
        scores = sqa.compute_all()
        overall = float(scores.get("overall_sqi", 0.0))

        failed_rules = []
        for metric, thresholds in (rule_dict or {}).items():
            val = scores.get(metric)
            if val is None:
                continue
            val = float(val)
            min_t = thresholds.get("min")
            max_t = thresholds.get("max")
            if min_t is not None and val < min_t:
                failed_rules.append({"metric": metric, "value": val, "threshold": min_t, "operator": "min"})
            if max_t is not None and val > max_t:
                failed_rules.append({"metric": metric, "value": val, "threshold": max_t, "operator": "max"})

        classification = "reject" if (failed_rules or overall < 0.5) else "accept"

        windows.append({
            "window_idx": len(windows),
            "start_sec": round(i / fs, 1),
            "end_sec": round((i + win_samples) / fs, 1),
            "sqi_score": round(overall, 3),
            "classification": classification,
            "failed_rules": failed_rules,
            "metrics": {k: round(float(v), 3) for k, v in scores.items()},
        })
        i += step_samples

    accepted = sum(1 for w in windows if w["classification"] == "accept")
    rejected = len(windows) - accepted
    mean_sqi = float(np.mean([w["sqi_score"] for w in windows])) if windows else 0.0

    return {
        "windows": windows,
        "total_windows": len(windows),
        "accepted": accepted,
        "rejected": rejected,
        "acceptance_rate": round(accepted / len(windows), 3) if windows else 0.0,
        "mean_sqi": round(mean_sqi, 3),
    }
