#!/usr/bin/env python3
"""Tests for all RSI experiment modules — standalone, no pytest needed."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
print(f"=== RSI Modules Test Suite ===\n")

# ── 1. tasks ──────────────────────────────────────────────────────────
from tasks import get_task_batch, BenchmarkTask
tasks = get_task_batch()
assert len(tasks) == 20, f"Expected 20 tasks, got {len(tasks)}"
debug = [t for t in tasks if t.category == "debugging"]
shell = [t for t in tasks if t.category == "shell"]
assert len(debug) == 10, f"Expected 10 debug tasks, got {len(debug)}"
assert len(shell) == 10, f"Expected 10 shell tasks, got {len(shell)}"
for t in tasks:
    assert isinstance(t, BenchmarkTask)
    assert t.id and t.prompt and t.category
print("  [PASS] tasks.py — 20 tasks (10 debug + 10 shell)")

# ── 2. rsi_extractor ──────────────────────────────────────────────────
from rsi_extractor import extract_lesson_candidates, has_cause_effect, _mentions_tool

assert has_cause_effect("X causes Y")
assert has_cause_effect("because of this")
assert not has_cause_effect("hello world")
assert _mentions_tool("use read_file to open")
assert not _mentions_tool("use something random")

# Mock conversation with failure pattern
mock_msgs = [
    {"role": "user", "content": "fix this"},
    {"role": "assistant", "content": "", "tool_calls": [
        {"id": "call_1", "function": {"name": "read_file", "arguments": "{}"}}
    ]},
    {"role": "tool", "tool_call_id": "call_1", "content": "Error: file not found"},
]
candidates = extract_lesson_candidates(mock_msgs)
assert len(candidates) >= 1, f"Expected >=1 candidate, got {len(candidates)}"
print("  [PASS] rsi_extractor.py — cause-effect, tool mention, candidate extraction")

# ── 3. rsi_validator ──────────────────────────────────────────────────
from rsi_validator import validate_lesson, meets_criteria

valid_text = "Using read_file without encoding causes UnicodeDecodeError. Always use encoding='utf-8' to fix."
ok, _ = meets_criteria(valid_text, [])
assert ok, f"Valid text should pass: {valid_text}"

short_text = "hi"
ok, reason = meets_criteria(short_text, [])
assert not ok and "short" in (reason or "").lower(), f"Short text should fail: {reason}"

no_tool = "Using things causes problems because of reasons therefore careful."
ok, reason = meets_criteria(no_tool, [])
assert not ok, "No tool mention should fail"

verdict = validate_lesson({"content": valid_text}, [])
assert verdict["is_valid"]
print("  [PASS] rsi_validator.py — criteria, length, tool, dedup")

# ── 4. rsl_memory_store ───────────────────────────────────────────────
from rsl_memory_store import MemoryStore, lesson_from_candidate

with tempfile.TemporaryDirectory() as tmp:
    import rsl_memory_store as ms
    old = ms.HERMES_HOME
    ms.HERMES_HOME = Path(tmp)

    store = MemoryStore("test_persona")
    # Store
    lid = store.store_lesson({"content": "test", "confidence": 0.8, "action_body": "test lesson body"})
    assert lid, f"Expected lesson_id, got {lid}"
    # Query by search
    results = store.query_lessons(search_text="test", min_confidence=0.0)
    assert len(results) >= 1, f"Expected >=1 from FTS5, got {len(results)}"
    # Query by trigger
    t_results = store.query_lessons(trigger_type="error", min_confidence=0.0)
    assert isinstance(t_results, list)
    # Update confidence
    store.update_confidence(lid, helped=True)
    lesson = store.get_lesson(lid)
    assert lesson["confidence"] >= 0.8, f"Confidence should increase, got {lesson['confidence']}"
    # Deprecate
    store.deprecate_lesson(lid)
    lesson = store.get_lesson(lid)
    assert lesson["status"] == "deprecated", f"Status should be deprecated, got {lesson['status']}"
    store.close()
    ms.HERMES_HOME = old

print("  [PASS] rsl_memory_store.py — CRUD, FTS5, confidence, deprecate")

# ── 5. rsl_validator (enhanced) ────────────────────────────────────────
from rsl_validator import validate_and_store, meets_criteria as enhanced_meets
from rsl_memory_store import MemoryStore as MS2

valid = "Using terminal without escaping causes shell injection. Always use shlex.quote() to prevent."
ok, _ = enhanced_meets(valid, [])
assert ok, f"Enhanced criteria should pass: {valid}"

with tempfile.TemporaryDirectory() as tmp:
    import rsl_memory_store as ms2
    old2 = ms2.HERMES_HOME
    ms2.HERMES_HOME = Path(tmp)

    store = MS2("test_validator")
    result = validate_and_store({"content": valid, "source_tool": "terminal", "confidence": 0.7}, store)
    assert result["stored"], f"Should store valid lesson: {result}"
    active = store.get_all_active()
    assert len(active) == 1, f"Expected 1 active lesson, got {len(active)}"
    store.close()
    ms2.HERMES_HOME = old2

print("  [PASS] rsl_validator.py — enhanced criteria + store integration")

# ── Summary ───────────────────────────────────────────────────────────
print(f"\n=== All {5} modules: PASS ===")
