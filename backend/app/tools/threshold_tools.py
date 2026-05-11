"""Tool 8: check_clinical_thresholds — structured clinical/quality flags."""
from __future__ import annotations

try:
    from smolagents import tool
except ImportError:
    def tool(fn):
        return fn


@tool
def check_clinical_thresholds(
    heart_rate_bpm: float | None = None,
    spo2_pct: float | None = None,
    sqi_score: float | None = None,
) -> dict:
    """
    Flag heart rate, SpO2, and SQI values against configured clinical thresholds.

    Reads thresholds from the settings service (runtime-configurable via the
    Settings API). Falls back to config.yaml defaults if the DB is unreachable.

    Args:
        heart_rate_bpm: Mean heart rate in BPM. Pass None to skip.
        spo2_pct: SpO2 percentage. Pass None to skip.
        sqi_score: Signal quality index 0–1. Pass None to skip.

    Returns:
        dict with: flags (list), any_critical (bool), any_warning (bool), summary (str).
    """
    try:
        from app.services.settings_service import get_threshold_cache
        thr_map = get_threshold_cache()
        hr_min = thr_map.get("mean_hr", {}).get("min", 40)
        hr_max = thr_map.get("mean_hr", {}).get("max", 200)
        spo2_min = 88.0
        sqi_min = 0.5
    except Exception:
        from app.config import agent_config
        hr_min = agent_config.sqi_thresholds.get("hr_min", 40)
        hr_max = agent_config.sqi_thresholds.get("hr_max", 200)
        spo2_min = agent_config.sqi_thresholds.get("spo2_min", 88)
        sqi_min = agent_config.sqi_thresholds.get("sqi_min", 0.5)

    flags = []

    if heart_rate_bpm is not None:
        if heart_rate_bpm < hr_min:
            flags.append({
                "metric": "heart_rate_bpm", "value": heart_rate_bpm,
                "threshold": hr_min, "operator": "min",
                "severity": "warning", "note": f"Bradycardia (HR={heart_rate_bpm:.1f} bpm)",
            })
        elif heart_rate_bpm > hr_max:
            flags.append({
                "metric": "heart_rate_bpm", "value": heart_rate_bpm,
                "threshold": hr_max, "operator": "max",
                "severity": "warning", "note": f"Tachycardia (HR={heart_rate_bpm:.1f} bpm)",
            })

    if spo2_pct is not None and spo2_pct < spo2_min:
        flags.append({
            "metric": "spo2_pct", "value": spo2_pct,
            "threshold": spo2_min, "operator": "min",
            "severity": "critical", "note": f"Hypoxemia (SpO2={spo2_pct:.1f}%)",
        })

    if sqi_score is not None and sqi_score < sqi_min:
        flags.append({
            "metric": "sqi_score", "value": sqi_score,
            "threshold": sqi_min, "operator": "min",
            "severity": "warning", "note": f"Poor signal quality (SQI={sqi_score:.2f})",
        })

    any_critical = any(f["severity"] == "critical" for f in flags)
    any_warning = any(f["severity"] == "warning" for f in flags) and not any_critical
    summary = "All values within normal range." if not flags else "Flags: " + "; ".join(f["note"] for f in flags)

    return {"flags": flags, "any_critical": any_critical, "any_warning": any_warning, "summary": summary}
