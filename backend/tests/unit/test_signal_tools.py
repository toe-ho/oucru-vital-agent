"""Unit tests for signal tool wrappers — no LLM, no DB required."""
import sys
import tempfile
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def ppg_signal(duration: int = 30, fs: int = 100, hr: float = 70) -> list:
    t = np.linspace(0, duration, duration * fs)
    hz = hr / 60
    return (0.6 * np.sin(2 * np.pi * hz * t) + 0.05 * np.random.randn(len(t))).tolist()


def save_csv(signal: list, column: str = "ppg") -> str:
    f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    pd.DataFrame({column: signal}).to_csv(f.name, index=False)
    return f.name


def test_load_signal_file_csv():
    from app.tools.signal_loader import load_signal_file
    path = save_csv(ppg_signal())
    try:
        result = load_signal_file(path, column="ppg", fs=100)
        assert result["n_samples"] == 3000
        assert result["fs"] == 100
        assert result["duration_sec"] == 30.0
    finally:
        os.unlink(path)


def test_load_signal_file_missing():
    from app.tools.signal_loader import load_signal_file
    with pytest.raises(FileNotFoundError):
        load_signal_file("/nonexistent/file.csv")


def test_check_clinical_thresholds_normal():
    from app.tools.threshold_tools import check_clinical_thresholds
    result = check_clinical_thresholds(heart_rate_bpm=72.0, spo2_pct=98.0, sqi_score=0.85)
    assert result["flags"] == []
    assert not result["any_critical"]
    assert not result["any_warning"]


def test_check_clinical_thresholds_bradycardia():
    from app.tools.threshold_tools import check_clinical_thresholds
    result = check_clinical_thresholds(heart_rate_bpm=35.0)
    assert len(result["flags"]) == 1
    assert result["any_warning"]


def test_check_clinical_thresholds_hypoxemia():
    from app.tools.threshold_tools import check_clinical_thresholds
    result = check_clinical_thresholds(spo2_pct=85.0)
    assert result["any_critical"]


def test_tool_wrapper_catches_exception():
    from app.tools.base import ToolResult, tool_wrapper

    @tool_wrapper
    def bad_tool():
        raise ValueError("test error")

    result = bad_tool()
    assert isinstance(result, ToolResult)
    assert not result.success
    assert result.error_type == "ValueError"
    assert "test error" in result.error_detail
