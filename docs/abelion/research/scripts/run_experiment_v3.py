#!/usr/bin/env python3
"""Run the RSI effectiveness experiment (3 conditions, 20 tasks, multiple runs).

v3 changes:
- Uses rsi_extractor v2 (actionable heuristic synthesis)
- Uses rsl_memory_store (SQLite persistence, confidence tracking)
- Uses rsl_injector (smart lesson selection + compression)
- FEEDBACK LOOP: lesson confidence updated after each task outcome
- Cache-aware: injects at start of each condition, not inline

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
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

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


def _setup_store(persona_id: str = "rsi_exp_v3") -> Any:
    """Set up MemoryStore with temp directory for experiment isolation."""
    from rsl_memory_store import MemoryStore
    store = MemoryStore(persona_id)
    return store


def _extract_and_store(
    messages: list[dict],
    store: Any,
    validated: bool,
) -> list[dict]:
    """Extract lessons, optionally validate, store in DB. Returns new lessons."""
    from rsi_extractor import extract_lesson_candidates
    from rsl_validator import validate_and_store

    candidates = extract_lesson_candidates(messages)

    new_lessons = []
    for cand in candidates:
        if validated:
            result = validate_and_store(cand, store)
            if result.get("stored"):
                new_lessons.append(result)
        else:
            # Store directly (raw RSI)
            from rsl_memory_store import lesson_from_candidate
            lesson_data = lesson_from_candidate(cand)
            lid = store.store_lesson(lesson_data)
            new_lessons.append({"lesson_id": lid, "confidence": cand.get("confidence", 0.5)})

    return new_lessons


def _inject_lessons(agent: AIAgent, store: Any, injector: Any) -> None:
    """Inject top lessons from store into the agent's conversation."""
    all_lessons = store.get_all_active()
    if not all_lessons:
        return

    selected = injector.select_lessons(all_lessons)
    if not selected:
        return

    # Compress: merge similar triggers
    compressed = injector.compress(selected)

    injection_text = injector.format_injection_prompt(compressed)
    if not injection_text:
        return

    try:
        if hasattr(agent, '_system_message') and agent._system_message:
            existing = agent._system_message
            if isinstance(existing, str):
                agent._system_message = existing + "\n\n" + injection_text
            elif isinstance(existing, dict):
                existing['content'] = existing.get('content', '') + "\n\n" + injection_text
    except Exception:
        pass


def _update_feedback(store: Any, injected_lessons: list[dict], task_succeeded: bool) -> None:
    """Update confidence for each injected lesson based on task outcome."""
    for lesson in injected_lessons:
        lid = lesson.get("lesson_id")
        if lid:
            store.update_confidence(lid, helped=task_succeeded)


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
) -> tuple[list[dict], list[dict]]:
    """Run all tasks under one condition for one run.

    Returns (results, injected_lessons).
    """
    print(f"  Condition {condition_id} ({config['name']}) — run {run_number}")
    agent = create_agent(api_key, model, max_iterations=max_iterations,
                         base_url=base_url, provider=provider)
    random.shuffle(tasks)

    # Setup persistent store + injector if RSI is enabled
    store = None
    injector = None
    condition_lessons: list[dict] = []  # tracks which lessons were injected
    feedback_lessons: list[dict] = []  # tracks lessons for feedback loop

    if config["rsi"]:
        from rsl_memory_store import MemoryStore
        from rsl_injector import Injector
        store = MemoryStore(f"rsi_v3_{condition_id}_run{run_number}")
        injector = Injector(max_inline=5, max_tokens=1200)
        # Inject existing lessons at start
        _inject_lessons(agent, store, injector)

    results: list[dict] = []

    for task_idx, task in enumerate(tasks):
        print(f"    Task {task.id}...", end=" ")
        sys.stdout.flush()

        execution = run_single_task(agent, task)
        result = execution["metrics"]
        result["condition"] = condition_id
        result["condition_name"] = config["name"]
        result["run"] = run_number
        results.append(result)

        if config["rsi"] and store and injector:
            # Extract + store lessons from this task's conversation
            new_lessons = _extract_and_store(
                execution["messages"], store,
                validated=config["validated"],
            )

            if new_lessons:
                # Track for feedback
                feedback_lessons.extend(new_lessons)
                print(f"+{len(new_lessons)}", end="")

                # Update feedback: did the lesson help this task?
                succeeded = result["completed"] and not result["failed"]
                _update_feedback(store, new_lessons, succeeded)

            # Inject lessons before next task (if available)
            if task_idx < len(tasks) - 1:
                _inject_lessons(agent, store, injector)

        status = "OK" if result["completed"] and not result["failed"] else "FAIL"
        print(f" {status} ({result['iterations']} calls, {result['total_tokens']} tokens)")

    # Collect final lesson stats
    final_lessons = store.get_all_active() if store else []
    if store:
        store.close()

    return results, final_lessons


def main():
    parser = argparse.ArgumentParser(description="Run RSI experiment v3")
    parser.add_argument("--api-key", required=True, help="API key")
    parser.add_argument("--model", default="gc/gemini-3.1-flash-lite", help="Model name")
    parser.add_argument("--base-url", default="http://localhost:20128/v1", help="API base URL")
    parser.add_argument("--provider", default="openai", help="Provider name")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per condition")
    parser.add_argument("--output", default="", help="Output CSV path")
    parser.add_argument("--conditions", default="A,B,C", help="Conditions to run (comma-separated)")
    parser.add_argument("--tasks", default="hard",
                        help="Task set: 'standard' or 'hard'")
    parser.add_argument("--max-iterations", type=int, default=3,
                        help="Max iterations per task (default 3)")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or Path("data") / f"experiment_v3_{timestamp}.csv"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "task_id", "category", "condition", "condition_name", "run",
        "completed", "failed", "error",
        "iterations", "total_tokens", "input_tokens", "output_tokens",
        "cost_usd", "elapsed_seconds", "response",
    ]

    if args.tasks == "hard":
        from tasks_hard import get_task_batch as get_hard
        tasks = get_hard()
    else:
        from tasks import get_task_batch
        tasks = get_task_batch()

    condition_ids = args.conditions.split(",")

    print(f"RSI Experiment v3 — {len(tasks)} tasks, {len(condition_ids)} conditions, {args.runs} runs")
    print(f"Model: {args.model}")
    print(f"Max iterations: {args.max_iterations}")
    print(f"Output: {output_path}")
    print()

    print("[WARNING] This will make real API calls.")
    print(f"  Estimated conversations: {len(tasks) * len(condition_ids) * args.runs}")
    confirm = input("Proceed? (y/N): ")
    if confirm.lower() != "y":
        print("Aborted.")
        return

    total_start = time.time()
    all_lesson_data: dict[str, list[dict]] = {}

    with open(output_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for run in range(1, args.runs + 1):
            print(f"\n=== Run {run}/{args.runs} ===")
            for cid in condition_ids:
                config = CONDITIONS[cid]
                results, lessons = run_condition(
                    cid, config, tasks, args.api_key, args.model, run,
                    base_url=args.base_url, provider=args.provider,
                    max_iterations=args.max_iterations,
                )
                all_lesson_data[f"{cid}_run{run}"] = lessons
                for row in results:
                    writer.writerow(row)
                csv_file.flush()

    total_elapsed = time.time() - total_start
    print(f"\n=== Done in {total_elapsed:.0f}s ===")
    print(f"Results saved to: {output_path}")

    lessons_path = output_path.with_suffix(".lessons.json")
    with open(lessons_path, "w") as f:
        # Convert DB rows to serializable dicts
        serializable = {}
        for k, v in all_lesson_data.items():
            serializable[k] = [{kk: vv for kk, vv in l.items()} if isinstance(l, dict) else str(l) for l in v]
        json.dump(serializable, f, indent=2, default=str)
    print(f"Lessons saved to: {lessons_path}")


if __name__ == "__main__":
    main()
