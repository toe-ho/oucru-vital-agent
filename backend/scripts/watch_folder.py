"""
scripts/watch_folder.py

Continuous folder watcher — automatically triggers the agent
whenever a new signal file appears in data/raw/.

Usage (from vital-agent/backend/):
  python -m scripts.watch_folder
  python -m scripts.watch_folder --task ecg_plan --interval 10
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Allow running as a standalone script from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))


PROCESSED_LOG = Path("data/.processed_files.json")


def load_processed() -> set:
    if PROCESSED_LOG.exists():
        with open(PROCESSED_LOG) as f:
            return set(json.load(f))
    return set()


def save_processed(processed: set):
    PROCESSED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_LOG, "w") as f:
        json.dump(list(processed), f)


def file_fingerprint(path: Path) -> str:
    return f"{path}:{path.stat().st_mtime}"


def process_file(file_path: Path, task: str, mode: str, config: str):
    prompt = (
        f"Analyze the physiological signal in '{file_path}'. "
        f"Load it, assess signal quality, extract all available features, "
        f"check clinical thresholds, and produce a structured report."
    )

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New file: {file_path.name}")

    try:
        if mode == "smolagents":
            from app.agent.core import run_with_smolagents
            result = run_with_smolagents(prompt, task, config)
        else:
            from app.agent.core import OllamaAgent
            agent = OllamaAgent(config)
            result = agent.run(prompt, task)

        out_dir = Path("data/processed")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{file_path.stem}_result.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"  → Result saved: {out_path}")

        flags = result.get("flags", [])
        if flags:
            print(f"  Warning Flags: {', '.join(str(f) for f in flags)}")
        else:
            print(f"  No clinical flags.")

    except Exception as e:
        print(f"  Error processing {file_path.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="vital-agent folder watcher")
    parser.add_argument("--watch_dir", default="data/raw")
    parser.add_argument("--task", default="ppg_plan")
    parser.add_argument("--mode", choices=["smolagents", "raw"], default="smolagents")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds.")
    parser.add_argument(
        "--extensions",
        default=".csv,.parquet,.edf",
        help="Comma-separated file extensions to watch.",
    )
    args = parser.parse_args()

    watch_dir = Path(args.watch_dir)
    watch_dir.mkdir(parents=True, exist_ok=True)
    extensions = set(args.extensions.split(","))
    processed = load_processed()

    print(f"[vital-agent watcher]")
    print(f"  Watching : {watch_dir.resolve()}")
    print(f"  Task     : {args.task}")
    print(f"  Interval : {args.interval}s")
    print(f"  Formats  : {extensions}")
    print(f"\nWaiting for new files... (Ctrl+C to stop)\n")

    try:
        while True:
            for path in sorted(watch_dir.iterdir()):
                if path.suffix not in extensions:
                    continue
                fp = file_fingerprint(path)
                if fp not in processed:
                    process_file(path, args.task, args.mode, args.config)
                    processed.add(fp)
                    save_processed(processed)

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[Watcher stopped]")


if __name__ == "__main__":
    main()
