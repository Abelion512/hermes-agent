# Session Summary: 2026-06-19 — Branch Cleanup & Plugin Restructure

## Objective

Clean up the `implement-research-z.ai` branch:
1. Extract upstream-viable security fix into its own PR branch.
2. Revert personal/local-only edits from 5 core Hermes files.
3. Strip monkey-patches and toolset injection from `abelion_core` plugin.
4. Use proper Hermes hooks/middleware instead.

## Deliverables

### PR Branch: `fix/security-mcp-bootstrap-shell-injection`
- **Fix**: `hermes_cli/mcp_catalog.py:_run_bootstrap` used `subprocess.run(cmd, shell=True)` — shell injection from malicious MCP manifests.
- **Fix**: Swap to `shlex.split` + `shell=False`, split `&&` chains into sequential calls.
- **Tests**: `TestRunBootstrapShellHardening` class (5 tests) in `tests/hermes_cli/test_mcp_catalog.py`.
- **Commit**: `40a991698`
- **Status**: Ready for upstream PR. 2 files changed (+142/-7).

### Core Revert (implement-research-z.ai)
- **Reverted**: PII redaction injection in `tools/memory_tool.py`, `agent/tool_dispatch_helpers.py`, `tools/session_search_tool.py`.
- **Reverted**: `_expand_env_vars` in `gateway/config.py`.
- **Reverted**: `plugins.abelion_core.health` import in `acp_adapter/server.py`.
- **Commit**: `b9bf5a95e`

### Plugin Cleanup (abelion_core)

#### Removed (monkey-patches):
- `_patch_kanban_db` — PII redaction via function replacement on `hermes_cli.kanban_db` module.
- `_patch_validate_requested_model` — local provider normalization hack.
- `_patch_model_switch_is_custom` — belt-and-suspenders for model switch.
- `_patch_discord_model_picker_view` — Discord pagination via method replacement.
- `_patch_list_authenticated_providers` — 9router model injection + OpenRouter model population.
- `patched_make_tool_result_message` — monkey-patch on `agent/tool_dispatch_helpers.py`.
- Toolset injection: `CONFIGURABLE_TOOLSETS` and `TOOLSETS` / `_HERMES_CORE_TOOLS` patching.

#### Fixed (paths):
- `reflection.py`: Hardcoded `/media/abelion/.../docs/abelion/reflections` → `get_hermes_home() / "abelion" / "reflections"`.
- `dataset_generator.py`: Hardcoded `/media/abelion/.../OlivXOS/data_chat` → `get_hermes_home() / "abelion" / "data_chat"`.
- `obsidian_exporter.py`: Hardcoded `/home/abelion/Downloads/HermesVault` → `get_hermes_home() / "abelion" / "obsidian_vault"`.
- `health.py`: Removed `_find_agent_on_stack` (no longer exists).

#### Kept (valid hooks/middleware/tools):
- `pre_tool_hook`: Loop detection, circuit breaker, RAG iteration cap, RAM guard.
- `pre_llm_hook`: Model health check + RAM warning injection.
- `post_llm_call`: `cache_messages` + link tracking.
- `on_session_end`: `record_reflection` → JSON file + FTS5 + Obsidian export.
- `optimize_caching` middleware: Prefix stability + Anthropic cache markers + RAM truncation.
- Tools: `abelion_test_model` (health check), `recall_experience` (FTS5 + LLM reranking).

- **Test**: Removed 8 PII redaction tests, renumbered remaining 22. 21 pass, 1 skip.
- **Commit**: `780f88839`

## Verification
- 21/22 abelion plugin tests pass.
- Working tree clean on both branches.
- No remaining references to removed functions in plugin directory.
- No hardcoded absolute paths remain in plugin files.
