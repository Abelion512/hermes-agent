# Architecture Design: RSI & Experiential Learning System

## 1. Philosophy: Zero-Alpha & Experiential Learning
The primary objective of this architecture is to transition the agent from relying solely on its pre-trained LLM weights (Prompt Engineering) towards an **Experience-Driven Knowledge Base** (Experience Engineering).
Inspired by the AlphaGo Zero / Zero-Alpha paradigm, the agent learns by doing. Successes and failures in task execution are parsed and converted into local, persistent training data (Memories). The agent relies on its accumulated experience within the project or persona over its inherent pre-trained bias.

## 2. Persona-Based Memory Isolation
To prevent context collapse and hallucination across different domains, memory is heavily segregated.
- **Global Constraints:** Static system rules.
- **Persona Memory (`~/.config/hermes/profiles/`):** Separated memory profiles for different roles (e.g., `coding_agent.md`, `seo_agent.md`, `business_agent.md`).
- **Project Memory (`AGENTS.md` / `.plans/`):** Context strictly bound to the current working directory.
- **Mechanism:** When a specific persona is invoked, only its respective memory is loaded into the context window, keeping the Semantic Memory sharp, precise, and token-efficient.

## 3. Multi-Agent Fault Tolerance & Hierarchy
The system employs a hierarchical "Managed Agents" structure: **CEO Agent -> Division Agent -> Worker Agent**.
- **Execution Flow:** The CEO delegates tasks to specialized sub-agents.
- **Fault Tolerance & Error Handling:**
  - **Timeout/Crash:** If a sub-agent crashes, times out, or returns garbage, the CEO does not crash. It catches the exception.
  - **Fallback:** The CEO can retry the task with a fallback model, invoke a different sub-agent, or degrade gracefully.
  - **Feedback Loop:** The failure is logged into the sub-agent's training memory so the mistake is not repeated.
  - **Circuit Breaker:** Maximum of 3 retries for a failing task before the system pauses and escalates to the human user.

## 4. Interactive Resource Management (Codex-CLI Style)
Token exhaustion, Rate Limits, or API errors will no longer result in a hard crash.
- **Interactive Interrupt:** When limits are hit during long-running tasks (e.g., `/goal`), the loop pauses safely.
- **CLI Options Presented to User:**
  1. **Wait:** Hold the state until limits reset.
  2. **Switch Model:** Hot-swap the provider (e.g., from `Antigravity` to `Opencode`) and continue seamlessly.
  3. **Abort/Reset:** Drop the current context and start fresh.

## 5. Resource Efficiency (RAM & Caching)
Optimized for 4GB RAM Linux environments and Free-Tier proxy APIs (like 9router).
- **Garbage Collection:** Explicit `gc.collect()` hooks post-task to clear unreferenced memory.
- **Universal Caching:**
  - Support for **Anthropic Cache-Control** (`{"cache_control": {"type": "ephemeral"}}`).
  - Support for **OpenAI Prefix Caching**: The core System Prompt and initial history are strictly frozen (static). Dynamic variables (like timestamps) are pushed to the end of the prompt to ensure maximum cache hit rates across proxy providers.
- **Smart Compression:** Replaces naive truncation. Context is safely summarized without dropping critical facts (like URLs or error traces) marked by `<memory-context>` tags.
