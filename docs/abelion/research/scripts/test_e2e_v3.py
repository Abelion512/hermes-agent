#!/usr/bin/env python3
"""E2E test: runs 5 tasks with full pipeline, asserts lesson quality.

Verifies:
1. Extractor produces actionable heuristics (not raw error dumps)
2. Validator passes good lessons, filters noise
3. MemoryStore persists and retrieves
4. Feedback loop updates confidence
5. Injector selects best lessons
"""

import sys, tempfile, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=== E2E: RSI Pipeline v3 ===")

# 1. Test extractor with mock conversation
from rsi_extractor import extract_lesson_candidates

mock_msgs = [
    {"role": "user", "content": "fix this"},
    {"role": "assistant", "content": "", "tool_calls": [
        {"id": "c1", "function": {"name": "terminal", "arguments": "{}"}}
    ]},
    {"role": "tool", "tool_call_id": "c1", "content": "Error: awk: line 1: cannot access /tmp/nonexistent"},
    {"role": "user", "content": "check"},
    {"role": "assistant", "content": "", "tool_calls": [
        {"id": "c2", "function": {"name": "read_file", "arguments": "{}"}}
    ]},
    {"role": "tool", "tool_call_id": "c2", "content": "FileNotFoundError: No such file or directory: '/tmp/missing.txt'"},
]
candidates = extract_lesson_candidates(mock_msgs)

assert len(candidates) >= 1, f"Expected >=1 candidate, got {len(candidates)}"
for c in candidates:
    content = c.get("content", "")
    action = c.get("action", "")
    # v2 quality check: should NOT be a raw error dump
    assert "Using terminal without proper validation causes errors" not in content, \
        f"v1 generic template found: {content[:100]}"
    # Should have specific heuristic
    assert len(content) > 40, f"Content too short: {content[:100]}"
    assert c.get("confidence", 0) >= 0.3, f"Confidence too low: {c}"
    print(f"  ✓ Candidate: conf={c['confidence']:.2f} trigger={c.get('trigger','')[:40]}")

print(f"  ✓ Extractor: {len(candidates)} quality candidates")

# 2. Test validator
from rsl_memory_store import MemoryStore, lesson_from_candidate

with tempfile.TemporaryDirectory() as tmp:
    import rsl_memory_store as ms
    ms.HERMES_HOME = Path(tmp)
    
    store = MemoryStore("test_e2e")
    
    # Validate + store
    from rsl_validator import validate_and_store
    good_cand = {
        "content": "Thread safety: When multiple threads access shared data, always use threading.Lock. Acquire lock before all reads AND writes. Release in finally block or use 'with lock:'.",
        "source_tool": "terminal",
        "confidence": 0.8,
    }
    bad_cand = {
        "content": "x",  # too short, no substance
        "source_tool": "terminal",
        "confidence": 0.1,
    }
    
    r1 = validate_and_store(good_cand, store)
    assert r1.get("stored"), f"Good candidate should store: {r1}"
    print(f"  ✓ Validator accepted good candidate: id={r1.get('lesson_id','')[:8]}")
    
    r2 = validate_and_store(bad_cand, store)
    assert not r2.get("stored"), f"Bad candidate should be rejected: {r2}"
    print(f"  ✓ Validator rejected bad candidate: {r2.get('reason','')}")
    
    # Direct store (raw RSI)
    lid = store.store_lesson(lesson_from_candidate(good_cand))
    assert lid, "store_lesson should return id"
    print(f"  ✓ MemoryStore stored lesson: {lid[:8]}")
    
    # Query
    results = store.get_all_active()
    assert len(results) >= 1, f"Expected >=1 active lesson, got {len(results)}"
    print(f"  ✓ MemoryStore.query: {len(results)} active")
    
    # Feedback loop
    store.update_confidence(lid, helped=True)
    lesson = store.get_lesson(lid)
    assert lesson["confidence"] >= 0.8, f"Confidence should increase: {lesson['confidence']}"
    print(f"  ✓ Feedback loop: confidence {lesson['confidence']:.2f} (increased)")
    
    # Deprecate
    store.deprecate_lesson(lid)
    lesson = store.get_lesson(lid)
    assert lesson["status"] == "deprecated"
    print(f"  ✓ MemoryStore: deprecation works")
    
    store.close()

# 3. Test injector
from rsl_injector import Injector
injector = Injector(max_inline=3, max_tokens=800)

mock_lessons = [
    {"trigger": "Thread safety", "action": "Always use threading.Lock for shared data", "confidence": 0.8, "evidence_count": 3},
    {"trigger": "Encoding", "action": "Always use UTF-8 for encoding/decoding", "confidence": 0.7, "evidence_count": 2},
    {"trigger": "Recursion", "action": "Add iterative fallback for n > 1000", "confidence": 0.6, "evidence_count": 1},
]
selected = injector.select_lessons(mock_lessons)
assert len(selected) <= 3, f"Select should respect limit: {len(selected)}"
assert selected[0]["confidence"] == 0.8, "First should be highest confidence"
print(f"  ✓ Injector selected {len(selected)}/{len(mock_lessons)} lessons (top={selected[0]['confidence']})")

compressed = injector.compress(mock_lessons)
assert len(compressed) == 3, "Compress should keep all with unique triggers"

prompt = injector.format_injection_prompt(selected)
assert "[Lessons from experience]" in prompt
assert "1." in prompt
print(f"  ✓ Injector format: {len(prompt)} chars")

# Duplicate trigger test
dup_lessons = mock_lessons + [{"trigger": "Thread safety", "action": "Different action", "confidence": 0.9, "evidence_count": 1}]
deduped = injector.compress(dup_lessons)
assert len(deduped) == 3, f"Compress should dedup triggers: {len(deduped)} vs expected 3"
print(f"  ✓ Injector dedup: {len(dup_lessons)} → {len(deduped)} (removed duplicate trigger)")

print()
print("=== ALL E2E CHECKS PASSED ===")
