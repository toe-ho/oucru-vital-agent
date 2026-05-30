"""Registry of approved tools for the smolagents ToolCallingAgent.

Wraps each signal-processing function as a smolagents Tool subclass.
Falls back to an empty list if smolagents is not installed.
"""

from __future__ import annotations

from app.tools.clinical_threshold_tools import evaluate_thresholds
from app.tools.load_signal_file_tool import load_signal_file
from app.tools.sqi_tools import (
    check_clinical_thresholds,
    compute_sqi,
    compute_sqi_windowed,
    estimate_spo2,
    extract_hrv_features,
    extract_ppg_dc_layer,
    preprocess_ppg,
)

# Graceful import of smolagents
try:
    from smolagents import Tool
    _SMOLAGENTS_AVAILABLE = True
except ImportError:
    Tool = None  # type: ignore[assignment,misc]
    _SMOLAGENTS_AVAILABLE = False


def _make_tool(fn, name: str, description: str, inputs: dict, output_type: str):
    """Wrap a plain function as a smolagents Tool subclass."""
    if not _SMOLAGENTS_AVAILABLE or Tool is None:
        return None

    class _WrappedTool(Tool):
        def forward(self, **kwargs):
            return fn(**kwargs)

    _WrappedTool.name = name
    _WrappedTool.description = description
    _WrappedTool.inputs = inputs
    _WrappedTool.output_type = output_type
    return _WrappedTool()


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

_TOOL_SPECS = [
    (
        load_signal_file,
        "load_signal_file",
        "Load a signal file and return metadata and statistics. Does NOT return raw samples.",
        {
            "recording_id": {"type": "string", "description": "UUID of the recording"},
            "storage_uri": {"type": "string", "description": "Absolute path to the signal file"},
            "signal_column": {"type": "string", "description": "Column name of the signal"},
            "sampling_rate": {"type": "integer", "description": "Sampling rate in Hz"},
            "file_format": {"type": "string", "description": "File format: csv or parquet"},
        },
        "object",
    ),
    (
        compute_sqi,
        "compute_sqi",
        "Compute a single SQI metric (snr, kurtosis, skewness) for a signal reference.",
        {
            "signal_ref": {"type": "object", "description": "SignalRef dict"},
            "metric": {"type": "string", "description": "Metric name: snr, kurtosis, skewness"},
        },
        "object",
    ),
    (
        compute_sqi_windowed,
        "compute_sqi_windowed",
        "Compute an SQI metric over non-overlapping time windows.",
        {
            "signal_ref": {"type": "object", "description": "SignalRef dict"},
            "window_s": {"type": "integer", "description": "Window duration in seconds"},
            "metric": {"type": "string", "description": "Metric name"},
        },
        "object",
    ),
    (
        preprocess_ppg,
        "preprocess_ppg",
        "Apply bandpass filter (0.5–8 Hz) to a PPG signal. Returns filter metadata only.",
        {
            "signal_ref": {"type": "object", "description": "SignalRef dict"},
        },
        "object",
    ),
    (
        extract_hrv_features,
        "extract_hrv_features",
        "Detect peaks and compute time-domain HRV features (mean_rr, sdnn, rmssd, pnn50).",
        {
            "signal_ref": {"type": "object", "description": "SignalRef dict"},
        },
        "object",
    ),
    (
        estimate_spo2,
        "estimate_spo2",
        "Estimate SpO2 using perfusion index heuristic.",
        {
            "signal_ref": {"type": "object", "description": "SignalRef dict"},
        },
        "object",
    ),
    (
        extract_ppg_dc_layer,
        "extract_ppg_dc_layer",
        "Extract DC baseline layer of a PPG signal via low-pass filter.",
        {
            "signal_ref": {"type": "object", "description": "SignalRef dict"},
        },
        "object",
    ),
    (
        check_clinical_thresholds,
        "check_clinical_thresholds",
        "Check metric values against threshold bounds, returning violations.",
        {
            "metrics": {"type": "object", "description": "Dict of metric_name → value"},
            "thresholds": {"type": "object", "description": "Dict of metric_name → {min, max}"},
        },
        "object",
    ),
    (
        evaluate_thresholds,
        "evaluate_thresholds",
        "Evaluate metric values against configurable threshold config, returning pass/fail per metric.",
        {
            "metric_values": {"type": "object", "description": "Dict of metric_name → value"},
            "threshold_config": {"type": "object", "description": "Dict of metric_name → {min, max}"},
        },
        "object",
    ),
]


def build_tool_registry() -> list:
    """Return list of smolagents Tool instances for all approved tools.

    Returns empty list if smolagents is not installed.
    """
    if not _SMOLAGENTS_AVAILABLE:
        return []
    tools = []
    for fn, name, desc, inputs, output_type in _TOOL_SPECS:
        tool = _make_tool(fn, name, desc, inputs, output_type)
        if tool is not None:
            tools.append(tool)
    return tools
