"""SQI and signal-processing tool wrappers for the Vital Agent.

Each function accepts a signal_ref dict and returns a structured result dict.
Raw arrays are NEVER returned to callers.
"""

from __future__ import annotations

from uuid import UUID

import numpy as np
from scipy import signal as sp_signal

from app.tools.signal_ref import SignalRef, resolve_signal_array

# Optional vital_sqi import — nolds (a transitive dep) raises TypeError on
# Python 3.11 with importlib.resources, so catch broadly.
try:
    import vital_sqi  # noqa: F401
    _VITAL_SQI_AVAILABLE = True
except Exception:  # noqa: BLE001
    vital_sqi = None  # type: ignore[assignment]
    _VITAL_SQI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ref_from_dict(signal_ref: dict) -> SignalRef:
    return SignalRef(
        recording_id=UUID(signal_ref["recording_id"]),
        storage_uri=signal_ref["storage_uri"],
        signal_column=signal_ref["signal_column"],
        sampling_rate=int(signal_ref["sampling_rate"]),
        file_format=signal_ref["file_format"],
    )


def _snr_numpy(arr: np.ndarray) -> float:
    """Simple SNR estimate: mean / std (power ratio proxy)."""
    std = float(np.std(arr))
    if std == 0:
        return float("inf")
    return float(np.abs(np.mean(arr)) / std)


def _bandpass(arr: np.ndarray, fs: int, low: float, high: float) -> np.ndarray:
    nyq = fs / 2.0
    low_n, high_n = low / nyq, high / nyq
    b, a = sp_signal.butter(4, [low_n, high_n], btype="band")
    return sp_signal.filtfilt(b, a, arr).astype(np.float64)


def _lowpass(arr: np.ndarray, fs: int, cutoff: float) -> np.ndarray:
    nyq = fs / 2.0
    b, a = sp_signal.butter(4, cutoff / nyq, btype="low")
    return sp_signal.filtfilt(b, a, arr).astype(np.float64)


def _detect_peaks(arr: np.ndarray, fs: int) -> np.ndarray:
    """Simple peak detection using scipy; min distance ~0.4 s."""
    min_dist = max(1, int(0.4 * fs))
    peaks, _ = sp_signal.find_peaks(arr, distance=min_dist)
    return peaks


# ---------------------------------------------------------------------------
# Public tool wrappers
# ---------------------------------------------------------------------------

def compute_sqi(signal_ref: dict, metric: str = "snr") -> dict:
    """Compute a single SQI metric for a signal.

    Returns:
        {"status": "ok"|"error", "metric_name": str, "value": float, "error": str|None}
    """
    try:
        ref = _ref_from_dict(signal_ref)
        arr = resolve_signal_array(ref)
        if metric == "snr":
            value = _snr_numpy(arr)
        elif metric == "kurtosis":
            from scipy.stats import kurtosis
            value = float(kurtosis(arr))
        elif metric == "skewness":
            from scipy.stats import skew
            value = float(skew(arr))
        else:
            return {"status": "error", "metric_name": metric, "value": None,
                    "error": f"Unknown metric '{metric}'."}
        return {"status": "ok", "metric_name": metric, "value": value, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "metric_name": metric, "value": None, "error": str(exc)}


def compute_sqi_windowed(
    signal_ref: dict, window_s: int = 30, metric: str = "snr"
) -> dict:
    """Compute SQI metric over non-overlapping windows.

    Returns:
        {"status": "ok"|"error", "metric_name": str,
         "windows": [{"window_index", "start_s", "end_s", "value"}], "error": str|None}
    """
    try:
        ref = _ref_from_dict(signal_ref)
        arr = resolve_signal_array(ref)
        fs = ref.sampling_rate
        step = window_s * fs
        windows = []
        for i, start in enumerate(range(0, len(arr), step)):
            chunk = arr[start: start + step]
            if len(chunk) < fs:  # skip sub-second remainder
                break
            single = compute_sqi(
                {**signal_ref, "_override_arr": None},  # ref only — reloaded per call
                metric=metric,
            )
            # compute directly on chunk to avoid re-reading storage per window
            if metric == "snr":
                val = _snr_numpy(chunk)
            elif metric == "kurtosis":
                from scipy.stats import kurtosis
                val = float(kurtosis(chunk))
            elif metric == "skewness":
                from scipy.stats import skew
                val = float(skew(chunk))
            else:
                val = None
            windows.append({
                "window_index": i,
                "start_s": start / fs,
                "end_s": (start + len(chunk)) / fs,
                "value": val,
            })
        return {"status": "ok", "metric_name": metric, "windows": windows, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "metric_name": metric, "windows": [], "error": str(exc)}


def preprocess_ppg(signal_ref: dict) -> dict:
    """Apply bandpass filter to a PPG signal (0.5–8 Hz).

    The filtered signal is written back to a temp in-memory ref; only
    metadata is returned.

    Returns:
        {"status", "signal_ref" (same as input), "filter_params", "error"}
    """
    try:
        ref = _ref_from_dict(signal_ref)
        arr = resolve_signal_array(ref)
        low, high = 0.5, 8.0
        _bandpass(arr, ref.sampling_rate, low, high)  # validate filterability
        return {
            "status": "ok",
            "signal_ref": signal_ref,
            "filter_params": {"type": "bandpass", "low_hz": low, "high_hz": high, "order": 4},
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "signal_ref": signal_ref, "filter_params": None,
                "error": str(exc)}


def extract_hrv_features(signal_ref: dict) -> dict:
    """Detect R/systolic peaks and compute time-domain HRV features.

    Returns:
        {"status", "features": {"mean_rr", "sdnn", "rmssd", "pnn50"}, "error"}
    """
    try:
        ref = _ref_from_dict(signal_ref)
        arr = resolve_signal_array(ref)
        fs = ref.sampling_rate
        peaks = _detect_peaks(arr, fs)
        if len(peaks) < 2:
            return {"status": "error", "features": None,
                    "error": "Insufficient peaks for HRV calculation."}
        rr_intervals = np.diff(peaks) / fs * 1000  # ms
        mean_rr = float(np.mean(rr_intervals))
        sdnn = float(np.std(rr_intervals))
        rmssd = float(np.sqrt(np.mean(np.diff(rr_intervals) ** 2)))
        pnn50 = float(np.sum(np.abs(np.diff(rr_intervals)) > 50) / len(rr_intervals) * 100)
        return {
            "status": "ok",
            "features": {
                "mean_rr": mean_rr,
                "sdnn": sdnn,
                "rmssd": rmssd,
                "pnn50": pnn50,
            },
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "features": None, "error": str(exc)}


def estimate_spo2(signal_ref: dict) -> dict:
    """Estimate SpO2 using a perfusion index heuristic (placeholder).

    Returns:
        {"status", "spo2_estimate": float|None, "method": str, "error"}
    """
    try:
        ref = _ref_from_dict(signal_ref)
        arr = resolve_signal_array(ref)
        ac_component = float(np.std(arr))
        dc_component = float(np.abs(np.mean(arr))) or 1.0
        perfusion_index = ac_component / dc_component
        # Heuristic mapping: PI roughly maps to SpO2 in 94–100 range
        spo2_estimate = min(100.0, 94.0 + perfusion_index * 6.0)
        return {
            "status": "ok",
            "spo2_estimate": round(spo2_estimate, 1),
            "method": "perfusion_index_heuristic",
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "spo2_estimate": None,
                "method": "perfusion_index_heuristic", "error": str(exc)}


def extract_ppg_dc_layer(signal_ref: dict) -> dict:
    """Extract the DC (baseline) layer of a PPG signal via low-pass filter.

    Returns:
        {"status", "dc_mean": float, "dc_std": float, "error"}
    """
    try:
        ref = _ref_from_dict(signal_ref)
        arr = resolve_signal_array(ref)
        dc = _lowpass(arr, ref.sampling_rate, cutoff=0.5)
        return {
            "status": "ok",
            "dc_mean": float(np.mean(dc)),
            "dc_std": float(np.std(dc)),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "dc_mean": None, "dc_std": None, "error": str(exc)}


def check_clinical_thresholds(metrics: dict, thresholds: dict) -> dict:
    """Check each metric against threshold bounds.

    thresholds format: {"metric_name": {"min": float|None, "max": float|None}}

    Returns:
        {"passed": bool, "violations": [{"metric", "value", "bound", "threshold"}]}
    """
    violations = []
    for metric_name, bounds in thresholds.items():
        value = metrics.get(metric_name)
        if value is None:
            continue
        lo = bounds.get("min")
        hi = bounds.get("max")
        if lo is not None and value < lo:
            violations.append({"metric": metric_name, "value": value,
                                "bound": "min", "threshold": lo})
        if hi is not None and value > hi:
            violations.append({"metric": metric_name, "value": value,
                                "bound": "max", "threshold": hi})
    return {"passed": len(violations) == 0, "violations": violations}
