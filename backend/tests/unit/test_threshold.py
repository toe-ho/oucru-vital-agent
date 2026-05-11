"""Unit tests for check_clinical_thresholds."""
import pytest
from app.tools.threshold_tools import check_clinical_thresholds


def test_normal_values_no_flags():
    result = check_clinical_thresholds(heart_rate_bpm=72.0, spo2_pct=98.0, sqi_score=0.85)
    assert result["flags"] == []
    assert not result["any_critical"]
    assert not result["any_warning"]


def test_bradycardia_flagged():
    result = check_clinical_thresholds(heart_rate_bpm=35.0)
    assert len(result["flags"]) >= 1
    notes = [f["note"] for f in result["flags"]]
    assert any("Bradycardia" in n for n in notes)


def test_tachycardia_flagged():
    result = check_clinical_thresholds(heart_rate_bpm=210.0)
    notes = [f["note"] for f in result["flags"]]
    assert any("Tachycardia" in n for n in notes)


def test_hypoxemia_is_critical():
    result = check_clinical_thresholds(spo2_pct=85.0)
    assert result["any_critical"]
    notes = [f["note"] for f in result["flags"]]
    assert any("Hypoxemia" in n for n in notes)


def test_poor_sqi_is_warning():
    result = check_clinical_thresholds(sqi_score=0.2)
    assert result["any_warning"] or result["any_critical"]


def test_multiple_flags():
    result = check_clinical_thresholds(heart_rate_bpm=35.0, spo2_pct=85.0)
    assert len(result["flags"]) >= 2


def test_missing_optional_values_no_crash():
    result = check_clinical_thresholds()
    assert result["flags"] == []


def test_none_values_no_crash():
    result = check_clinical_thresholds(heart_rate_bpm=None, spo2_pct=None, sqi_score=None)
    assert result["flags"] == []


def test_summary_string_present(capsys):
    result = check_clinical_thresholds(heart_rate_bpm=72.0)
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0


def test_flag_severity_field():
    result = check_clinical_thresholds(heart_rate_bpm=35.0)
    for flag in result["flags"]:
        assert "severity" in flag
        assert flag["severity"] in ("warning", "critical")
