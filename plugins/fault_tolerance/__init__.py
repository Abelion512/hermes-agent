"""fault_tolerance plugin — Error handling, circuit breakers, and error logging.

Wires:
1. ``post_tool_call`` hook — tracks tool failures and manages the circuit breaker.
2. ``pre_llm_call`` hook — injects "Zero-Alpha" correction memory based on past failures.
3. ``on_session_end`` hook — summarizes errors and persists them to the "Zero-Alpha" memory.
4. ``/fault-tolerance`` slash command — status, reset, config.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# State management
_session_stats: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()
_plugin_ctx: Optional[Any] = None
_ERROR_LOG_PATH = Path("memory/projects/error_log.json")


def _get_stats(session_id: str) -> Dict[str, Any]:
    with _lock:
        if session_id not in _session_stats:
            _session_stats[session_id] = {
                "consecutive_failures": 0,
                "total_failures": 0,
                "tripped": False,
                "errors": [],
                "retry_counts": {},
            }
        return _session_stats[session_id]


def _on_pre_llm_call(session_id: str = "", **_: Any) -> Optional[str]:
    """Inject past failure context to help the agent avoid repeating mistakes."""
    if not _ERROR_LOG_PATH.exists():
        return None

    try:
        with open(_ERROR_LOG_PATH, "r") as f:
            logs = json.load(f)

        # Heuristic: find last 3 failures in this project
        relevant_failures = []
        for entry in reversed(logs):
            for err in entry.get("stats", {}).get("errors", []):
                relevant_failures.append(
                    f"- Tool '{err['tool']}' failed: {err['error_preview']}"
                )
                if len(relevant_failures) >= 3:
                    break
            if len(relevant_failures) >= 3:
                break

        if relevant_failures:
            context = "\n".join(
                [
                    "### 🧠 Zero-Alpha Correction Memory",
                    "Based on past experiences in this project, avoid the following failure patterns:",
                ]
                + relevant_failures
            )
            return context
    except Exception as e:
        logger.error(f"Failed to inject correction memory: {e}")

    return None


def _on_post_tool_call(
    tool_name: str = "",
    args: Optional[Dict[str, Any]] = None,
    result: Any = None,
    task_id: str = "",
    session_id: str = "",
    tool_call_id: str = "",
    **_: Any,
) -> None:
    global _plugin_ctx
    stats = _get_stats(session_id)

    # Heuristic for failure
    is_error = False
    result_str = str(result).lower()

    if "error" in result_str or "failed" in result_str or "exception" in result_str:
        is_error = True

    if is_error:
        stats["consecutive_failures"] += 1
        stats["total_failures"] += 1
        stats["errors"].append({
            "tool": tool_name,
            "args": args,
            "error_preview": result_str[:200],
        })

        threshold = 5
        if stats["consecutive_failures"] >= threshold:
            stats["tripped"] = True
            if _plugin_ctx:
                _plugin_ctx.inject_message(
                    f"⚠️ Circuit breaker tripped after {threshold} consecutive failures. Review logs at memory/projects/error_log.json",
                    role="system",
                )
        else:
            retry_count = stats["retry_counts"].get(tool_call_id, 0)
            if retry_count < 2:
                stats["retry_counts"][tool_call_id] = retry_count + 1
                if _plugin_ctx:
                    _plugin_ctx.inject_message(
                        f"🔄 Tool '{tool_name}' failed. Auto-retry {retry_count + 1}/2. Error: {result_str[:100]}",
                        role="user",
                    )
    else:
        stats["consecutive_failures"] = 0


def _on_session_end(session_id: str = "", **_: Any) -> None:
    stats = _drain_stats(session_id)
    if not stats or stats["total_failures"] == 0:
        return

    try:
        current_logs = []
        if _ERROR_LOG_PATH.exists():
            with open(_ERROR_LOG_PATH, "r") as f:
                current_logs = json.load(f)

        current_logs.append({"session_id": session_id, "stats": stats})

        current_logs = current_logs[-50:]

        with open(_ERROR_LOG_PATH, "w") as f:
            json.dump(current_logs, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save error log: {e}")


def _drain_stats(session_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        return _session_stats.pop(session_id, None)


def _handle_slash(raw_args: str) -> Optional[str]:
    argv = raw_args.strip().split()
    if not argv:
        return "Usage: /fault-tolerance [status|reset]"

    sub = argv[0]
    if sub == "status":
        return json.dumps(_session_stats, indent=2)
    elif sub == "reset":
        with _lock:
            _session_stats.clear()
        return "Fault tolerance stats reset."
    return f"Unknown subcommand: {sub}"


def register(ctx) -> None:
    global _plugin_ctx
    _plugin_ctx = ctx
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_end", _on_session_end)
    ctx.register_command(
        "fault-tolerance",
        handler=_handle_slash,
        description="Monitor and manage agent reliability.",
    )
