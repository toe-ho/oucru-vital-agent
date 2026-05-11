"""
app/agent/core.py

Two agent modes for running signal analysis:
  1. smolagents CodeAgent  — LLM writes Python code to call tools (recommended)
  2. OllamaAgent raw loop  — manual JSON tool-call parsing (more control, no framework)

Ported from the original standalone agent/core.py; imports updated to app.tools.*.
"""

from __future__ import annotations

import json
import os
import yaml
import requests
from pathlib import Path
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Config + task plan loaders
# ---------------------------------------------------------------------------

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_task_plan(task_name: str, tasks_dir: str | None = None) -> dict:
    """Load a task plan YAML by name (e.g. 'ppg_plan', 'ecg_plan')."""
    if tasks_dir is None:
        tasks_dir = Path(__file__).parent / "task_plans"
    path = Path(tasks_dir) / f"{task_name}.yaml"
    if not path.exists():
        available = [p.stem for p in Path(tasks_dir).glob("*.yaml")]
        raise FileNotFoundError(
            f"Task plan '{task_name}' not found at {path}. Available: {available}"
        )
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def build_system_prompt(task_plan: dict, config: dict) -> str:
    plan_yaml = yaml.dump(task_plan, default_flow_style=False, allow_unicode=True)
    return f"""You are a clinical wearable data analysis agent.
You have access to Python tools for signal processing and quality assessment.

## Your task plan
```yaml
{plan_yaml}
```

## Behavior rules
1. Always check signal quality (SQI) before running heavy analysis.
2. If SQI < {config.get('thresholds', {}).get('sqi_min', 0.5)}, still attempt analysis
   but mark confidence as "low" in the final report.
3. Use the tool that matches each step. Do not skip steps unless a condition
   specified in the task plan is not met.
4. If a tool raises an error, report it and try an alternative or mark the step failed.
5. Always produce a final structured JSON report matching the task plan output_schema.
6. Be concise — do not explain what you are doing, just do it and report results.

## Datetime
{datetime.now().isoformat()}

## Thresholds (from config)
{yaml.dump(config.get('thresholds', {}), default_flow_style=True)}
"""


# ---------------------------------------------------------------------------
# Mode 1: smolagents CodeAgent
# ---------------------------------------------------------------------------

def run_with_smolagents(
    prompt: str,
    task_name: str,
    config_path: str = "config.yaml",
) -> dict:
    """Run the agent using smolagents CodeAgent with all 8 registered tools."""
    from smolagents import CodeAgent, OllamaModel
    from app.tools.signal_loader import load_signal_file
    from app.tools.ppg_tools import preprocess_ppg, extract_ppg_dc_layer
    from app.tools.hrv_tools import extract_hrv_features
    from app.tools.spo2_tools import estimate_spo2
    from app.tools.threshold_tools import check_clinical_thresholds
    from app.tools.sqi_tools import compute_sqi, compute_sqi_windowed

    cfg = load_config(config_path)
    task_plan = load_task_plan(task_name)
    system_prompt = build_system_prompt(task_plan, cfg)

    llm_cfg = cfg["llm"]
    model = OllamaModel(model_id=llm_cfg["model"], url=llm_cfg["base_url"])

    tools = [
        load_signal_file,
        preprocess_ppg,
        extract_ppg_dc_layer,
        extract_hrv_features,
        estimate_spo2,
        check_clinical_thresholds,
        compute_sqi,
        compute_sqi_windowed,
    ]

    agent = CodeAgent(
        tools=tools,
        model=model,
        system_prompt=system_prompt,
        max_steps=cfg["agent"]["max_steps"],
        verbose=cfg["agent"]["verbose"],
    )
    return agent.run(prompt)


# ---------------------------------------------------------------------------
# Mode 2: Raw Ollama loop (no framework dependency)
# ---------------------------------------------------------------------------

class OllamaAgent:
    """
    Minimal agent loop using Ollama's /api/chat endpoint directly.
    Supports Ollama's native tool-calling format (Qwen3, Llama3).
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.cfg = load_config(config_path)
        llm = self.cfg["llm"]
        self.model = llm["model"]
        self.base_url = llm["base_url"].rstrip("/")
        self.max_steps = self.cfg["agent"]["max_steps"]
        self.verbose = self.cfg["agent"]["verbose"]
        self._tools = self._load_tools()

    def _load_tools(self) -> dict:
        from app.tools.signal_loader import load_signal_file
        from app.tools.ppg_tools import preprocess_ppg, extract_ppg_dc_layer
        from app.tools.hrv_tools import extract_hrv_features
        from app.tools.spo2_tools import estimate_spo2
        from app.tools.threshold_tools import check_clinical_thresholds
        from app.tools.sqi_tools import compute_sqi, compute_sqi_windowed

        return {
            "load_signal_file": load_signal_file,
            "preprocess_ppg": preprocess_ppg,
            "extract_ppg_dc_layer": extract_ppg_dc_layer,
            "extract_hrv_features": extract_hrv_features,
            "estimate_spo2": estimate_spo2,
            "check_clinical_thresholds": check_clinical_thresholds,
            "compute_sqi": compute_sqi,
            "compute_sqi_windowed": compute_sqi_windowed,
        }

    def _tool_schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "load_signal_file",
                    "description": "Load a physiological signal from CSV, Parquet, or WFDB.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "column": {"type": "string", "default": "ppg"},
                            "fs": {"type": "integer", "default": 100},
                        },
                        "required": ["file_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "compute_sqi",
                    "description": "Compute Signal Quality Index (0–1) for PPG or ECG.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "signal": {"type": "array", "items": {"type": "number"}},
                            "fs": {"type": "integer", "default": 100},
                            "signal_type": {"type": "string", "default": "ppg"},
                        },
                        "required": ["signal"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "compute_sqi_windowed",
                    "description": "Compute SQI over sliding windows of a long signal.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "signal": {"type": "array", "items": {"type": "number"}},
                            "fs": {"type": "integer", "default": 100},
                            "signal_type": {"type": "string", "default": "ppg"},
                            "window_sec": {"type": "integer", "default": 30},
                            "step_sec": {"type": "integer"},
                        },
                        "required": ["signal"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "preprocess_ppg",
                    "description": "Filter, normalize and detect peaks in a PPG signal.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "signal": {"type": "array", "items": {"type": "number"}},
                            "fs": {"type": "integer", "default": 100},
                        },
                        "required": ["signal"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_hrv_features",
                    "description": "Extract time and frequency domain HRV features.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rr_intervals_ms": {"type": "array", "items": {"type": "number"}},
                            "fs": {"type": "integer", "default": 100},
                        },
                        "required": ["rr_intervals_ms"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "estimate_spo2",
                    "description": "Estimate SpO2 from red and infrared PPG channels.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "red_signal": {"type": "array", "items": {"type": "number"}},
                            "ir_signal": {"type": "array", "items": {"type": "number"}},
                            "fs": {"type": "integer", "default": 100},
                        },
                        "required": ["red_signal", "ir_signal"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_clinical_thresholds",
                    "description": "Flag HR, SpO2, or SQI values outside clinical thresholds.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "heart_rate_bpm": {"type": "number"},
                            "spo2_pct": {"type": "number"},
                            "sqi_score": {"type": "number"},
                        },
                    },
                },
            },
        ]

    def _call_ollama(self, messages: list[dict]) -> dict:
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "tools": self._tool_schemas(),
                "stream": False,
                "options": {
                    "temperature": self.cfg["llm"]["temperature"],
                    "num_predict": self.cfg["llm"]["max_tokens"],
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def _execute_tool(self, name: str, args: dict) -> Any:
        if name not in self._tools:
            return {"error": f"Unknown tool: {name}"}
        try:
            return self._tools[name](**args)
        except Exception as e:
            return {"error": str(e), "tool": name, "args": args}

    def run(self, prompt: str, task_name: str) -> dict:
        task_plan = load_task_plan(task_name)
        system_prompt = build_system_prompt(task_plan, self.cfg)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        for step in range(self.max_steps):
            if self.verbose:
                print(f"\n[Agent step {step + 1}/{self.max_steps}]")

            response = self._call_ollama(messages)
            msg = response.get("message", {})
            tool_calls = msg.get("tool_calls", [])

            if not tool_calls:
                final_text = msg.get("content", "")
                if self.verbose:
                    print(f"[Done] {final_text[:200]}")
                try:
                    return json.loads(final_text)
                except Exception:
                    return {"result": final_text, "raw": True}

            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})

            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    args = json.loads(args)

                if self.verbose:
                    print(f"  → tool: {name}({list(args.keys())})")

                result = self._execute_tool(name, args)

                if self.verbose and "error" not in result:
                    print(f"  ← {json.dumps(result)[:150]}...")

                messages.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "name": name,
                })

        return {"error": f"Agent reached max_steps ({self.max_steps}) without finishing."}
