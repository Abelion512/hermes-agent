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


def _patch_kanban_db(redact_fn):
    """
    Monkey patch hermes_cli.kanban_db write functions to apply PII redaction
    on all text fields before they are persisted to SQLite.

    Patched functions:
      - create_task       → redacts title, body
      - add_comment       → redacts body
      - complete_task     → redacts result, summary
      - block_task        → redacts reason
      - specify_triage_task → redacts title, body

    Strategy: guard with _orig_* sentinel so double-registration (plugin
    reloads) is a no-op.
    """
    try:
        import hermes_cli.kanban_db as kanban_db

        # ------------------------------------------------------------------ #
        # 1. create_task — redact title, body
        # ------------------------------------------------------------------ #
        if not hasattr(kanban_db, "_orig_create_task"):
            kanban_db._orig_create_task = kanban_db.create_task

            def _patched_create_task(conn, *, title, body=None, **kw):
                if isinstance(title, str):
                    title = redact_fn(title)
                if isinstance(body, str):
                    body = redact_fn(body)
                return kanban_db._orig_create_task(conn, title=title, body=body, **kw)

            kanban_db.create_task = _patched_create_task
            logger.info("[abelion_core] Patched kanban_db.create_task for PII Redaction")

        # ------------------------------------------------------------------ #
        # 2. add_comment — redact body
        # ------------------------------------------------------------------ #
        if not hasattr(kanban_db, "_orig_add_comment"):
            kanban_db._orig_add_comment = kanban_db.add_comment

            def _patched_add_comment(conn, task_id, author, body):
                if isinstance(body, str):
                    body = redact_fn(body)
                return kanban_db._orig_add_comment(conn, task_id, author, body)

            kanban_db.add_comment = _patched_add_comment
            logger.info("[abelion_core] Patched kanban_db.add_comment for PII Redaction")

        # ------------------------------------------------------------------ #
        # 3. complete_task — redact result, summary
        # ------------------------------------------------------------------ #
        if not hasattr(kanban_db, "_orig_complete_task"):
            kanban_db._orig_complete_task = kanban_db.complete_task

            def _patched_complete_task(conn, task_id, *, result=None, summary=None, **kw):
                if isinstance(result, str):
                    result = redact_fn(result)
                if isinstance(summary, str):
                    summary = redact_fn(summary)
                return kanban_db._orig_complete_task(
                    conn, task_id, result=result, summary=summary, **kw
                )

            kanban_db.complete_task = _patched_complete_task
            logger.info("[abelion_core] Patched kanban_db.complete_task for PII Redaction")

        # ------------------------------------------------------------------ #
        # 4. block_task — redact reason
        # ------------------------------------------------------------------ #
        if not hasattr(kanban_db, "_orig_block_task"):
            kanban_db._orig_block_task = kanban_db.block_task

            def _patched_block_task(conn, task_id, *, reason=None, **kw):
                if isinstance(reason, str):
                    reason = redact_fn(reason)
                return kanban_db._orig_block_task(conn, task_id, reason=reason, **kw)

            kanban_db.block_task = _patched_block_task
            logger.info("[abelion_core] Patched kanban_db.block_task for PII Redaction")

        # ------------------------------------------------------------------ #
        # 5. specify_triage_task — redact title, body
        # ------------------------------------------------------------------ #
        if not hasattr(kanban_db, "_orig_specify_triage_task"):
            kanban_db._orig_specify_triage_task = kanban_db.specify_triage_task

            def _patched_specify_triage_task(
                conn, task_id, *, title=None, body=None, **kw
            ):
                if isinstance(title, str):
                    title = redact_fn(title)
                if isinstance(body, str):
                    body = redact_fn(body)
                return kanban_db._orig_specify_triage_task(
                    conn, task_id, title=title, body=body, **kw
                )

            kanban_db.specify_triage_task = _patched_specify_triage_task
            logger.info("[abelion_core] Patched kanban_db.specify_triage_task for PII Redaction")

    except Exception as e:
        logger.error(f"[abelion_core] Failed to patch kanban_db: {e}")


def _patch_validate_requested_model():
    """
    Monkey-patch hermes_cli.models.validate_requested_model so that
    user-defined providers with names matching 'local-*' patterns
    (e.g. 'local-localhost:20128' for 9Router) are treated as
    custom/OpenRouter-compatible endpoints.

    By default, Hermes only recognises the string 'custom' or 'custom:*'
    as custom endpoints.  Named custom providers (set via config.yaml
    providers.<name>) fall through to the generic /v1/models probe path,
    which returns accepted=False if the requested model is not listed --
    even though the proxy (9Router) supports all OpenRouter models.
    """
    try:
        import hermes_cli.models as _models_mod

        if hasattr(_models_mod, "_orig_validate_requested_model_abelion"):
            return  # already patched

        _orig_validate = _models_mod.validate_requested_model

        def _patched_validate(
            model_name,
            provider,
            *,
            api_key=None,
            base_url=None,
            api_mode=None,
        ):
            """
            Intercept validate_requested_model.

            If the provider slug looks like a local named custom provider
            (e.g. 'local-localhost:20128'), normalize it to 'custom' before
            calling the original so it gets the lenient custom-endpoint path
            (accept model even if not in /v1/models listing).
            """
            prov_str = (provider or "").strip().lower()

            # Detect local/named-custom providers:
            # - starts with 'local-'  → e.g. 'local-localhost:20128'
            # - starts with 'local:'  → e.g. 'local:myserver'
            # - contains 'localhost'  → any slug that embeds localhost
            # - starts with '127.'    → e.g. '127.0.0.1:port'
            is_local_custom = (
                prov_str.startswith("local-")
                or prov_str.startswith("local:")
                or "localhost" in prov_str
                or prov_str.startswith("127.")
            )

            if is_local_custom:
                logger.debug(
                    "[abelion_core] validate_requested_model: treating "
                    "provider '%s' as custom (local proxy)", provider
                )
                return _orig_validate(
                    model_name,
                    "custom",
                    api_key=api_key,
                    base_url=base_url,
                    api_mode=api_mode,
                )

            return _orig_validate(
                model_name,
                provider,
                api_key=api_key,
                base_url=base_url,
                api_mode=api_mode,
            )

        _models_mod._orig_validate_requested_model_abelion = _orig_validate
        _models_mod.validate_requested_model = _patched_validate
        logger.info(
            "[abelion_core] Patched validate_requested_model for local custom providers"
        )
    except Exception as e:
        logger.error("[abelion_core] Failed to patch validate_requested_model: %s", e)


def _patch_model_switch_is_custom():
    """
    Monkey-patch hermes_cli.model_switch.switch_model so that the
    'is_custom' guard (which skips detect_provider_for_model) also
    recognises named local providers like 'local-localhost:20128'.

    The original check is:
        is_custom = current_provider in {"custom", "local"} or (
            "localhost" in _base or "127.0.0.1" in _base
        )

    For providers like 'local-localhost:20128', current_provider is NOT
    in {"custom", "local"} but it IS a local custom endpoint.  Without
    is_custom=True, detect_provider_for_model fires and may incorrectly
    re-route the model to an unrelated provider (e.g. OpenRouter).

    This patch is a belt-and-suspenders for switch_model path B step e.
    The real fix is the validate_requested_model patch above.
    """
    try:
        import hermes_cli.model_switch as _ms_mod

        if hasattr(_ms_mod, "_orig_switch_model_abelion"):
            return

        _orig_switch = _ms_mod.switch_model

        def _patched_switch_model(
            raw_input,
            current_provider,
            current_model,
            current_base_url="",
            current_api_key="",
            is_global=False,
            explicit_provider="",
            user_providers=None,
            custom_providers=None,
        ):
            # Normalise named local providers to 'custom' so the switch
            # pipeline uses the correct is_custom=True branch.
            prov = (current_provider or "").strip().lower()
            is_local_named = (
                prov.startswith("local-")
                or prov.startswith("local:")
                or ("localhost" in prov and prov not in {"custom", "local"})
            )
            if is_local_named and not explicit_provider:
                logger.debug(
                    "[abelion_core] switch_model: normalising provider "
                    "'%s' to 'custom' for local proxy", current_provider
                )
                return _orig_switch(
                    raw_input,
                    current_provider="custom",
                    current_model=current_model,
                    current_base_url=current_base_url,
                    current_api_key=current_api_key,
                    is_global=is_global,
                    explicit_provider=explicit_provider,
                    user_providers=user_providers,
                    custom_providers=custom_providers,
                )
            return _orig_switch(
                raw_input,
                current_provider=current_provider,
                current_model=current_model,
                current_base_url=current_base_url,
                current_api_key=current_api_key,
                is_global=is_global,
                explicit_provider=explicit_provider,
                user_providers=user_providers,
                custom_providers=custom_providers,
            )

        _ms_mod._orig_switch_model_abelion = _orig_switch
        _ms_mod.switch_model = _patched_switch_model
        logger.info(
            "[abelion_core] Patched switch_model for local custom providers"
        )
    except Exception as e:
        logger.error("[abelion_core] Failed to patch switch_model: %s", e)


def _patch_discord_model_picker_view():
    """
    Monkey-patch Discord's ModelPickerView to support pagination of models.
    Discord select menus are limited to 25 options. This patch dynamically
    adds 'Prev Page' and 'Next Page' buttons if models count exceeds 23.
    """
    try:
        import sys
        if "hermes_plugins.discord_platform.adapter" not in sys.modules:
            return
        da = sys.modules["hermes_plugins.discord_platform.adapter"]
        cls = da.DiscordAdapter.ModelPickerView
        if hasattr(cls, "_patched_by_abelion"):
            return

        import discord

        orig_init = cls.__init__
        def patched_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            self.model_page = 0
        cls.__init__ = patched_init

        orig_on_provider_selected = cls._on_provider_selected
        async def patched_on_provider_selected(self, interaction):
            self.model_page = 0
            await orig_on_provider_selected(self, interaction)
        cls._on_provider_selected = patched_on_provider_selected

        orig_on_back = cls._on_back
        async def patched_on_back(self, interaction):
            self.model_page = 0
            await orig_on_back(self, interaction)
        cls._on_back = patched_on_back

        def patched_build_model_select(self, provider_slug: str):
            self.clear_items()
            provider = next(
                (p for p in self.providers if p["slug"] == provider_slug), None
            )
            if not provider:
                return

            models = provider.get("models", [])
            options = []

            # Page size is 23 to leave room for Prev, Next, Back, Cancel buttons in Discord's 25 components view limit
            page = getattr(self, "model_page", 0)
            page_size = 23
            start = page * page_size
            end = start + page_size
            page_models = models[start:end]

            for model_id in page_models:
                short = model_id.split("/")[-1] if "/" in model_id else model_id
                options.append(
                    discord.SelectOption(
                        label=short[:100],
                        value=model_id[:100],
                    )
                )
            if not options:
                return

            select = discord.ui.Select(
                placeholder=f"Choose a model ({start+1}-{min(end, len(models))} of {len(models)})...",
                options=options,
                custom_id="model_model_select",
            )
            select.callback = self._on_model_selected
            self.add_item(select)

            total_models = len(models)
            if total_models > page_size:
                if page > 0:
                    prev_btn = discord.ui.Button(
                        label="◀ Prev Page", style=discord.ButtonStyle.blurple, custom_id="model_prev_page"
                    )
                    async def _prev_cb(interaction):
                        if not self._check_auth(interaction):
                            await interaction.response.send_message("You're not authorized~", ephemeral=True)
                            return
                        self.model_page = max(0, self.model_page - 1)
                        self._build_model_select(self._selected_provider)
                        pname = provider.get("name", self._selected_provider) if provider else self._selected_provider
                        total_m = len(provider.get("models", [])) if provider else 0
                        start_idx = self.model_page * 23 + 1
                        end_idx = min((self.model_page + 1) * 23, total_m)
                        await interaction.response.edit_message(
                            embed=discord.Embed(
                                title="⚙ Model Configuration",
                                description=f"Provider: **{pname}** (Showing {start_idx}-{end_idx} of {total_m})\nSelect a model:",
                                color=discord.Color.blue(),
                            ),
                            view=self,
                        )
                    prev_btn.callback = _prev_cb
                    self.add_item(prev_btn)

                if end < total_models:
                    next_btn = discord.ui.Button(
                        label="Next Page ▶", style=discord.ButtonStyle.blurple, custom_id="model_next_page"
                    )
                    async def _next_cb(interaction):
                        if not self._check_auth(interaction):
                            await interaction.response.send_message("You're not authorized~", ephemeral=True)
                            return
                        self.model_page = self.model_page + 1
                        self._build_model_select(self._selected_provider)
                        pname = provider.get("name", self._selected_provider) if provider else self._selected_provider
                        total_m = len(provider.get("models", [])) if provider else 0
                        start_idx = self.model_page * 23 + 1
                        end_idx = min((self.model_page + 1) * 23, total_m)
                        await interaction.response.edit_message(
                            embed=discord.Embed(
                                title="⚙ Model Configuration",
                                description=f"Provider: **{pname}** (Showing {start_idx}-{end_idx} of {total_m})\nSelect a model:",
                                color=discord.Color.blue(),
                            ),
                            view=self,
                        )
                    next_btn.callback = _next_cb
                    self.add_item(next_btn)

            back_btn = discord.ui.Button(
                label="◀ Back", style=discord.ButtonStyle.grey, custom_id="model_back"
            )
            back_btn.callback = self._on_back
            self.add_item(back_btn)

            cancel_btn = discord.ui.Button(
                label="Cancel", style=discord.ButtonStyle.red, custom_id="model_cancel2"
            )
            cancel_btn.callback = self._on_cancel
            self.add_item(cancel_btn)

        cls._build_model_select = patched_build_model_select
        cls._patched_by_abelion = True
        logger.info("[abelion_core] Patched Discord ModelPickerView for pagination")
    except Exception as e:
        logger.error("[abelion_core] Failed to patch Discord ModelPickerView: %s", e)


def _patch_list_authenticated_providers():
    """
    Monkey-patch hermes_cli.model_switch.list_authenticated_providers so that
    custom/local providers (e.g. 9Router 'local-localhost:20128') are populated
    with the complete set of supported models, including:
      - All model aliases configured in the 9Router SQLite DB / db.json
      - All openrouter curated models (both raw, openrouter/ prefixed, and oc/ prefixed)
    """
    try:
        import hermes_cli.model_switch as _ms_mod

        if hasattr(_ms_mod, "_orig_list_authenticated_providers_abelion"):
            return  # already patched

        _orig_list_auth = _ms_mod.list_authenticated_providers

        def _patched_list_auth(*args, **kwargs):
            # Run Discord adapter patch if Discord platform is loaded
            _patch_discord_model_picker_view()

            results = _orig_list_auth(*args, **kwargs)
            if not results:
                return results

            for p in results:
                slug = (p.get("slug") or "").strip().lower()
                api_url = (p.get("api_url") or "").strip().lower()
                is_local_custom = (
                    slug.startswith("local-")
                    or slug.startswith("local:")
                    or "localhost" in slug
                    or slug.rstrip("/") == "local"
                    or "127.0.0.1" in slug
                    or "localhost" in api_url
                    or "127.0.0.1" in api_url
                )

                if is_local_custom:
                    logger.info("[abelion_core] Enhancing local provider model list for '%s'", p.get("slug"))
                    models = list(p.get("models") or [])
                    seen = {m.lower() for m in models}

                    # 1. Fetch aliases from 9Router SQLite DB
                    aliases = []
                    try:
                        import sqlite3
                        db_path = "/home/abelion/.9router/db/data.sqlite"
                        if os.path.exists(db_path):
                            conn = sqlite3.connect(db_path)
                            cur = conn.cursor()
                            cur.execute("SELECT key, value FROM kv WHERE scope='modelAliases'")
                            for row in cur.fetchall():
                                key = row[0]
                                val = row[1]
                                if val.startswith('"') and val.endswith('"'):
                                    val = json.loads(val)
                                aliases.append(key)
                                aliases.append(val)
                            conn.close()
                    except Exception as e:
                        logger.debug("[abelion_core] Failed to query 9router DB: %s", e)

                    # Try JSON fallback if SQLite failed/empty
                    if not aliases:
                        try:
                            import json
                            import os
                            json_path = "/home/abelion/.9router/db.json"
                            if os.path.exists(json_path):
                                with open(json_path, "r") as f:
                                    db_data = json.load(f)
                                    ma = db_data.get("modelAliases", {})
                                    if isinstance(ma, dict):
                                        for k, v in ma.items():
                                            aliases.append(k)
                                            aliases.append(v)
                        except Exception as e:
                            logger.debug("[abelion_core] Failed to read db.json fallback: %s", e)

                    # Add aliases to models
                    for a in aliases:
                        if a and a.lower() not in seen:
                            models.append(a)
                            seen.add(a.lower())

                    # 2. Add OpenRouter models
                    try:
                        from hermes_cli.models import fetch_openrouter_models
                        or_models = [mid for mid, _ in fetch_openrouter_models()]
                    except Exception:
                        or_models = []

                    for or_m in or_models:
                        variants = [
                            or_m,
                            f"openrouter/{or_m}",
                            f"oc/{or_m}"
                        ]
                        if or_m.endswith(":free"):
                            clean_name = or_m.replace("/", "-").replace(":", "-")
                            variants.append(f"oc/{clean_name}")
                            variants.append(clean_name)

                        for var in variants:
                            if var and var.lower() not in seen:
                                models.append(var)
                                seen.add(var.lower())

                    p["models"] = models
                    p["total_models"] = len(models)

            return results

        _ms_mod._orig_list_authenticated_providers_abelion = _orig_list_auth
        _ms_mod.list_authenticated_providers = _patched_list_auth
        logger.info("[abelion_core] Patched list_authenticated_providers for local custom providers")
    except Exception as e:
        logger.error("[abelion_core] Failed to patch list_authenticated_providers: %s", e)


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
    Register the unified abelion_core plugin.
    """
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

    # 5. Monkey Patch Core Systems for custom features (zero-core modification strategy)
    try:
        import agent.tool_dispatch_helpers as dispatch_helpers
        from agent.redact import redact_sensitive_text

        if not hasattr(dispatch_helpers, "_orig_make_tool_result_message"):
            dispatch_helpers._orig_make_tool_result_message = dispatch_helpers.make_tool_result_message

            def patched_make_tool_result_message(name, content, tool_call_id):
                if isinstance(content, str):
                    content = redact_sensitive_text(content)
                elif isinstance(content, list):
                    for part in content:
                        if (
                            isinstance(part, dict)
                            and part.get("type") == "text"
                            and isinstance(part.get("text"), str)
                        ):
                            part["text"] = redact_sensitive_text(part["text"])
                return dispatch_helpers._orig_make_tool_result_message(name, content, tool_call_id)

            dispatch_helpers.make_tool_result_message = patched_make_tool_result_message
            logger.info("[abelion_core] Patched make_tool_result_message for PII Redaction")
    except Exception as e:
        logger.error(f"[abelion_core] Failed to patch tool_dispatch_helpers: {e}")

    # 6. PII Redactor: kanban_db write functions
    try:
        from agent.redact import redact_sensitive_text
        _patch_kanban_db(redact_sensitive_text)
    except Exception as e:
        logger.error(f"[abelion_core] Failed to initialize kanban_db PII patch: {e}")

    try:
        import hermes_cli.tools_config as tools_config

        messaging_exists = any(ts[0] == "messaging" for ts in tools_config.CONFIGURABLE_TOOLSETS)
        if not messaging_exists:
            idx = len(tools_config.CONFIGURABLE_TOOLSETS)
            for i, ts in enumerate(tools_config.CONFIGURABLE_TOOLSETS):
                if ts[0] == "homeassistant":
                    idx = i
                    break
            tools_config.CONFIGURABLE_TOOLSETS.insert(idx, ("messaging", "📨 Cross-Platform Messaging", "send_message"))
            logger.info("[abelion_core] Injected 'messaging' toolset into CONFIGURABLE_TOOLSETS")
    except Exception as e:
        logger.error(f"[abelion_core] Failed to patch tools_config: {e}")

    try:
        import toolsets

        if "send_message" not in toolsets._HERMES_CORE_TOOLS:
            idx = len(toolsets._HERMES_CORE_TOOLS)
            for i, t in enumerate(toolsets._HERMES_CORE_TOOLS):
                if t == "ha_list_entities":
                    idx = i
                    break
            toolsets._HERMES_CORE_TOOLS.insert(idx, "send_message")
            logger.info("[abelion_core] Injected 'send_message' into _HERMES_CORE_TOOLS")

        if "messaging" not in toolsets.TOOLSETS:
            toolsets.TOOLSETS["messaging"] = {
                "description": "Cross-platform messaging: send messages to Telegram, Discord, Slack, SMS, etc.",
                "tools": ["send_message"],
                "includes": []
            }
            logger.info("[abelion_core] Injected 'messaging' into TOOLSETS")
    except Exception as e:
        logger.error(f"[abelion_core] Failed to patch toolsets: {e}")

    # 7. Fix /model command for local custom providers (e.g. 9Router 'local-localhost:20128')
    _patch_validate_requested_model()
    _patch_model_switch_is_custom()
    _patch_list_authenticated_providers()

    logger.info(
        "abelion_core plugin registered successfully. (Hierarchy removed in favor of native Kanban/Prompts)"
    )
