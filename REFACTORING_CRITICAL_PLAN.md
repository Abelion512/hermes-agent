# Critical Refactoring Plan - Hermes Agent

## Executive Summary

This document outlines the critical refactoring priorities for the Hermes Agent codebase, focusing on the three largest monolithic files:

1. **`gateway/run.py`** - 21,815 lines (GatewayRunner class + 50+ helper functions)
2. **`cli.py`** - 17,685 lines (HermesCLI class + ChatConsole + 100+ helpers)  
3. **`hermes_cli/main.py`** - 16,152 lines (CLI command handlers)

---

## 🔴 CRITICAL PRIORITY

### 1. Break Down `gateway/run.py` (21K lines)

**Current Structure:**
- Single `GatewayRunner` class (lines 1951-21133, ~19K lines)
- 50+ module-level helper functions scattered throughout
- Mixed concerns: message handling, session management, agent lifecycle, platform adapters

**Refactoring Strategy:**

#### Phase 1A: Extract Message Handling Pipeline (`gateway/message_handler.py`)
Extract methods related to message processing:
- `_handle_message()` (line 7998)
- `_handle_message_with_agent()` (line 9566)
- Helper functions: `_build_gateway_agent_history()`, `_wrap_current_message_with_observed_context()`, etc.

#### Phase 1B: Extract Session Management (`gateway/session_manager.py`)
Extract session-related logic:
- Session creation/retrieval
- Session state management
- History offset preservation
- Model overrides

#### Phase 1C: Extract Agent Lifecycle (`gateway/agent_lifecycle.py`)
Extract agent management:
- Agent cache management (_agent_cache)
- Agent instantiation and configuration
- Running agents tracking
- Interrupt handling

#### Phase 1D: Extract Command Handlers (`gateway/commands/`)
Extract slash command implementations:
- `/new`, `/reset`, `/model`, `/reasoning`, `/queue`, etc.
- Move to `gateway/commands/new.py`, `gateway/commands/model.py`, etc.

#### Phase 1E: Extract Utility Functions (`gateway/utils/`)
Group helper functions by concern:
- `gateway/utils/error_handling.py` - Error detection, redaction
- `gateway/utils/timestamp.py` - Timestamp coercion, formatting
- `gateway/utils/media.py` - Media handling, placeholders
- `gateway/utils/config.py` - Config loading, resolution

### 2. Break Down `cli.py` (17K lines)

**Current Structure:**
- `HermesCLI` class (starts line 3236)
- `ChatConsole` class (starts line 2958)
- `_SkinAwareAnsi` class (starts line 1993)
- 100+ module-level helper functions

**Refactoring Strategy:**

#### Phase 2A: Complete TUI Module (`hermes_cli/tui/`)
Already started, needs completion:
- `hermes_cli/tui/console.py` - ChatConsole class
- `hermes_cli/tui/input.py` - Fixed input area, key bindings
- `hermes_cli/tui/rendering.py` - Output rendering, streaming
- `hermes_cli/tui/skin.py` - _SkinAwareAnsi, color engine

#### Phase 2B: Extract CLI Commands (`hermes_cli/commands/`)
Already has directory, populate with:
- `hermes_cli/commands/slash_commands.py` - /new, /reset, /model, etc.
- `hermes_cli/commands/session_commands.py` - /history, /summary, etc.
- `hermes_cli/commands/config_commands.py` - /config, /profile, etc.

#### Phase 2C: Extract Core Logic (`hermes_cli/core/`)
Already has `formatting.py`, expand:
- `hermes_cli/core/agent_wrapper.py` - AIAgent integration
- `hermes_cli/core/worktree.py` - Worktree management
- `hermes_cli/core/session_db.py` - Session database operations
- `hermes_cli/core/clipboard.py` - Clipboard abstraction

#### Phase 2D: Extract Utilities (`hermes_cli/utils/`)
Create new directory:
- `hermes_cli/utils/formatting.py` - Duration, token formatting
- `hermes_cli/utils/markdown.py` - Table alignment, markdown processing
- `hermes_cli/utils/path.py` - Path normalization, Git Bash handling
- `hermes_cli/utils/logging.py` - Logging setup, quiet mode

### 3. Break Down `hermes_cli/main.py` (16K lines)

**Refactoring Strategy:**

#### Phase 3A: Extract Command Groups
- `hermes_cli/commands/auth_commands.py` - Authentication commands
- `hermes_cli/commands/model_commands.py` - Model selection, switching
- `hermes_cli/commands/profile_commands.py` - Profile management
- `hermes_cli/commands/plugin_commands.py` - Plugin management

---

## 🟡 HIGH PRIORITY

### 4. Eliminate Circular Dependencies

**Current Issues:**
- `gateway/run.py` imports from `cli.py` (lines 15665, 16029)
- `hermes_cli/callbacks.py` imports from `cli.py` (lines 24, 203)
- `hermes_cli/main.py` imports from `cli.py` (lines 1793, 2135)

**Solution:**
- Create `hermes_cli/shared_config.py` for shared configuration
- Move `save_config_value()`, `CLI_CONFIG` to shared module
- Use dependency injection instead of direct imports

### 5. Standardize Error Handling

**Current State:** Inconsistent error handling patterns

**Solution:**
- Create `hermes_cli/exceptions.py` with custom exceptions:
  ```python
  class HermesError(Exception): pass
  class ConfigError(HermesError): pass
  class SessionError(HermesError): pass
  class AgentError(HermesError): pass
  class PlatformError(HermesError): pass
  ```
- Replace generic `try/except Exception` with specific handlers
- Add error context and user-friendly messages

### 6. Add Systematic Type Hints

**Current Coverage:** ~30%

**Target:** 90%+ coverage

**Approach:**
- Add type hints to all public APIs first
- Use `typing.Optional`, `typing.Union`, `typing.Dict`, etc.
- Run mypy in CI to enforce

---

## 🟢 MEDIUM PRIORITY

### 7. Consolidate Duplicate Code

**Duplicates Found:**
- Formatting utilities (duration, tokens)
- Clipboard operations
- Table rendering
- Markdown processing

**Solution:**
- Centralize in `hermes_cli/utils/`
- Create single source of truth for each utility

### 8. Improve Test Coverage

**Current State:** Limited unit tests

**Solution:**
- Write unit tests for extracted functions
- Mock external dependencies (LLM APIs, platforms)
- Add integration tests for critical paths

### 9. Standardize Plugin Architecture

**Current State:** Ad-hoc plugin system

**Solution:**
- Define clear plugin interfaces
- Document plugin contract
- Add plugin validation

---

## 📋 IMPLEMENTATION ORDER

### Week 1-2: Gateway Refactoring
1. Extract `gateway/utils/` (lowest risk, immediate benefit)
2. Extract `gateway/message_handler.py`
3. Extract `gateway/session_manager.py`
4. Extract `gateway/agent_lifecycle.py`

### Week 3-4: CLI Refactoring
5. Complete `hermes_cli/tui/` module
6. Extract `hermes_cli/utils/`
7. Populate `hermes_cli/commands/`
8. Expand `hermes_cli/core/`

### Week 5: Cleanup
9. Eliminate circular dependencies
10. Add error handling framework
11. Add type hints to extracted modules

### Week 6: Testing & Documentation
12. Write unit tests
13. Update documentation
14. Run full test suite

---

## ✅ SUCCESS METRICS

- [ ] No file exceeds 5,000 lines
- [ ] All classes under 2,000 lines
- [ ] Zero circular dependencies
- [ ] 90%+ type hint coverage
- [ ] 80%+ test coverage
- [ ] All existing tests pass
- [ ] No regression in functionality

---

## 🚀 QUICK WINS (Start Immediately)

These can be done in parallel with minimal risk:

1. **Extract formatting utilities** - Already started in `hermes_cli/core/formatting.py`
   - Move `format_duration_compact`, `format_token_count_compact`, `strip_reasoning_tags`
   - Update imports in `cli.py` and `gateway/run.py`

2. **Create unified clipboard module** - `hermes_cli/utils/clipboard.py`
   - Consolidate clipboard operations from multiple locations

3. **Extract table utilities** - `hermes_cli/utils/tables.py`
   - `is_table_divider`, `looks_like_table_row`, `realign_markdown_tables`

4. **Add pre-commit hooks**
   - ruff (linting)
   - black (formatting)
   - mypy (type checking)

---

## 📝 NOTES

- Maintain backward compatibility during refactoring
- Use deprecation warnings for moved/renamed APIs
- Keep git history clean with focused commits
- Test after each extraction step
- Document all public APIs
