"""Unit tests for estimate_spo2."""
import numpy as np
import pytest
from app.tools.spo2_tools import estimate_spo2


@pytest.fixture
def red_ir_signals():
    t = np.linspace(0, 30, 3000)
    hr_hz = 70 / 60
    red = 0.6 * np.sin(2 * np.pi * hr_hz * t) + 1.5
    ir = 0.8 * np.sin(2 * np.pi * hr_hz * t) + 2.0
    return red.tolist(), ir.tolist()


def test_spo2_returns_percentage(red_ir_signals):
    red, ir = red_ir_signals
    result = estimate_spo2(red, ir, fs=100)
    assert "spo2_pct" in result
    assert 0.0 <= result["spo2_pct"] <= 100.0


def test_spo2_returns_perfusion_index(red_ir_signals):
    red, ir = red_ir_signals
    result = estimate_spo2(red, ir, fs=100)
    assert "perfusion_index" in result
    assert result["perfusion_index"] >= 0.0


def test_spo2_returns_confidence_label(red_ir_signals):
    red, ir = red_ir_signals
    result = estimate_spo2(red, ir, fs=100)
    assert result["confidence"] in ("high", "medium", "low")


def test_spo2_mismatched_lengths_raises():
    red = [0.5] * 3000
    ir = [0.6] * 2000
    with pytest.raises(Exception):
        estimate_spo2(red, ir, fs=100)


def test_spo2_short_signal_does_not_crash():
    t = np.linspace(0, 5, 500)
    hr_hz = 70 / 60
    red = (0.6 * np.sin(2 * np.pi * hr_hz * t) + 1.5).tolist()
    ir = (0.8 * np.sin(2 * np.pi * hr_hz * t) + 2.0).tolist()
    result = estimate_spo2(red, ir, fs=100)
    assert "spo2_pct" in result
