"""Tool wrapper: load a signal file and return metadata + stats only.

Raw sample arrays are NEVER included in the returned dict.
"""

from uuid import UUID

import numpy as np

from app.tools.signal_ref import SignalRef, resolve_signal_array


def load_signal_file(
    recording_id: str,
    storage_uri: str,
    signal_column: str,
    sampling_rate: int,
    file_format: str,
) -> dict:
    """Return signal metadata and statistics — NOT raw samples.

    Result keys:
        recording_id    str UUID
        duration_seconds float
        sample_count    int
        sampling_rate   int
        mean            float
        std             float
        min             float
        max             float
        signal_ref      dict  (reconstructable into SignalRef for downstream tools)
    """
    ref = SignalRef(
        recording_id=UUID(recording_id),
        storage_uri=storage_uri,
        signal_column=signal_column,
        sampling_rate=sampling_rate,
        file_format=file_format,
    )
    arr: np.ndarray = resolve_signal_array(ref)

    return {
        "recording_id": recording_id,
        "duration_seconds": len(arr) / sampling_rate,
        "sample_count": len(arr),
        "sampling_rate": sampling_rate,
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "signal_ref": {
            "recording_id": recording_id,
            "storage_uri": storage_uri,
            "signal_column": signal_column,
            "sampling_rate": sampling_rate,
            "file_format": file_format,
        },
    }
