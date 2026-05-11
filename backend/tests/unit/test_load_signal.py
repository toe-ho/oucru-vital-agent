"""Unit tests for load_signal_file."""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from app.tools.signal_loader import load_signal_file


@pytest.fixture
def csv_file(tmp_path) -> str:
    sig = np.sin(np.linspace(0, 30, 3000))
    pd.DataFrame({"ppg": sig, "ecg": sig * 0.8}).to_csv(tmp_path / "test.csv", index=False)
    return str(tmp_path / "test.csv")


@pytest.fixture
def parquet_file(tmp_path) -> str:
    sig = np.sin(np.linspace(0, 30, 3000))
    pd.DataFrame({"ppg": sig}).to_parquet(tmp_path / "test.parquet")
    return str(tmp_path / "test.parquet")


def test_load_csv_returns_signal(csv_file):
    result = load_signal_file(csv_file, column="ppg", fs=100)
    assert "signal" in result
    assert len(result["signal"]) == 3000


def test_load_csv_metadata(csv_file):
    result = load_signal_file(csv_file, column="ppg", fs=100)
    assert result["fs"] == 100
    assert result["n_samples"] == 3000
    assert result["duration_sec"] == 30.0
    assert "columns_available" in result


def test_load_parquet(parquet_file):
    result = load_signal_file(parquet_file, column="ppg", fs=100)
    assert len(result["signal"]) == 3000


def test_load_multichannel(csv_file):
    result = load_signal_file(csv_file, column="ppg,ecg", fs=100)
    assert isinstance(result["signal"], dict)
    assert "ppg" in result["signal"]
    assert "ecg" in result["signal"]


def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_signal_file("/nonexistent/path/signal.csv")


def test_load_missing_column(csv_file):
    with pytest.raises(ValueError, match="not found"):
        load_signal_file(csv_file, column="missing_col", fs=100)


def test_load_unsupported_format(tmp_path):
    f = tmp_path / "signal.xyz"
    f.write_text("dummy")
    with pytest.raises(ValueError, match="Unsupported"):
        load_signal_file(str(f))


def test_load_unusual_sampling_rate(csv_file):
    result = load_signal_file(csv_file, column="ppg", fs=50)
    assert result["fs"] == 50
    assert result["duration_sec"] == 60.0  # 3000 / 50


def test_load_columns_available(csv_file):
    result = load_signal_file(csv_file, column="ppg", fs=100)
    assert "ppg" in result["columns_available"]
    assert "ecg" in result["columns_available"]
