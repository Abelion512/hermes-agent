import json
import logging
from functools import partial

from .caching import optimize_caching
from .circuit_breaker import get_breaker
from .health import register_health_tools, verify_model_health
from .loop_detector import check_loop

# Import unified modules
from .reflection import cache_messages, record_reflection
from .recall_tool import register_recall_tool

logger = logging.getLogger(__name__)

# Track RAG calls per session to limit iterations
_rag_calls_count = {}


def pre_tool_hook(tool_name, args, **kwargs):
    """
    Hook: pre_tool_call
    Applies loop detection, circuit breaker, RAM monitor, and RAG iteration capping.
    """
    session_id = kwargs.get("session_id") or ""

    # 1. Loop Detection
    loop_result = check_loop(tool_name, args, **kwargs)
    if loop_result:
        return loop_result  # If it decides to block

    # 2. Circuit Breaker for Delegation (Native delegate_task)
    if tool_name == "delegate_task":
        breaker = get_breaker("delegation")
        if not breaker.allow_request():
            logger.warning("[abelion_core] Delegation blocked by circuit breaker.")
            return {
                "action": "block",
                "message": "Delegation service is temporarily unavailable (Circuit Breaker OPEN). Please try again in 30 seconds.",
            }

    # 3. RAG Iteration Capping
    if tool_name == "knowledge_search":
        count = _rag_calls_count.get(session_id, 0)
        if count >= 3:
            logger.warning(f"[abelion_core.rag] Blocked knowledge_search in session {session_id} - reached limit of 3.")
            return {
                "action": "block",
                "message": "Blocked: knowledge_search has been called 3 times in this task. Capping RAG search iterations to prevent infinite search loops."
            }
        _rag_calls_count[session_id] = count + 1

    # 4. RAM Monitor Check
    try:
        from .ram_monitor import enforce_ram_guard
        is_ram_critical = enforce_ram_guard()
        if is_ram_critical:
            # Block heavy tools if RAM is critical (>80%)
            heavy_tools = {"execute_command", "run_command", "browser_navigate", "browser_click", "browser_type"}
            if tool_name in heavy_tools:
                logger.warning(f"[abelion_core.ram] Blocking heavy tool '{tool_name}' due to critical RAM usage.")
                return {
                    "action": "block",
                    "message": "Blocked: System RAM usage is critical (>80%). Running new subprocesses or browser instances is temporarily disabled to prevent OOM crash."
                }
    except Exception as e:
        logger.error(f"[abelion_core.ram] RAM Guard hook check failed: {e}")

    return None


def pre_llm_hook(**kwargs):
    """
    Hook: pre_llm_call
    Performs model health checks and RAM alerts.
    """
    context = ""

    # Model health check (first turn only to minimize latency)
    agent = kwargs.get("agent")
    messages = kwargs.get("messages", [])
    if agent and len(messages) <= 1:
        error = verify_model_health(agent)
        if error:
            context += f"\n\n⚠️ WARNING: Model health check failed: {error}. This model may be offline or restricted.\n"

    # RAM alert check before LLM calls
    try:
        from .ram_monitor import get_system_ram_percent
        sys_percent = get_system_ram_percent()
        if sys_percent >= 80:
            context += f"\n\n⚠️ WARNING: System RAM usage is currently critical ({sys_percent}%). Please close unneeded applications to prevent crashes.\n"
    except Exception as e:
        logger.debug(f"[abelion_core.ram] Failed to check RAM status in pre_llm_hook: {e}")

    return {"context": context} if context else None


def on_session_end_hook(ctx, session_id=None, **kwargs):
    """
    Hook: on_session_end
    Trigger active reflection and cleanup session-specific counters.
    """
    record_reflection(ctx, session_id=session_id, **kwargs)
    if session_id:
        _rag_calls_count.pop(session_id, None)


def register(ctx):
    """
    Register the abelion_core plugin.
    """
    # Ensure memory store DB is initialized on plugin load
    try:
        from .memory_store import init_db
        init_db()
    except Exception as e:
        logger.error(f"[abelion_core] Failed to auto-initialize memory store DB: {e}")

    # 1. Caching & RAM Guard
    ctx.register_middleware("llm_request", optimize_caching)

    # 2. RSI Phase 1.1: Active Reflection
    ctx.register_hook("post_llm_call", cache_messages)
    ctx.register_hook("on_session_end", partial(on_session_end_hook, ctx))

    # 3. Safety Hooks
    ctx.register_hook("pre_tool_call", pre_tool_hook)
    ctx.register_hook("pre_llm_call", pre_llm_hook)

    # 4. Specialized Tools
    register_health_tools(ctx)
    register_recall_tool(ctx)

    logger.info(
        "abelion_core plugin registered successfully."
    )
