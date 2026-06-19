import copy
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

def optimize_caching(request: Dict[str, Any], **kwargs: Any) -> Optional[Dict[str, Any]]:
    """
    Middleware: llm_request
    Optimizes the request for caching and RAM usage.
    """
    changed = False
    new_request = copy.deepcopy(request)

    messages = new_request.get("messages", [])
    if not messages or not isinstance(messages, list):
        return None

    provider = kwargs.get("provider", "")

    # 1. Prefix Stability
    # We trust Hermes core for now.

    # 2. Universal Caching (Anthropic-style markers for proxies)
    if provider in {"custom", "antigravity", "openrouter"}:
        from agent.prompt_caching import apply_anthropic_cache_control

        try:
            cached_messages = apply_anthropic_cache_control(
                messages, cache_ttl="5m", native_anthropic=False
            )
            new_request["messages"] = cached_messages
            changed = True
            logger.debug(f"[abelion_core.caching] Applied Anthropic-style cache markers for provider {provider}")
        except Exception as e:
            logger.warning(f"[abelion_core.caching] Failed to apply cache markers: {e}")

    # 3. RAM Guard: Prune very large tool results
    MAX_PART_SIZE = 50000
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            for part in content:
                if part.get("type") == "text":
                    text = part.get("text", "")
                    if len(text) > MAX_PART_SIZE:
                        part["text"] = text[:MAX_PART_SIZE] + "\n\n[... truncated by abelion_core RAM Guard ...]"
                        changed = True
        elif isinstance(content, str):
            if len(content) > MAX_PART_SIZE:
                msg["content"] = content[:MAX_PART_SIZE] + "\n\n[... truncated by abelion_core RAM Guard ...]"
                changed = True

    if changed:
        return {"request": new_request}
    return None
