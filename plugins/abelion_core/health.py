import json
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

_VERIFIED_MODELS = set()


def verify_model_health(agent: Any) -> Optional[str]:
    """
    Check if the selected model is responding on the current provider.
    Returns an error message if failed, else None.
    """
    if not agent or not agent.model:
        return "No model selected."

    if agent.model in _VERIFIED_MODELS:
        return None

    # Only verify for custom/9router/aggregators to avoid overhead on stable providers
    # 'antigravity' is a common alias used in this workspace.
    if agent.provider not in {"9router", "custom", "openrouter", "antigravity"}:
        return None

    base_url = agent.base_url
    if not base_url or not base_url.startswith("http"):
        # Fallback to 9router default if provider is 9router
        if agent.provider == "9router":
            base_url = "https://api.9router.ai/v1"
        else:
            return None

    logger.info(f"[abelion_core] Verifying model health: {agent.model} on {base_url}")

    # Try a minimal completion request
    try:
        headers = {"Authorization": f"Bearer {agent.api_key}"}
        payload = {
            "model": agent.model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
        }

        # Use short timeout for health check
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            if resp.status_code == 200:
                _VERIFIED_MODELS.add(agent.model)
                return None
            else:
                try:
                    err_data = resp.json()
                    msg = err_data.get("error", {}).get("message", resp.text)
                except:
                    msg = resp.text
                return f"Model {agent.model} reported error {resp.status_code}: {msg}"
    except Exception as e:
        return f"Failed to connect to model {agent.model}: {e}"


def register_health_tools(ctx):
    schema = {
        "name": "abelion_test_model",
        "description": "Test if a model is currently available and working on the active provider. Use this to avoid 'not work' models.",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "Optional: Model ID to test. Defaults to current model.",
                },
                "provider": {
                    "type": "string",
                    "description": "Optional: Provider to test on. Defaults to current provider.",
                },
            },
        },
    }

    def handler(args, **kwargs):
        agent = kwargs.get("parent_agent")
        if not agent:
            return json.dumps({"error": "No agent context available for health check."})

        # Temporarily swap model/provider if specified
        old_model = agent.model
        old_provider = agent.provider

        test_model = args.get("model", agent.model)
        test_provider = args.get("provider", agent.provider)

        agent.model = test_model
        agent.provider = test_provider

        # Force fresh check
        if test_model in _VERIFIED_MODELS:
            _VERIFIED_MODELS.remove(test_model)

        error = verify_model_health(agent)

        # Restore
        agent.model = old_model
        agent.provider = old_provider

        if error:
            return json.dumps({"success": False, "error": error})
        return json.dumps({
            "success": True,
            "message": f"Model {test_model} is ONLINE and working.",
        })

    ctx.register_tool(
        name="abelion_test_model",
        toolset="abelion_core",
        schema=schema,
        handler=handler,
    )
