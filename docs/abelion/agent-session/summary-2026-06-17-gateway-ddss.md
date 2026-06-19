# Session Summary: 2026-06-17 - Gateway Resilience & DDSS Architecture

## 1. Gateway Blackout Resolution & Env-Var Patch
- **Incident**: Hermes gateway crashed/looped due to multiple overlapping issues (missing `news.py` CLI module, redundant systemd services, invalid `SOUL.md` prefill config).
- **Core Fix**: Discovered that the gateway's `config.py` loader lacked the `_expand_env_vars` function present in the CLI loader. Agents failed to connect to Discord/Telegram because `${TELEGRAM_BOT_TOKEN_ASA}` was passed as literal text.
- **Action**: Surgically patched `gateway/config.py` to recursively expand env vars via regex (mirroring `cli.py`). Restarted `hermes-gateway-enami-asa` successfully connecting to Telegram, Discord, and WhatsApp.

## 2. Security Protocol Enforcement (.env Isolation)
- **Vulnerability**: Agents could potentially read `.env` and leak credentials to untrusted LLM providers.
- **Action**: Updated root `GEMINI.md` to establish a **ZERO TOLERANCE** policy for `.env` access.
- **Protocol**: Agents are hard-blocked by `file_safety.py`. Shell bypass (`cat .env`) is banned. Any required access mandates triggering a manual `/approve` from the user via the gateway.

## 3. "Inverted Clarify" (Mid-Stream Interruption)
- **Concept**: Free-tier/low-end models are prone to hallucination and brute-forcing when encountering errors or permission blocks.
- **Architecture**: Instead of relying on the model to call the `clarify` tool, the *system infrastructure* (wrapper) intercepts the error (e.g., Exit Code 1 or sensitive pattern match), pauses the LLM execution state, and sends an alert to Discord/Telegram.
- **Natural Language Override**: The user can reply with specific instructions (not just multiple-choice), which are injected back into the context, allowing the agent to resume execution without context collapse.

## 4. PII Redaction: Beyond Regex (Entropy & AST)
- **Limitation**: Standard regex in `redact.py` fails to catch unconventional proprietary secrets or algorithms.
- **Proposed Solution**: 
  1. **Shannon Entropy Analysis**: Block or mask strings with high randomness (entropy > 4.5) indicative of keys/passwords.
  2. **AST (Abstract Syntax Tree) Tracing**: Parse code structure rather than raw text to mask values assigned to sensitive variable names (e.g., `db_password`, `client_secret`) before sending to the LLM.

## 5. Catalog Bug Analysis (Missing 9router Models)
- **Symptom**: `hermes model` fails to list models from 9router (e.g., `mmf/mimo-auto`), unlike n8n which loads them fine.
- **Root Cause (By Data)**: Analyzed `hermes_cli/models.py`. Hermes relies on a static `_PROVIDER_MODELS` list by default. For the `custom` provider to perform a live fetch (`fetch_api_models`), it strictly requires the `api_base` parameter to be defined.
- **Fix**: The user's `config.yaml` had the `api_key` but omitted the `api_base` under `providers.custom`. Adding `api_base: https://[9router-url]/v1` will force Hermes to fetch the dynamic model list.

## 6. DDSS (Data-Driven Support System) Routing Matrix
- **Goal**: Optimize cost and API limits while protecting sensitive data.
- **Rate Limit Anatomy**:
  - *Layer 1 (Account/429)*: Limit on the 9router API key. Requires fallback to a different key/provider.
  - *Layer 2 (Upstream/529)*: Limit on the origin server (e.g., Google). Requires fallback to a different model on the same aggregator.
- **Context-Aware Routing**:
  - `GENERAL` Tasks -> Routed to free/cheap tiers (9router).
  - `SENSITIVE` Tasks -> Routed to trusted providers (Local Ollama or Paid OpenRouter). **Strictly no fallback to untrusted proxies.**
- **Note**: The full DDSS concept blueprint is saved separately in `docs/abelion/notes/DDSS_CONCEPT.md`.