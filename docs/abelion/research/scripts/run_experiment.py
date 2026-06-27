#!/usr/bin/env python3
"""Run the RSI effectiveness experiment (3 conditions, 20 tasks, multiple runs).

Usage:
    python3 run_experiment.py --api-key KEY [--model MODEL] [--runs 3]
"""

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure we can import from project root (walk up until we find run_agent.py)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
while not (PROJECT_ROOT / "run_agent.py").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent
    if PROJECT_ROOT == PROJECT_ROOT.parent:
        raise RuntimeError("Could not find project root (run_agent.py)")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from run_agent import AIAgent
from tasks import get_task_batch
from rsi_extractor import extract_lesson_candidates
from rsi_validator import validate_lesson


CONDITIONS = {
    "A": {"name": "control", "rsi": False, "validated": False},
    "B": {"name": "raw_rsi", "rsi": True, "validated": False},
    "C": {"name": "validated_rsi", "rsi": True, "validated": True},
}


def create_agent(api_key: str, model: str, max_iterations: int = 10,
                 base_url: str = None, provider: str = None) -> AIAgent:
    """Create a fresh AIAgent instance for a single run."""
    return AIAgent(
        api_key=api_key,
        base_url=base_url or "https://openrouter.ai/api/v1",
        provider=provider or "openrouter",
        model=model,
        max_iterations=max_iterations,
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
        enabled_toolsets=["terminal", "file", "web", "search"],
    )


def run_single_task(agent: AIAgent, task) -> dict:
    """Run a single benchmark task and return metrics + message history."""
    start_time = time.time()
    try:
        conversation = agent.run_conversation(task.prompt)
        elapsed = time.time() - start_time

        return {
            "metrics": {
                "task_id": task.id,
                "category": task.category,
                "completed": conversation.get("completed", False),
                "failed": conversation.get("failed", False),
                "error": conversation.get("error", "") or "",
                "iterations": conversation.get("api_calls", 0),
                "total_tokens": conversation.get("total_tokens", 0),
                "input_tokens": conversation.get("input_tokens", 0),
                "output_tokens": conversation.get("output_tokens", 0),
                "cost_usd": conversation.get("estimated_cost_usd", 0.0),
                "response": (conversation.get("final_response") or "")[:200],
                "elapsed_seconds": round(elapsed, 2),
            },
            "messages": list(conversation.get("messages", [])),
        }
    except Exception as e:
        return {
            "metrics": {
                "task_id": task.id,
                "category": task.category,
                "completed": False,
                "failed": True,
                "error": str(e),
                "iterations": 0,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "response": "",
                "elapsed_seconds": round(time.time() - start_time, 2),
            },
            "messages": [],
        }


def run_condition(
    condition_id: str,
    config: dict,
    tasks: list,
    api_key: str,
    model: str,
    run_number: int,
    base_url: str = None,
    provider: str = None,
    max_iterations: int = 10,
    global_task_count: int = 0,
) -> tuple[list[dict], list[dict]]:
    """Run all tasks under one condition for one run.

    Returns (results, injected_lessons).
    """
    print(f"  Condition {condition_id} ({config['name']}) — run {run_number}")
    agent = create_agent(api_key, model, max_iterations=max_iterations,
                         base_url=base_url, provider=provider)
    random.shuffle(tasks)
    injected_lessons: list[dict] = []
    results: list[dict] = []

    for task in tasks:
        print(f"    Task {task.id}...", end=" ")
        sys.stdout.flush()

        execution = run_single_task(agent, task)
        result = execution["metrics"]
        result["condition"] = condition_id
        result["condition_name"] = config["name"]
        result["run"] = run_number
        results.append(result)

        # Live status update per-task
        _update_status(
            f"running ({len(results)}/{global_task_count})",
            condition=condition_id,
            run=run_number,
            task_id=task.id,
            ok=result["completed"] and not result["failed"],
            tokens=int(result["total_tokens"]),
            iterations=int(result["iterations"]),
        )

        if config["rsi"] and not result["failed"]:
            # Extract lesson candidates from the same conversation
            candidates = extract_lesson_candidates(execution["messages"])

            if config["validated"]:
                for candidate in candidates:
                    validation = validate_lesson(candidate, injected_lessons)
                    if validation["is_valid"]:
                        injected_lessons.append(candidate)
                        print("+", end="")
            else:
                injected_lessons.extend(candidates)
                if candidates:
                    print(f"+{len(candidates)}", end="")

        status = "OK" if result["completed"] and not result["failed"] else "FAIL"
        print(f" {status} ({result['iterations']} calls, {result['total_tokens']} tokens)")

    return results, injected_lessons


# ── Live status (realtime transparency) ───────────────────────────────

_status_cache = {"status": "", "progress": 0, "total": 0, "conditions": {}, "latest": ""}
_status_path: Path | None = None


def _write_status(status_path: Path, data: dict) -> None:
    """Write live status JSON — user can `cat` this anytime."""
    try:
        with open(status_path, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def _update_status(
    status: str,
    condition: str = "",
    run: int = 0,
    task_id: str = "",
    ok: bool = False,
    tokens: int = 0,
    iterations: int = 0,
) -> None:
    global _status_cache, _status_path
    sc = _status_cache
    sc["status"] = status
    if condition:
        key = f"{condition}_run{run}"
        if key not in sc["conditions"]:
            sc["conditions"][key] = {"total": 0, "ok": 0}
        sc["conditions"][key]["total"] += 1
        if ok:
            sc["conditions"][key]["ok"] += 1
    if task_id:
        sc["latest"] = f"{task_id}: {'OK' if ok else 'FAIL'} ({iterations} calls, {tokens} tokens)"
    if _status_path:
        _write_status(_status_path, sc)


def main():
    parser = argparse.ArgumentParser(description="Run RSI experiment")
    parser.add_argument("--api-key", required=True, help="API key")
    parser.add_argument("--model", default="anthropic/claude-sonnet-4", help="Model name")
    parser.add_argument("--base-url", help="API base URL (default: OpenRouter)")
    parser.add_argument("--provider", help="Provider name (default: openrouter)")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per condition")
    parser.add_argument("--output", default="", help="Output CSV path")
    parser.add_argument("--conditions", default="A,B,C", help="Conditions to run (comma-separated)")
    parser.add_argument("--tasks", default="standard",
                        help="Task set: 'standard' (from tasks) or 'hard' (from tasks_hard)")
    parser.add_argument("--max-iterations", type=int, default=10,
                        help="Max iterations per task (default 10)")
    args = parser.parse_args()

    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or Path("data") / f"experiment_{timestamp}.csv"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Live status file — updated every task, readable anytime
    status_path = output_path.with_suffix(".status.json")
    _write_status(status_path, {"status": "starting", "progress": 0, "total": 0, "conditions": {}, "latest": ""})
    _status_path = status_path

    fieldnames = [
        "task_id", "category", "condition", "condition_name", "run",
        "completed", "failed", "error",
        "iterations", "total_tokens", "input_tokens", "output_tokens",
        "cost_usd", "elapsed_seconds", "response",
    ]

    tasks = get_task_batch()
    condition_ids = args.conditions.split(",")
    total_tasks = len(tasks) * len(condition_ids) * args.runs

    # Switch task sets
    if args.tasks == "hard":
        from tasks_hard import get_task_batch as get_hard
        tasks = get_hard()
        print(f"[Using hard task set: {len(tasks)} tasks]")
    
    print(f"RSI Experiment — {len(tasks)} tasks, {len(condition_ids)} conditions, {args.runs} runs")
    print(f"Model: {args.model}")
    print(f"Output: {output_path}")
    print()

    print("[WARNING] This will make real API calls and cost money.")
    print(f"  Estimated conversations: {len(tasks) * len(condition_ids) * args.runs}")
    confirm = input("Proceed? (y/N): ")
    if confirm.lower() != "y":
        print("Aborted.")
        return

    total_start = time.time()
    all_lessons: dict[str, list[dict]] = {}
    task_number = 0

    with open(output_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for run in range(1, args.runs + 1):
            print(f"\n=== Run {run}/{args.runs} ===")
            for cid in condition_ids:
                config = CONDITIONS[cid]
                _update_status(f"running ({task_number}/{total_tasks})", condition=cid, run=run)
                results, lessons = run_condition(
                    cid, config, tasks, args.api_key, args.model, run,
                    base_url=args.base_url, provider=args.provider,
                    max_iterations=args.max_iterations,
                    global_task_count=total_tasks,
                )
                all_lessons[f"{cid}_run{run}"] = lessons
                for row in results:
                    writer.writerow(row)
                    task_number += 1
                csv_file.flush()

    total_elapsed = time.time() - total_start
    print(f"\n=== Done in {total_elapsed:.0f}s ===")
    print(f"Results saved to: {output_path}")

    lessons_path = output_path.with_suffix(".lessons.json")
    import json
    with open(lessons_path, "w") as f:
        json.dump(all_lessons, f, indent=2, default=str)
    print(f"Lessons saved to: {lessons_path}")


if __name__ == "__main__":
    main()
