"""Tool 6: estimate_spo2 — vitalDSP SpO2 wrapper."""
from __future__ import annotations

import numpy as np

try:
    from smolagents import tool
except ImportError:
    def tool(fn):
        return fn


@tool
def estimate_spo2(red_signal: list, ir_signal: list, fs: int = 100) -> dict:
    """
    Estimate blood oxygen saturation (SpO2) from red and infrared PPG channels.

    Uses the ratio-of-ratios method via vitalDSP.

    Args:
        red_signal: Red channel PPG as list of floats.
        ir_signal: Infrared channel PPG as list of floats.
        fs: Sampling frequency in Hz.

    Returns:
        dict with: spo2_pct (float), perfusion_index (float),
        confidence ("high" | "medium" | "low").
    """
    from vitaldsp.spo2_analysis import SpO2Analysis

    red = np.array(red_signal)
    ir = np.array(ir_signal)

    spo2_obj = SpO2Analysis(red, ir, fs)
    result = spo2_obj.estimate_spo2()

    spo2_val = float(result.get("spo2", 0))
    pi = float(result.get("perfusion_index", 0))
    confidence = "high" if pi > 0.5 else ("medium" if pi > 0.2 else "low")

    return {
        "spo2_pct": round(spo2_val, 1),
        "perfusion_index": round(pi, 3),
        "confidence": confidence,
    }
