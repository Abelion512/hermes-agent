"""Tests for rsi_validator module."""
import sys
sys.path.insert(0, "docs/abelion/research/scripts")

from rsi_validator import validate_lesson, meets_criteria


def test_validates_good_lesson():
    lesson = {
        "content": (
            "Using read_file without checking path first causes FileNotFoundError. "
            "Always verify path with search_files before reading."
        ),
        "source_tool": "read_file",
        "confidence": 0.8,
    }
    result = validate_lesson(lesson, existing_lessons=[])
    assert result["is_valid"] is True
    # reason should be None or contain "pass"
    assert result["reason"] in (None, "pass")


def test_rejects_short_lesson():
    lesson = {
        "content": "File not found",
        "source_tool": "read_file",
        "confidence": 0.3,
    }
    result = validate_lesson(lesson, existing_lessons=[])
    assert result["is_valid"] is False
    assert "length" in result["reason"].lower() or "short" in result["reason"].lower()


def test_rejects_no_cause_effect():
    lesson = {
        "content": (
            "The file was not found in the directory structure when the agent "
            "tried to access it."
        ),
        "source_tool": "read_file",
        "confidence": 0.4,
    }
    result = validate_lesson(lesson, existing_lessons=[])
    assert result["is_valid"] is False
    assert "cause" in result["reason"].lower() or "effect" in result["reason"].lower()


def test_detects_duplicate():
    lesson = {
        "content": "Using read_file without checking path first causes FileNotFoundError.",
        "source_tool": "read_file",
        "confidence": 0.8,
    }
    existing = [lesson]
    result = validate_lesson(lesson, existing_lessons=existing)
    assert result["is_valid"] is False
    assert "duplicate" in result["reason"].lower()


def test_meets_criteria():
    assert meets_criteria(
        "This is a good lesson with cause effect because it explains things.",
        [],
    )


def test_meets_criteria_short():
    assert not meets_criteria("Hi", [])[0]
