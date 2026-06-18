import json
import logging
from functools import partial

from .caching import optimize_caching
from .circuit_breaker import get_breaker
from .health import register_health_tools, verify_model_health
from .loop_detector import check_loop

# Import unified modules
from .reflection import cache_messages, record_reflection

logger = logging.getLogger(__name__)


def pre_tool_hook(tool_name, args, **kwargs):
    """
    Hook: pre_tool_call
    Applies loop detection and circuit breaker logic sequentially.
    """
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

    return None


def pre_llm_hook(**kwargs):
    """
    Hook: pre_llm_call
    Performs model health checks.
    """
    context = ""

    # Model health check (first turn only to minimize latency)
    agent = kwargs.get("agent")
    messages = kwargs.get("messages", [])
    if agent and len(messages) <= 1:
        error = verify_model_health(agent)
        if error:
            context += f"\n\n⚠️ WARNING: Model health check failed: {error}. This model may be offline or restricted.\n"

    return {"context": context} if context else None


def register(ctx):
    """
    Register the unified abelion_core plugin.
    """
    # 1. Caching & RAM Guard
    ctx.register_middleware("llm_request", optimize_caching)

    # 2. RSI Phase 1.1: Active Reflection
    ctx.register_hook("post_llm_call", cache_messages)
    ctx.register_hook("on_session_end", partial(record_reflection, ctx))

    # 3. Safety Hooks
    ctx.register_hook("pre_tool_call", pre_tool_hook)
    ctx.register_hook("pre_llm_call", pre_llm_hook)

    # 4. Specialized Tools
    register_health_tools(ctx)

    logger.info(
        "abelion_core plugin registered successfully. (Hierarchy removed in favor of native Kanban/Prompts)"
    )
