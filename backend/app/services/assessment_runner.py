"""Deterministic assessment runner: splits signal into windows, computes SQI, persists results."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import numpy as np

from app.models.recording_models import AssessmentJob, Recording
from app.models.segment_models import Segment, SqiResult
from app.services import agent_log_service
from app.services.segment_classification_service import classify_segment
from app.tools.signal_ref import SignalRef, resolve_signal_array


def _build_signal_ref(recording: Recording, signal_column: str, sampling_rate: int) -> SignalRef:
    return SignalRef(
        recording_id=recording.id,
        storage_uri=recording.storage_uri or "",
        signal_column=signal_column,
        sampling_rate=sampling_rate,
        file_format=recording.file_format,
    )


def _split_windows(
    arr: np.ndarray,
    fs: int,
    window_s: int,
    overlap_s: int,
) -> list[tuple[int, int, float, float]]:
    """Return list of (start_sample, end_sample, start_time_s, end_time_s)."""
    step_s = window_s - overlap_s
    if step_s <= 0:
        step_s = window_s
    step = step_s * fs
    window_len = window_s * fs
    windows = []
    start = 0
    while start < len(arr):
        end = start + window_len
        if end > len(arr):
            end = len(arr)
        # skip windows shorter than min useful length (1 sample)
        if end - start < fs:
            break
        windows.append((start, end, start / fs, end / fs))
        start += step
    return windows


def _compute_metric(chunk: np.ndarray, metric: str) -> float | None:
    """Compute a single metric on a numpy chunk; return None on failure."""
    try:
        if metric == "snr":
            std = float(np.std(chunk))
            return float("inf") if std == 0 else float(np.abs(np.mean(chunk)) / std)
        if metric == "kurtosis":
            from scipy.stats import kurtosis
            return float(kurtosis(chunk))
        if metric == "skewness":
            from scipy.stats import skew
            return float(skew(chunk))
        if metric == "zero_crossing_rate":
            crossings = float(np.sum(np.diff(np.sign(chunk)) != 0))
            return crossings / len(chunk) if len(chunk) > 1 else 0.0
        if metric == "perfusion_index":
            dc = float(np.abs(np.mean(chunk))) or 1.0
            return float(np.std(chunk)) / dc
    except Exception:  # noqa: BLE001
        return None
    return None


def _check_threshold(value: float | None, rule: dict) -> bool | None:
    """Return True/False if value is present; None if value is missing."""
    if value is None:
        return None
    lo = rule.get("min")
    hi = rule.get("max")
    if lo is not None and value < lo:
        return False
    if hi is not None and value > hi:
        return False
    return True


async def run_deterministic_assessment(
    job: AssessmentJob,
    recording: Recording,
    db,
    signal_column: str,
    sampling_rate: int,
    config: dict,
) -> None:
    """Run the full deterministic SQI pipeline for one job.

    Mutates job.total_segments, job.processed_segments, job.progress_pct in place.
    Caller is responsible for committing the session.
    """
    assessment_cfg = config.get("assessment", {})
    window_s = int(assessment_cfg.get("window_duration_seconds", 30))
    overlap_s = int(assessment_cfg.get("overlap_seconds", 0))
    metrics: list[str] = assessment_cfg.get("metrics", ["snr"])
    rule_dict: dict = assessment_cfg.get("rule_dict", {})

    ref = _build_signal_ref(recording, signal_column, sampling_rate)
    arr = resolve_signal_array(ref)

    windows = _split_windows(arr, sampling_rate, window_s, overlap_s)
    job.total_segments = len(windows)
    job.processed_segments = 0
    db.add(job)
    await db.flush()

    step = 0
    for seg_idx, (start_s, end_s, start_t, end_t) in enumerate(windows):
        t0 = time.monotonic()
        chunk = arr[start_s:end_s]
        sqi_results: list[dict] = []

        for metric in metrics:
            value = _compute_metric(chunk, metric)
            rule = rule_dict.get(metric, {})
            passed = _check_threshold(value, rule)
            sqi_results.append({
                "metric_name": metric,
                "metric_value": value,
                "passed": passed,
            })

        classification, quality_score = classify_segment(sqi_results, rule_dict)

        sqi_summary = {r["metric_name"]: r["metric_value"] for r in sqi_results}

        segment = Segment(
            assessment_job_id=job.id,
            recording_id=recording.id,
            segment_number=seg_idx,
            start_time=start_t,
            end_time=end_t,
            duration=end_t - start_t,
            classification=classification,
            quality_score=quality_score,
            sqi_summary=sqi_summary,
            created_by=job.created_by,
        )
        db.add(segment)
        await db.flush()

        for sqi_r in sqi_results:
            metric_name = sqi_r["metric_name"]
            # Determine metric_category for DB constraint compliance
            category = _metric_category(metric_name)
            sqi_row = SqiResult(
                segment_id=segment.id,
                metric_name=metric_name,
                metric_category=category,
                metric_value=sqi_r["metric_value"],
                threshold_min=rule_dict.get(metric_name, {}).get("min"),
                threshold_max=rule_dict.get(metric_name, {}).get("max"),
                passed=sqi_r["passed"],
                created_by=job.created_by,
            )
            db.add(sqi_row)

        await db.flush()

        duration_ms = int((time.monotonic() - t0) * 1000)
        step += 1
        try:
            await agent_log_service.persist_log(
                db=db,
                assessment_job_id=job.id,
                recording_id=recording.id,
                step_number=step,
                stage="assessing",
                tool_called="compute_sqi",
                input_params={"segment_number": seg_idx, "metrics": metrics},
                output_summary=(
                    f"seg={seg_idx} class={classification} score={quality_score:.3f}"
                ),
                reasoning=None,
                duration_ms=duration_ms,
                status="success",
                error_detail=None,
                created_by=job.created_by,
            )
        except Exception:  # noqa: BLE001
            pass  # Log failure must not abort pipeline

        job.processed_segments = seg_idx + 1
        if job.total_segments and job.total_segments > 0:
            job.progress_pct = round(job.processed_segments / job.total_segments * 100, 2)
        db.add(job)
        await db.flush()


def _metric_category(metric_name: str) -> str:
    """Map metric name to allowed metric_category value for SqiResult."""
    _MAP = {
        "snr": "signal_processing",
        "kurtosis": "statistical",
        "skewness": "statistical",
        "zero_crossing_rate": "signal_processing",
        "perfusion_index": "clinical",
        "sdnn": "hrv_time",
        "rmssd": "hrv_time",
        "pnn50": "hrv_time",
        "mean_rr": "hrv_time",
    }
    return _MAP.get(metric_name, "statistical")
