# Session Summary: 2026-06-17 - Shift to Kanban Architecture

## Context & Pain Points
This session focused on resolving structural and operational flaws in the previous Multi-Agent implementation:
1.  **RAM Limitations (4GB constraint):** The previous nested delegation approach (`CEO -> Division -> Worker` running simultaneously) caused massive memory overhead.
2.  **Prompt vs. System Constraints:** Acknowledged that complex prompt engineering (expecting one agent to juggle roles/subagents flawlessly) is weaker than enforcing behavior via system architecture (Reverse-Engineering).
3.  **IDE Context Bloat:** Zed IDE's failure to persist chat UI across restarts led to bloated manual log dumps (`agent-session/`), consuming unnecessary tokens.

## Decisions Made (ATA Principle applied)
-   **Abandon Custom Hierarchy:** The over-engineered `abelion_core_delegate` tool in `hierarchy.py` was deleted. We will adhere to the **ATA (Amati, Tiru, Adopsi)** principle by utilizing Hermes' native tools rather than reinventing the wheel.
-   **Adopt Kanban for Multi-Agent:** We are shifting to Hermes' native SQLite-backed Kanban system. This transforms the architecture into an **Asynchronous State Machine**:
    -   CEO creates a task on the board.
    -   CEO process dies (freeing RAM).
    -   Gateway Dispatcher wakes a specialized Worker Profile.
    -   Worker completes the task and dies.
    -   *Result:* Only one agent process runs at a time, making it highly stable for 4GB RAM.
-   **Disable Docker Sandbox Rule:** For vibe-coding flexibility, host terminal access is required. The mandatory Docker sandbox rule in `Security.md` is deprecated in favor of Secret Redaction and Prompt Injection guards.
-   **Worker Setup via Script:** Agreed to use a reproducible bash script to scaffold Worker Profiles (cloning API keys from the default profile and injecting specific role descriptions for Kanban routing).

## Next Steps
-   Write and execute `scripts/setup_workers.sh` to generate the foundational Worker Profiles (`worker-engineer`, `worker-research`).
