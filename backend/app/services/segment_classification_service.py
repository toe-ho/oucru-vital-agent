"""Service for classifying signal segments based on SQI results and threshold rules."""

from __future__ import annotations


def classify_segment(sqi_results: list[dict], rule_dict: dict) -> tuple[str, float]:
    """Classify a segment and compute a quality score.

    Args:
        sqi_results: list of {"metric_name": str, "metric_value": float|None, "passed": bool|None}
        rule_dict: {"metric_name": {"required": bool, "min": float|None, "max": float|None}}

    Returns:
        (classification, quality_score)
        - classification: "uncomputable" | "reject" | "accept"
        - quality_score: fraction of all metrics that passed (0.0–1.0)
    """
    if not sqi_results:
        return "uncomputable", 0.0

    # Index results by metric name for fast lookup
    results_by_name: dict[str, dict] = {r["metric_name"]: r for r in sqi_results}

    required_metrics = [m for m, cfg in rule_dict.items() if cfg.get("required", False)]

    # Check for uncomputable required metrics first
    for metric in required_metrics:
        result = results_by_name.get(metric)
        if result is None or result.get("metric_value") is None:
            return "uncomputable", _compute_quality_score(sqi_results)

    # Check required metric threshold failures
    for metric in required_metrics:
        result = results_by_name.get(metric)
        if result and result.get("passed") is False:
            return "reject", _compute_quality_score(sqi_results)

    return "accept", _compute_quality_score(sqi_results)


def _compute_quality_score(sqi_results: list[dict]) -> float:
    """Compute fraction of metrics that passed (0.0–1.0)."""
    if not sqi_results:
        return 0.0
    passed_count = sum(
        1 for r in sqi_results
        if r.get("passed") is True and r.get("metric_value") is not None
    )
    return round(passed_count / len(sqi_results), 4)
