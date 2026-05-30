"""Evaluate clinical metric values against configurable threshold bounds."""

from __future__ import annotations


def evaluate_thresholds(metric_values: dict, threshold_config: dict) -> dict:
    """Check each metric in threshold_config against min/max bounds.

    Args:
        metric_values:    {"metric_name": numeric_value, ...}
        threshold_config: {"metric_name": {"min": float|None, "max": float|None}, ...}

    Returns:
        {
            "overall_pass": bool,
            "results": {
                "metric_name": {
                    "value":  float | None,
                    "passed": bool,
                    "reason": str,
                }
            }
        }
    """
    results: dict[str, dict] = {}

    for metric, bounds in threshold_config.items():
        value = metric_values.get(metric)
        lo: float | None = bounds.get("min")
        hi: float | None = bounds.get("max")

        if value is None:
            results[metric] = {"value": None, "passed": False, "reason": "metric value missing"}
            continue

        reasons: list[str] = []
        if lo is not None and value < lo:
            reasons.append(f"{value} < min({lo})")
        if hi is not None and value > hi:
            reasons.append(f"{value} > max({hi})")

        passed = len(reasons) == 0
        results[metric] = {
            "value": value,
            "passed": passed,
            "reason": "ok" if passed else "; ".join(reasons),
        }

    overall_pass = all(r["passed"] for r in results.values())
    return {"overall_pass": overall_pass, "results": results}
