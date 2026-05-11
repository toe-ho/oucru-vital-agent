"""Tools 4, 7: preprocess_ppg and extract_ppg_dc_layer — vitalDSP wrappers."""
from __future__ import annotations

import numpy as np

try:
    from smolagents import tool
except ImportError:
    def tool(fn):
        return fn


@tool
def preprocess_ppg(signal: list, fs: int = 100) -> dict:
    """
    Filter, normalize, and detect peaks in a raw PPG signal.

    Steps: bandpass 0.5–8 Hz → normalize → peak detection.

    Args:
        signal: Raw PPG signal as list of floats.
        fs: Sampling frequency in Hz.

    Returns:
        dict with: filtered_signal, peaks_indices, rr_intervals_ms,
        heart_rate_bpm, n_peaks.
    """
    from vitaldsp.signal_processing import SignalProcessing
    from vitaldsp.peak_detection import PeakDetection

    sig = np.array(signal)
    sp = SignalProcessing(sig, fs)
    filtered = sp.bandpass_filter(lowcut=0.5, highcut=8.0)
    filtered = (filtered - np.mean(filtered)) / (np.std(filtered) + 1e-8)

    pd_obj = PeakDetection(filtered, fs)
    peaks = pd_obj.detect_peaks()

    rr_ms = np.diff(peaks) / fs * 1000
    hr = 60000 / np.mean(rr_ms) if len(rr_ms) > 0 else None

    return {
        "filtered_signal": filtered.tolist(),
        "peaks_indices": peaks.tolist(),
        "rr_intervals_ms": rr_ms.tolist(),
        "heart_rate_bpm": round(float(hr), 1) if hr is not None else None,
        "n_peaks": len(peaks),
    }


@tool
def extract_ppg_dc_layer(signal: list, fs: int = 100) -> dict:
    """
    Extract the DC (low-frequency baseline) component of a PPG signal.

    Lowpass filter at 0.5 Hz retains respiratory and vasomotor components.

    Args:
        signal: Raw PPG signal as list of floats.
        fs: Sampling frequency in Hz.

    Returns:
        dict with: dc_trend (downsampled to 10 Hz), mean_dc, dc_variance.
    """
    from vitaldsp.signal_processing import SignalProcessing

    sig = np.array(signal)
    sp = SignalProcessing(sig, fs)
    dc = sp.lowpass_filter(cutoff=0.5)

    downsample_factor = max(1, fs // 10)
    dc_downsampled = dc[::downsample_factor].tolist()

    return {
        "dc_trend": dc_downsampled,
        "mean_dc": round(float(np.mean(dc)), 4),
        "dc_variance": round(float(np.var(dc)), 6),
    }
