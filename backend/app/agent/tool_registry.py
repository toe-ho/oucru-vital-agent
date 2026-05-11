"""Register all 8 OUCRU tools with smolagents."""
from __future__ import annotations

from app.tools.hrv_tools import extract_hrv_features
from app.tools.ppg_tools import extract_ppg_dc_layer, preprocess_ppg
from app.tools.signal_loader import load_signal_file
from app.tools.spo2_tools import estimate_spo2
from app.tools.sqi_tools import compute_sqi, compute_sqi_windowed
from app.tools.threshold_tools import check_clinical_thresholds

ALL_TOOLS = [
    load_signal_file,
    compute_sqi,
    compute_sqi_windowed,
    preprocess_ppg,
    extract_hrv_features,
    estimate_spo2,
    extract_ppg_dc_layer,
    check_clinical_thresholds,
]
