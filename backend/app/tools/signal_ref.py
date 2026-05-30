"""SignalRef dataclass and array resolver.

Raw numpy arrays are NEVER returned to agent callers — only stats/metadata.
"""

import io
from dataclasses import dataclass
from uuid import UUID

import numpy as np
import pandas as pd

from app.services import storage_service


@dataclass
class SignalRef:
    """Lightweight pointer to a persisted signal — no raw data in memory."""

    recording_id: UUID
    storage_uri: str
    signal_column: str
    sampling_rate: int
    file_format: str  # "csv" or "parquet"


def resolve_signal_array(ref: SignalRef) -> np.ndarray:
    """Load and return the numpy array for a signal column.

    This function is INTERNAL — callers must NOT expose the returned array
    to agent prompts or HTTP responses.  Use compute_stats() or tool wrappers
    to surface summaries only.
    """
    raw = storage_service.read_file(ref.storage_uri)
    if ref.file_format == "parquet":
        df = pd.read_parquet(io.BytesIO(raw))
    else:
        df = pd.read_csv(io.BytesIO(raw))
    return df[ref.signal_column].to_numpy(dtype=np.float64)
