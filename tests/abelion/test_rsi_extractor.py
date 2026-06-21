"""Tests for rsi_extractor module."""
import sys
sys.path.insert(0, "docs/abelion/research/scripts")

from rsi_extractor import extract_lesson_candidates, has_cause_effect


def test_extract_from_empty_messages():
    result = extract_lesson_candidates([])
    assert result == []


def test_extract_from_messages_with_error():
    """Messages with tool call failures should yield candidates."""
    messages = [
        {"role": "user", "content": "Fix the import error"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"file_path": "/tmp/test.py"}',
                    },
                }
            ],
        },
        {
            "role": "tool",
            "content": "Error: FileNotFoundError: /tmp/test.py does not exist",
            "tool_call_id": "call_1",
        },
        {
            "role": "assistant",
            "content": "I see the file is missing. Let me use search_files to find it.",
        },
        {
            "role": "user",
            "content": "The correct path is /tmp/rsibench_fix_import.py",
        },
    ]
    candidates = extract_lesson_candidates(messages)
    assert len(candidates) >= 1
    first = candidates[0]
    assert "content" in first and len(first["content"]) > 0
    assert "source_tool" in first
    assert "confidence" in first


def test_has_cause_effect_positive():
    assert has_cause_effect(
        "Using read_file without checking path first causes FileNotFoundError"
    )


def test_has_cause_effect_negative():
    assert not has_cause_effect("The file was not found")
