"""AgentOrchestrator: wraps smolagents ToolCallingAgent with Ollama LLM backend.

LLM failure must never propagate — callers receive a fallback dict on any error.
Raw waveform arrays are never passed to the LLM; only summary statistics.
"""

from __future__ import annotations

import json
from pathlib import Path

# Graceful smolagents import
try:
    from smolagents import LiteLLMModel, ToolCallingAgent
    _SMOLAGENTS_AVAILABLE = True
except ImportError:
    _SMOLAGENTS_AVAILABLE = False

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

_FALLBACK_RESPONSE = {
    "interpretation": "Fallback: deterministic classification applied.",
    "recommendations": [],
    "confidence": 0.0,
}

_PROMPT_PATH = Path(__file__).parent / "prompts" / "assessment_system_prompt.md"
_CHAT_PROMPT_PATH = Path(__file__).parent / "prompts" / "chat_system_prompt.md"


def _load_system_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return "You are a signal quality assessment assistant. Return JSON only."


def _load_chat_system_prompt() -> str:
    try:
        return _CHAT_PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return "You are a signal quality assistant. Answer only from provided context."


class OllamaHealthChecker:
    """Check Ollama availability with a lightweight HTTP probe."""

    @staticmethod
    async def is_available(url: str) -> bool:
        """Return True if Ollama responds at GET {url}/api/tags within 5 s."""
        if not _HTTPX_AVAILABLE:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/api/tags")
                return response.status_code == 200
        except Exception:  # noqa: BLE001
            return False


class AgentOrchestrator:
    """Orchestrates LLM-based interpretation of deterministic assessment results."""

    def __init__(self, settings) -> None:
        self._settings = settings
        self._system_prompt = _load_system_prompt()
        self._agent = None
        if _SMOLAGENTS_AVAILABLE:
            try:
                from app.agent.tool_registry import build_tool_registry
                tools = build_tool_registry()
                model = LiteLLMModel(
                    model_id=f"ollama/{settings.ollama_model}",
                    api_base=settings.ollama_base_url,
                )
                self._agent = ToolCallingAgent(
                    tools=tools,
                    model=model,
                    max_steps=20,
                    system_prompt=self._system_prompt,
                )
            except Exception:  # noqa: BLE001
                self._agent = None

    async def chat(self, context: dict, user_message: str) -> str:
        """Generate a grounded chat response from context and user question.

        Falls back to deterministic templates when Ollama is unavailable.
        Never fabricates metric values — all data comes from context.
        """
        if not _HTTPX_AVAILABLE:
            return _build_chat_fallback(context, user_message)

        chat_system_prompt = _load_chat_system_prompt()
        context_text = _build_context_text(context)
        full_prompt = (
            f"{chat_system_prompt}\n\n"
            f"## Recording Context\n{context_text}\n\n"
            f"## User Question\n{user_message}"
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._settings.ollama_base_url}/api/generate",
                    json={
                        "model": self._settings.ollama_model,
                        "prompt": full_prompt,
                        "stream": False,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    return str(data.get("response", "")).strip() or _build_chat_fallback(context, user_message)
        except Exception:  # noqa: BLE001
            pass

        return _build_chat_fallback(context, user_message)

    async def interpret_assessment(
        self,
        job_summary: dict,
        segment_summaries: list[dict],
    ) -> dict:
        """Request LLM interpretation of assessment results.

        Args:
            job_summary: {recording_id, total_segments, accepted, rejected, metrics_summary}
            segment_summaries: list of {segment_id, segment_number, classification, failed_metrics}
                               — NO raw arrays allowed

        Returns:
            {"interpretation": str, "recommendations": list[str], "confidence": float}
        """
        if self._agent is None:
            return _FALLBACK_RESPONSE

        prompt = _build_prompt(job_summary, segment_summaries)
        try:
            raw_output = self._agent.run(prompt)
            return _parse_llm_output(raw_output)
        except Exception:  # noqa: BLE001
            return _FALLBACK_RESPONSE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_context_text(context: dict) -> str:
    """Serialize grounding context to a concise text block — no raw arrays."""
    rec = context.get("recording") or {}
    job = context.get("job_summary") or {}
    segments = context.get("segments", [])
    failed_counts = context.get("failed_metric_counts", {})
    has_overrides = context.get("has_overrides", False)
    report_title = context.get("report_title")

    lines = [
        f"Recording: {rec.get('filename', 'unknown')} | type={rec.get('signal_type')} | "
        f"fs={rec.get('sampling_rate')} Hz | duration={rec.get('duration_seconds')}s | "
        f"status={rec.get('status')}",
    ]
    if report_title:
        lines.append(f"Report: {report_title}")
    if job:
        lines.append(
            f"Assessment: status={job.get('status')} | total={job.get('total_segments')} | "
            f"accepted={job.get('accepted')} | rejected={job.get('rejected')} | "
            f"uncomputable={job.get('uncomputable')} | "
            f"acceptance_rate={job.get('acceptance_rate_pct')}% | verdict={job.get('verdict')}"
        )
    if has_overrides:
        lines.append("Note: Some segments have practitioner overrides that differ from AI classification.")
    if failed_counts:
        top = sorted(failed_counts.items(), key=lambda x: -x[1])[:5]
        lines.append("Top failed metrics: " + ", ".join(f"{m}={c}" for m, c in top))
    if segments:
        lines.append(f"Segments ({min(len(segments), 10)} of {len(segments)} shown):")
        for seg in segments[:10]:
            fm = ", ".join(seg.get("failed_metrics", [])) or "none"
            lines.append(
                f"  seg {seg['segment_number']}: ai={seg['ai_classification']} "
                f"effective={seg['effective_classification']} score={seg.get('quality_score')} "
                f"failed=[{fm}]"
            )
    return "\n".join(lines)


def _build_chat_fallback(context: dict, user_message: str) -> str:
    """Return a deterministic response template when LLM is unavailable."""
    job = context.get("job_summary") or {}
    msg_lower = user_message.lower()

    if not job:
        return "No assessment data is available for this recording yet."

    total = job.get("total_segments", 0)
    accepted = job.get("accepted", 0)
    rejected = job.get("rejected", 0)
    rate = job.get("acceptance_rate_pct", 0.0)
    verdict = job.get("verdict", "unknown")

    if "why" in msg_lower and "reject" in msg_lower:
        failed_counts = context.get("failed_metric_counts", {})
        if failed_counts:
            top = sorted(failed_counts.items(), key=lambda x: -x[1])[:5]
            metric_list = ", ".join(f"{m} ({c} segment(s))" for m, c in top)
            return (
                f"Segments were rejected due to failed quality metrics. "
                f"Most common failures: {metric_list}."
            )
        return f"Segments were rejected because they failed one or more SQI thresholds."

    if "accept" in msg_lower or "quality" in msg_lower:
        return (
            f"The recording has an acceptance rate of {rate}%. "
            f"{accepted} of {total} segments were accepted. "
            f"Overall verdict: {verdict}."
        )

    return (
        f"Based on the assessment, verdict is '{verdict}'. "
        f"{accepted}/{total} segments were accepted ({rate}% acceptance rate). "
        f"{rejected} segments were rejected."
    )


def _build_prompt(job_summary: dict, segment_summaries: list[dict]) -> str:
    """Build a concise prompt string from summary dicts — no raw arrays."""
    return (
        "Analyze the following signal quality assessment results and return JSON.\n\n"
        f"Job summary:\n{json.dumps(job_summary, indent=2)}\n\n"
        f"Segment summaries (first 20):\n"
        f"{json.dumps(segment_summaries[:20], indent=2)}\n\n"
        'Return JSON matching: {"interpretation": str, "recommendations": [str], "confidence": 0.0-1.0}'
    )


def _parse_llm_output(raw: str | dict) -> dict:
    """Parse LLM output to the expected response schema."""
    if isinstance(raw, dict):
        candidate = raw
    else:
        try:
            # Extract JSON block if wrapped in markdown code fences
            text = str(raw)
            start = text.find("{")
            end = text.rfind("}") + 1
            candidate = json.loads(text[start:end]) if start >= 0 else {}
        except Exception:  # noqa: BLE001
            return _FALLBACK_RESPONSE

    return {
        "interpretation": str(candidate.get("interpretation", _FALLBACK_RESPONSE["interpretation"])),
        "recommendations": list(candidate.get("recommendations", [])),
        "confidence": float(candidate.get("confidence", 0.0)),
    }
