#!/usr/bin/env python3
"""E2E tests for RSI pipeline — extractor → validator.

Verifies:
1. Extractor produces actionable heuristics (v2 quality)
2. Validator accepts good heuristic, rejects bad
3. Conflict detection works
4. Duplicate detection works
"""

import sys, tempfile, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
print("=== E2E: RSI Pipeline ===")

# 1. Extractor
from rsi_extractor import extract_lesson_candidates

mock_msgs = [
    {"role": "user", "content": "fix"},
    {"role": "assistant", "content": "", "tool_calls": [
        {"id": "c1", "function": {"name": "terminal", "arguments": "{}"}}
    ]},
    {"role": "tool", "tool_call_id": "c1", "content": "Error: awk: line 1: cannot access /tmp/nonexistent"},
    {"role": "user", "content": "check"},
    {"role": "assistant", "content": "", "tool_calls": [
        {"id": "c2", "function": {"name": "read_file", "arguments": "{}"}}
    ]},
    {"role": "tool", "tool_call_id": "c2", "content": "FileNotFoundError: No such file or directory"},
]
candidates = extract_lesson_candidates(mock_msgs)

assert len(candidates) >= 1, f"Expected >=1 candidate, got {len(candidates)}"
for c in candidates:
    content = c.get("content", "")
    assert "Using terminal without proper validation causes errors" not in content, \
        f"v1 generic template: {content[:80]}"
    assert len(content) > 40, f"Content short: {content[:80]}"
    assert c.get("confidence", 0) >= 0.3, f"Conf low: {c}"
print(f"  ✓ Extractor: {len(candidates)} quality candidates")

# 2. Validator
from rsi_validator import meets_criteria, validate_lesson, validate_and_store as v_and_s

# Good heuristic
good = ("Thread safety: When multiple threads access shared data, "
        "always use threading.Lock. Acquire before reads and writes.")
ok, reason = meets_criteria(good, [])
assert ok, f"Good heuristic should pass: {reason}"
print(f"  ✓ Validator: accepts heuristic format")

# Bad (too short)
ok, reason = meets_criteria("x", [])
assert not ok
print(f"  ✓ Validator: rejects too short")

# Duplicate
ok, reason = meets_criteria(good, [good])
assert not ok
print(f"  ✓ Validator: detects duplicate")

# Contradiction
ok, reason = meets_criteria("never use grep for file search", ["always use grep for file search"])
assert not ok
print(f"  ✓ Validator: detects contradiction ({reason})")

# Validate lesson API
verdict = validate_lesson({"content": good}, [])
assert verdict["is_valid"]
assert verdict["adjusted_confidence"] > 0.5
print(f"  ✓ validate_lesson: returns verdict (conf={verdict['adjusted_confidence']})")

# Validate and store with callback
store_result = v_and_s({"content": good, "source_tool": "terminal"}, 
                       store_callback=lambda d: "test-id-123")
assert store_result["stored"]
assert store_result["lesson_id"] == "test-id-123"
print(f"  ✓ validate_and_store: callback works")

# Validate and store with store object
from collections import namedtuple
MockStore = namedtuple('MockStore', ['get_all_active', 'store_lesson'])
mock_store = MockStore(
    get_all_active=lambda: [{"action_body": "Something completely unrelated about grep usage"}],
    store_lesson=lambda d: "mock-id"
)
store_result2 = v_and_s({"content": "Recursion depth: When function recurses too deep, add iterative fallback instead.", "source_tool": "terminal"}, store=mock_store)
assert store_result2["stored"], f"Should store new unique lesson: {store_result2}"
print(f"  ✓ validate_and_store: store object works")

print()
print("=== ALL E2E CHECKS PASSED ===")
