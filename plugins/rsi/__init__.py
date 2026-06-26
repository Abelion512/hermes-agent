"""RSI Plugin for Hermes — Recurrent Self-Improvement.

Extension point: General Plugin (bukan MemoryProvider).
Injection target: agent.ephemeral_system_prompt (NOT cached — safe).

Lifecycle:
  on_session_start  → inject compressed lessons into ephemeral_system_prompt
  post_tool_call    → capture tool failure events
  on_session_end    → extract lessons from collected events, store to MEMORY.md

Hook signatures (dari codebase aktual):
  on_session_start:  session_id, model, platform
  post_tool_call:    function_name, function_args, result, status, error_type,
                     error_message, session_id, tool_call_id, turn_id, ...
  on_session_end:    session_id, task_id, turn_id, completed, interrupted, model, platform
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from .compressor import Lesson, LessonCompressor
from .lesson_store import LessonStore
from .lesson_extractor import LessonExtractor

logger = logging.getLogger(__name__)

# Plugin metadata — dibaca oleh Hermes plugin system.
PLUGIN_NAME = "rsi"
PLUGIN_VERSION = "2.0.0"
PLUGIN_DESCRIPTION = "Recurrent Self-Improvement — learns from tool errors via ephemeral injection"


# Module-level state (pattern: Hermes hooks are stateless functions,
# pakai module-level vars untuk persist antar hook calls per session).
_store: LessonStore | None = None
_compressor = LessonCompressor()
_extractor = LessonExtractor()

# Per-session state
_session_id: str = ""
_session_tool_events: list[dict] = []
_session_metrics: dict = {}
_session_start_time: Optional[datetime] = None


def _reset_session():
    global _session_id, _session_tool_events, _session_metrics, _session_start_time
    _session_id = ""
    _session_tool_events = []
    _session_start_time = None
    _session_metrics = {
        "tool_calls_total": 0,
        "tool_calls_failed": 0,
        "first_attempt_success": None,
        "error_types_seen": [],
        "lessons_injected": 0,
    }


def _ensure_store() -> LessonStore:
    global _store
    if _store is None:
        _store = LessonStore()
    return _store


# ── HOOKS ─────────────────────────────────────────────────────────────

def on_session_start(**kwargs: Any) -> None:
    """Hook: on_session_start. Fired once per new session.

    Inject compressed RSI lessons into agent.ephemeral_system_prompt.
    """
    global _session_id, _session_start_time

    _reset_session()
    _session_id = kwargs.get("session_id", "")
    _session_start_time = datetime.now(timezone.utc)

    store = _ensure_store()

    # Ambil lessons
    lessons = store._read_all()
    deduped = LessonCompressor.deduplicate(lessons)
    compressed = _compressor.compress(deduped)

    if not compressed:
        logger.debug("[RSI] No lessons to inject for session %s", _session_id[:8])
        return

    # Inject via ephemeral_system_prompt — Hermes append ini di API-call time,
    # TIDAK masuk ke _cached_system_prompt, jadi cache prefix AMAN.
    try:
        import hermes_cli.plugins as plugins
        agent = plugins.current_agent()
        if agent is None:
            logger.warning("[RSI] No current agent — skipping injection")
            return

        existing = getattr(agent, "ephemeral_system_prompt", "") or ""
        agent.ephemeral_system_prompt = (
            existing + "\n\n" + compressed
            if existing
            else compressed
        )
        _session_metrics["lessons_injected"] = len(deduped)
        logger.info(
            "[RSI] Session %s: injected %d lessons (%d chars)",
            _session_id[:8], len(deduped), len(compressed),
        )
    except Exception as e:
        logger.warning("[RSI] Injection failed: %s", e)


def on_post_tool_call(**kwargs: Any) -> None:
    """Hook: post_tool_call. Fired after every tool call.

    Captures failure events for lesson extraction at session end.
    """
    global _session_metrics

    _session_metrics["tool_calls_total"] += 1

    status = kwargs.get("status", "")
    error_type = kwargs.get("error_type", "")
    error_message = kwargs.get("error_message", "")
    function_name = kwargs.get("function_name", "unknown")
    function_args = kwargs.get("function_args", {})

    # First attempt tracking (for FASR metric)
    if _session_metrics["first_attempt_success"] is None:
        _session_metrics["first_attempt_success"] = (status != "error")

    if status == "error" or error_type:
        _session_metrics["tool_calls_failed"] += 1
        if error_type and error_type not in _session_metrics["error_types_seen"]:
            _session_metrics["error_types_seen"].append(error_type)

        _session_tool_events.append({
            "type": "tool_failure",
            "tool": function_name,
            "input": function_args,
            "error": error_type or "unknown",
            "error_detail": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    else:
        _session_tool_events.append({
            "type": "tool_success",
            "tool": function_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


def on_session_end(**kwargs: Any) -> None:
    """Hook: on_session_end. Fired at session boundary.

    Extract lessons from collected tool events, store to MEMORY.md.
    """
    global _session_id

    if not _session_id:
        return

    session_id = _session_id
    completed = kwargs.get("completed", False)
    interrupted = kwargs.get("interrupted", False)

    outcome = "success" if completed and not interrupted else "failure" if interrupted else "partial"

    duration_s = (
        (datetime.now(timezone.utc) - _session_start_time).total_seconds()
        if _session_start_time else 0
    )

    # Finalize metrics
    metrics = {
        **_session_metrics,
        "session_id": session_id,
        "outcome": outcome,
        "duration_seconds": duration_s,
        "error_type_count": len(_session_metrics["error_types_seen"]),
    }

    store = _ensure_store()

    # Extract lessons
    if _session_tool_events:
        new_lessons = _extractor.extract(
            tool_events=_session_tool_events,
            session_outcome=outcome,
        )
        for lesson in new_lessons:
            # Use sync version — Hermes hooks are sync
            import asyncio
            try:
                asyncio.get_running_loop()
                # Already in event loop — schedule
                import asyncio
                asyncio.ensure_future(store.upsert_lesson(lesson))
            except RuntimeError:
                # No event loop — create one
                import asyncio
                asyncio.run(store.upsert_lesson(lesson))

        # Save metrics
        try:
            asyncio.run(store.save_session_metrics(metrics))
        except Exception as e:
            logger.warning("[RSI] Failed to save metrics: %s", e)

        logger.info(
            "[RSI] Session %s: %s, extracted %d lessons, "
            "FASR=%s, errors=%d/%d",
            session_id[:8], outcome, len(new_lessons),
            metrics.get("first_attempt_success"),
            metrics.get("tool_calls_failed", 0),
            metrics.get("tool_calls_total", 0),
        )

    _reset_session()
