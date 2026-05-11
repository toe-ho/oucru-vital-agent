"""Tool 1: load_signal_file — load CSV, Parquet, or WFDB waveform files."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from smolagents import tool
except ImportError:
    def tool(fn):
        return fn


@tool
def load_signal_file(file_path: str, column: str = "ppg", fs: int = 100) -> dict:
    """
    Load a physiological signal from a CSV, Parquet, or WFDB file.

    Args:
        file_path: Path to the signal file (.csv, .parquet, or WFDB record).
        column: Column name containing the signal (comma-separated for multi-channel).
        fs: Sampling frequency in Hz.

    Returns:
        dict with: signal (list), fs (int), n_samples (int),
        duration_sec (float), columns_available (list), file_path (str).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Signal file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".parquet":
        df = pd.read_parquet(path)
    elif suffix in (".csv", ".txt"):
        df = pd.read_csv(path)
    elif suffix in ("", ".hea", ".dat"):
        try:
            import wfdb
            record = wfdb.rdrecord(str(path.with_suffix("")))
            df = pd.DataFrame(record.p_signal, columns=record.sig_name)
            fs = record.fs
        except Exception as e:
            raise ValueError(f"Could not read WFDB record: {e}") from e
    else:
        raise ValueError(f"Unsupported format: {suffix}. Use .csv, .parquet, or WFDB.")

    columns = [c.strip() for c in column.split(",")]
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Columns {missing} not found. Available: {list(df.columns)}")

    if len(columns) == 1:
        signal = df[columns[0]].dropna().tolist()
    else:
        signal = {c: df[c].dropna().tolist() for c in columns}

    n_samples = len(df[columns[0]])
    return {
        "signal": signal,
        "fs": fs,
        "n_samples": n_samples,
        "duration_sec": round(n_samples / fs, 2),
        "columns_available": list(df.columns),
        "file_path": str(file_path),
    }
