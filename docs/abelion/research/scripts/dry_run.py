#!/usr/bin/env python3
"""Dry-run experiment — verifies pipeline without API calls.

Replaces AIAgent with a mock. Ensures tasks→extractor→validator→store flow.
"""

import json
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

# ── mock AIAgent ───────────────────────────────────────────────────────
class MockAIAgent:
    def __init__(self, *a, **kw):
        self.call_count = 0
    def run_conversation(self, prompt):
        self.call_count += 1
        return {
            "completed": self.call_count % 3 != 0,  # ~66% success
            "failed": self.call_count % 5 == 0,
            "api_calls": 3,
            "total_tokens": 500,
            "input_tokens": 300,
            "output_tokens": 200,
            "estimated_cost_usd": 0.002,
            "final_response": "Done.",
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "", "tool_calls": [
                    {"id": f"call_{self.call_count}",
                     "function": {"name": "terminal", "arguments": "{}"}}
                ]},
                {"role": "tool", "tool_call_id": f"call_{self.call_count}",
                 "content": "Error: command not found. Using terminal without proper path causes failures. Use shlex.quote()."},
            ],
        }

# ── patch run_agent ────────────────────────────────────────────────────
import tasks
from rsi_extractor import extract_lesson_candidates
from rsi_validator import validate_lesson
from rsl_validator import validate_and_store
from rsl_memory_store import MemoryStore

# Override AIAgent import
sys.modules["run_agent"] = type(sys)("run_agent")
sys.modules["run_agent"].AIAgent = MockAIAgent

# ── run pipeline ───────────────────────────────────────────────────────
print("=== RSI Experiment Dry-Run ===\n")

with tempfile.TemporaryDirectory() as tmp:
    import rsl_memory_store as ms
    ms.HERMES_HOME = Path(tmp)
    store = MemoryStore("dryrun_persona")

    task_list = tasks.get_task_batch()
    print(f"Tasks loaded: {len(task_list)}")

    agent = MockAIAgent()
    results = []

    for task in task_list:
        conv = agent.run_conversation(task.prompt)
        result = {
            "task_id": task.id,
            "category": task.category,
            "completed": conv["completed"],
            "failed": conv["failed"],
            "iterations": conv["api_calls"],
            "total_tokens": conv["total_tokens"],
        }
        results.append(result)

        # RSI: extract + validate + store
        candidates = extract_lesson_candidates(conv["messages"])
        for cand in candidates:
            r = validate_and_store(cand, store)
            if r.get("stored"):
                pass  # stored

    # Stats
    completed = sum(1 for r in results if r["completed"])
    failed = sum(1 for r in results if r["failed"])
    lessons_stored = len(store.get_all_active())

    print(f"\nResults: {completed}/{len(results)} completed, {failed} failed")
    print(f"Lessons extracted and stored: {lessons_stored}")
    store.close()

    # Verify
    assert completed > 0, "Should have some completed tasks"
    assert lessons_stored > 0, "Should have stored lessons from error patterns"
    assert len(results) == 20, "Should process all 20 tasks"

print()
print("=== DRY-RUN PASS ===")
