# Dynamic Model Routing & Context-Aware Fallback (DDSS Concept)
*Saved for future implementation.*

## Goal
Implement a routing system that handles API rate limits while strictly enforcing data security (topic sensitivity).

## Architecture

1.  **Evaluator (Pre-flight):**
    *   Scans incoming prompt and context.
    *   Classifies as `SENSITIVE` (e.g., contains database schema, reads `.env` via approval, involves proprietary algorithms).
    *   Classifies as `GENERAL` (e.g., boilerplate code, log summarization).

2.  **The Routing Matrix:**
    *   **GENERAL Context:**
        *   Primary: Aggregator (9router) / Free-tier model.
        *   Fallback 1: Alternative model on 9router.
        *   Fallback 2: OpenRouter (Auto-router).
    *   **SENSITIVE Context:**
        *   Primary: Trusted Provider (e.g., local Ollama or paid Anthropic/OpenAI via OpenRouter).
        *   Fallback: **NO FALLBACK TO UNTRUSTED PROXIES**.
        *   Action on Failure: Pause execution, send Inverted Clarify to Discord: "Sensitive task stalled due to Trusted Provider limits. Wait or Abort."

3.  **Limit Handling (OpenRouter/9router):**
    *   Differentiate between Account Limit (e.g., 429 on the aggregator key) and Upstream Limit (e.g., 529 on the specific model's server).
    *   Account Limit -> Switch API Key / Provider.
    *   Upstream Limit -> Switch Model within the same aggregator.
