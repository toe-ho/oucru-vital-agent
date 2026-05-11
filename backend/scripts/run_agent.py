"""
scripts/run_agent.py

Interactive CLI — run the agent with a prompt and task plan.

Usage (from vital-agent/backend/):
  python -m scripts.run_agent --prompt "Analyze data/raw/patient_01.csv"
  python -m scripts.run_agent --prompt "..." --task ecg_plan
  python -m scripts.run_agent --prompt "..." --task fluid_response_monitoring --mode raw
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running as a standalone script from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(description="vital-agent CLI")
    parser.add_argument("--prompt", required=True, help="Analysis request")
    parser.add_argument(
        "--task",
        default="ppg_plan",
        help="Task plan name (without .yaml). Default: ppg_plan",
    )
    parser.add_argument(
        "--mode",
        choices=["smolagents", "raw"],
        default="smolagents",
        help="Agent backend. Default: smolagents",
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument(
        "--output",
        default=None,
        help="Save result JSON to this file path",
    )
    args = parser.parse_args()

    print(f"\n[vital-agent]")
    print(f"  Task plan : {args.task}")
    print(f"  Mode      : {args.mode}")
    print(f"  Prompt    : {args.prompt}\n")

    if args.mode == "smolagents":
        from app.agent.core import run_with_smolagents
        result = run_with_smolagents(args.prompt, args.task, args.config)
    else:
        from app.agent.core import OllamaAgent
        agent = OllamaAgent(args.config)
        result = agent.run(args.prompt, args.task)

    print("\n=== RESULT ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n[Saved to {args.output}]")


if __name__ == "__main__":
    main()
