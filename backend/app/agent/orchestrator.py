"""smolagents-based assessment orchestrator — runs as a FastAPI BackgroundTask."""
from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.agent.state import AgentState, transition
from app.agent.tool_registry import ALL_TOOLS
from app.config import agent_config


def _load_task_plan(signal_type: str) -> dict:
    plans_dir = Path(__file__).parent / "task_plans"
    plan_file = plans_dir / f"{signal_type}_plan.yaml"
    if not plan_file.exists():
        plan_file = plans_dir / "ppg_plan.yaml"
    with open(plan_file) as f:
        return yaml.safe_load(f)


def _load_system_prompt() -> str:
    prompt_file = Path(__file__).parent / "prompts" / "system_prompt.txt"
    with open(prompt_file) as f:
        return f.read()


def _build_task_string(state: AgentState, task_plan: dict) -> str:
    plan_yaml = yaml.dump(task_plan, default_flow_style=False, allow_unicode=True)
    return (
        f"Assess the quality of the following waveform recording:\n"
        f"- recording_id: {state['recording_id']}\n"
        f"- file_path: {state['file_path']}\n"
        f"- signal_type: {state['signal_type']}\n"
        f"- sampling_rate: {state['sampling_rate']} Hz\n"
        f"- subject_id: {state.get('subject_id', 'unknown')}\n\n"
        f"Follow this task plan:\n```yaml\n{plan_yaml}\n```\n\n"
        f"Return a JSON object matching the output schema in the system prompt."
    )


async def run_assessment(
    job_id: uuid.UUID,
    recording_id: uuid.UUID,
    file_path: str,
    signal_type: str,
    sampling_rate: int,
    subject_id: str | None = None,
) -> None:
    """
    Background task: orchestrates the full quality assessment pipeline.
    Creates its own DB session (request session closes before this runs).
    """
    from app.db.session import AsyncSessionLocal
    from app.services.assessment_service import (
        finalize_job,
        log_agent_step,
        update_job_progress,
    )

    state: AgentState = {
        "recording_id": str(recording_id),
        "file_path": file_path,
        "signal_type": signal_type,
        "sampling_rate": sampling_rate,
        "subject_id": subject_id,
        "current_stage": "initialized",
        "needs_preprocessing": False,
        "preprocessed_file_path": None,
        "assessment_result": None,
        "sqi_matrix": None,
        "flagged_segment_ids": [],
        "segment_details": {},
        "agent_interpretation": None,
        "key_findings": [],
        "recommendations": [],
        "overall_verdict": None,
        "acceptance_rate": None,
        "escalate": False,
        "escalation_reason": None,
        "report_id": None,
        "error_message": None,
        "tool_call_count": 0,
    }

    task_plan = _load_task_plan(signal_type)
    system_prompt = _load_system_prompt()
    task_string = _build_task_string(state, task_plan)

    async with AsyncSessionLocal() as db:
        await update_job_progress(job_id, 0, None, "initialized", db)

        try:
            from smolagents import CodeAgent, OllamaModel

            model = OllamaModel(
                model_id=agent_config.model,
                url=agent_config.base_url,
            )
            agent = CodeAgent(
                tools=ALL_TOOLS,
                model=model,
                system_prompt=system_prompt,
                max_steps=agent_config.max_steps,
                verbose=agent_config.verbose,
            )

            raw_result = await asyncio.wait_for(
                asyncio.to_thread(agent.run, task_string),
                timeout=agent_config.timeout_seconds,
            )

            # Parse the structured JSON verdict from the agent's final output
            if isinstance(raw_result, dict):
                verdict_data = raw_result
            else:
                text = str(raw_result)
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                if json_match:
                    verdict_data = json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse agent output as JSON: {text[:200]}")

            state = {
                **state,
                "overall_verdict": verdict_data.get("overall_verdict", "poor"),
                "acceptance_rate": verdict_data.get("acceptance_rate", 0.0),
                "key_findings": verdict_data.get("key_findings", []),
                "recommendations": verdict_data.get("recommendations", []),
                "flagged_segment_ids": [str(i) for i in verdict_data.get("flagged_segments", [])],
                "agent_interpretation": str(verdict_data.get("key_findings", "")),
                "escalate": verdict_data.get("escalate", False),
                "escalation_reason": verdict_data.get("escalation_reason"),
                "current_stage": "completed",
            }

        except asyncio.TimeoutError:
            state = {**state, "current_stage": "error", "error_message": "Assessment timed out"}
            await log_agent_step(
                job_id, {"stage": "error", "tool_called": None, "success": False,
                         "reasoning": "Pipeline timeout", "duration_ms": agent_config.timeout_seconds * 1000}, db
            )
        except Exception as e:
            # LLM failed — run deterministic fallback
            from app.agent.fallback import run_fallback_assessment
            state = run_fallback_assessment(state, task_plan)
            await log_agent_step(
                job_id, {"stage": "fallback", "tool_called": "fallback_mode", "success": True,
                         "reasoning": f"LLM failed: {e}. Using rule-based fallback.", "duration_ms": 0}, db
            )

        await finalize_job(job_id, state, db)
