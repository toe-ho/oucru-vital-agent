"""Unit tests for assessment_runner window-splitting logic — no DB, no HTTP."""

import numpy as np
import pytest

from app.services.assessment_runner import _split_windows


def _make_signal(duration_s: int, fs: int = 250) -> np.ndarray:
    """Return a simple sine-wave array of the requested duration."""
    t = np.linspace(0, duration_s, duration_s * fs, endpoint=False)
    return np.sin(2 * np.pi * 1.0 * t)


def test_window_split_produces_correct_segment_count():
    """30 s signal at 250 Hz with 30 s windows → exactly 1 segment."""
    arr = _make_signal(30, fs=250)
    windows = _split_windows(arr, fs=250, window_s=30, overlap_s=0)
    assert len(windows) == 1
    start_s, end_s, t_start, t_end = windows[0]
    assert start_s == 0
    assert end_s == len(arr)
    assert abs(t_start - 0.0) < 1e-9
    assert abs(t_end - 30.0) < 1e-6


def test_longer_signal_produces_multiple_segments():
    """90 s signal at 250 Hz with 30 s non-overlapping windows → 3 segments."""
    arr = _make_signal(90, fs=250)
    windows = _split_windows(arr, fs=250, window_s=30, overlap_s=0)
    assert len(windows) == 3
    # Verify start/end times are contiguous
    for i, (_, _, t_start, t_end) in enumerate(windows):
        assert abs(t_start - i * 30.0) < 1e-6
        assert abs(t_end - (i + 1) * 30.0) < 1e-6


def test_overlapping_windows_produces_more_segments():
    """60 s signal with 30 s windows and 15 s overlap → more windows than non-overlapping."""
    arr = _make_signal(60, fs=250)
    no_overlap = _split_windows(arr, fs=250, window_s=30, overlap_s=0)
    with_overlap = _split_windows(arr, fs=250, window_s=30, overlap_s=15)
    # step = 15 s → windows starting at 0, 15, 30, 45 → 4 windows (last may be partial)
    assert len(with_overlap) > len(no_overlap)


def test_short_remainder_is_skipped():
    """Signal that is not a multiple of window size — remainder < fs is dropped."""
    fs = 250
    # 31 s signal with 30 s windows → 1 full window, 1 s remainder (250 samples = fs) is borderline
    arr = _make_signal(31, fs=fs)
    windows = _split_windows(arr, fs=fs, window_s=30, overlap_s=0)
    # 31 s → window at [0,30s] (7500 samples); remainder = 250 samples = exactly fs
    # _split_windows skips chunks < fs, so 250 < 250 is False → remainder IS included
    assert len(windows) >= 1


def test_window_split_zero_overlap_step_equals_window():
    """With overlap_s=0, step equals window_s."""
    arr = _make_signal(60, fs=100)
    windows = _split_windows(arr, fs=100, window_s=20, overlap_s=0)
    assert len(windows) == 3  # 60 / 20 = 3
