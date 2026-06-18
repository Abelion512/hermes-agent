# Project Documentation Mandate

**EVERY AGENT AND DEVELOPER** editing this project MUST adhere to the following documentation standards. This is a foundational rule for maintaining the "Experience-Driven" architecture of Hermes Agent.

## 1. Documentation Requirements
- **Work Log**: Every session MUST be logged in `docs/abelion/notes/WORK_LOG.md`. Record goals, actions taken, and the current status.
- **Session Summaries**: Complex architectural discussions or research sessions MUST be summarized in `docs/abelion/agent-session/`. 
- **Change Traceability**: Every change must be traceable. Do not just "fix it"; explain "why" it was fixed and how it aligns with the core philosophy in `AGENTS.md`.

## 2. Methodology
- **Research -> Strategy -> Execution**: Follow this lifecycle for all changes.
- **Done means Done**: A task is only complete when it has been linted, built, and verified.

## 3. ATA Principle & Architectural Philosophy (MUST READ)
All agents operating in this repository MUST adhere to the following architectural guidelines dictated by the Project Lead (Abelion):
- **ATA (Amati, Tiru, Adopsi)**: Before building any custom tools, classes, or architecture (like sandboxes or hierarchy managers), you MUST observe existing open-source integrations in Hermes (e.g., `daytona`, `modal`, `honcho`, `kanban`). Do not reinvent the wheel. 
- **System Constraints > Prompt Engineering**: Relying solely on prompts to make the LLM juggle multiple personas or complex instructions leads to "Attention Deficit" and "Lost in the Middle" phenomena. Real architectural security and hierarchy must be enforced at the system/code level (Reverse-Engineering/State Machines), using tools like Hermes' native `Kanban` queues rather than deeply nested prompt wrappers.
- **Context-Aware Architecture ("Mobil vs Motor")**: Architecture is highly context-dependent. A multi-agent framework that holds 3 agents simultaneously in RAM is a "luxury car"—useless for a 4GB RAM "narrow alley" Linux VPS. Optimize for asynchronous, state-machine-driven execution (e.g., saving task states to SQLite and killing processes) to prevent Out of Memory (OOM) errors.

## 4. Reference Files
- `AGENTS.md`: Technical guide and contribution rubric.
- `docs/abelion/`: Primary research and session documentation.

*Failure to document changes is considered a violation of the project's integrity.*
- **Neat Tables**: All tables emitted by the LLM must be wrapped in ` ```table ` block codes (handled by `display_aesthetics` plugin).
- **Asa-Style Status**: Use structured status blocks for reports. Example:
  ```status
  Feature X    ✅ Completed
  Feature Y    🔄 In Progress
  ```
- **Diagrams**: Use `excalidraw` (JSON first) or `ascii-art`.
- **Excalidraw Aesthetic**: Prefer clean, hand-drawn styles.

*Failure to document changes is considered a violation of the project's integrity.*

## 5. Security Protocol: .env Access
- **ZERO TOLERANCE**: Agents MUST NEVER read, parse, or access `.env` files (or any file containing credentials) by default.
- **BUILT-IN BLOCK**: The `read_file` and `grep_search` tools are hardcoded to reject `.env` access (via `agent/file_safety.py`).
- **SHELL BYPASS BAN**: Agents MUST NOT use shell commands (e.g., `cat .env`, `grep token .env`) to bypass this restriction.
- **APPROVAL REQUIRED**: If an agent absolutely must inspect a `.env` file for debugging, it MUST explicitly ask the user for permission (e.g., "Minta /approve untuk membaca .env") sebelum menjalankan shell command untuk membacanya.
