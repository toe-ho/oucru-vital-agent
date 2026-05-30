"""HTML and PDF rendering utilities for assessment reports."""

from __future__ import annotations


def render_html(content_json: dict, is_stale: bool = False) -> str:
    """Render a report content_json dict into a readable HTML string."""
    stale_banner = (
        '<div class="stale-banner" style="background:#fff3cd;border:1px solid #ffc107;'
        'padding:10px;margin-bottom:16px;">'
        "<strong>Warning:</strong> This report may be out of date. "
        "Segment overrides have been applied since it was generated."
        "</div>"
        if is_stale
        else ""
    )

    summary = content_json.get("summary", {})
    segments = content_json.get("segments", [])
    agent_interp = content_json.get("agent_interpretation") or {}
    limitations = content_json.get("limitations", [])

    # --- Summary section ---
    summary_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in summary.items()
    )
    summary_html = f"""
    <h2>Summary</h2>
    <table border="1" cellpadding="4" cellspacing="0">
      <tr><th>Metric</th><th>Value</th></tr>
      {summary_rows}
    </table>"""

    # --- Segments section ---
    seg_rows = ""
    for seg in segments:
        failed = ", ".join(seg.get("failed_metrics", []))
        seg_rows += (
            f"<tr><td>{seg.get('segment_number','')}</td>"
            f"<td>{seg.get('start_time','')}</td>"
            f"<td>{seg.get('end_time','')}</td>"
            f"<td>{seg.get('classification','')}</td>"
            f"<td>{seg.get('quality_score','')}</td>"
            f"<td>{failed}</td></tr>"
        )
    segments_html = f"""
    <h2>Segments</h2>
    <table border="1" cellpadding="4" cellspacing="0">
      <tr>
        <th>#</th><th>Start</th><th>End</th>
        <th>Classification</th><th>Quality Score</th><th>Failed Metrics</th>
      </tr>
      {seg_rows}
    </table>"""

    # --- Agent interpretation section ---
    interp_html = ""
    if agent_interp:
        interp_html = f"""
    <h2>Agent Interpretation</h2>
    <p><strong>Interpretation:</strong> {agent_interp.get("interpretation","")}</p>
    <p><strong>Recommendations:</strong> {agent_interp.get("recommendations","")}</p>
    <p><strong>Confidence:</strong> {agent_interp.get("confidence","")}</p>"""

    # --- Limitations section ---
    limit_items = "".join(f"<li>{lim}</li>" for lim in limitations)
    limits_html = f"<h2>Limitations</h2><ul>{limit_items}</ul>" if limitations else ""

    recording_id = content_json.get("recording_id", "")
    job_id = content_json.get("assessment_job_id", "")
    generated_at = content_json.get("generated_at", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Assessment Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #333; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 16px; }}
    th {{ background: #f2f2f2; }}
    h1 {{ color: #1a1a2e; }}
    h2 {{ color: #16213e; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
  </style>
</head>
<body>
  {stale_banner}
  <h1>OUCRU Vital Agent — Assessment Report</h1>
  <p><strong>Recording ID:</strong> {recording_id}</p>
  <p><strong>Assessment Job:</strong> {job_id}</p>
  <p><strong>Generated At:</strong> {generated_at}</p>
  {summary_html}
  {segments_html}
  {interp_html}
  {limits_html}
</body>
</html>"""


def render_pdf(html: str, output_path: str) -> bool:
    """Render HTML to PDF using WeasyPrint. Returns True on success."""
    try:
        import weasyprint  # type: ignore

        weasyprint.HTML(string=html).write_pdf(output_path)
        return True
    except Exception:  # noqa: BLE001
        return False
