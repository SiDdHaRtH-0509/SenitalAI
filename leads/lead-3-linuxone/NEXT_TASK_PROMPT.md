# Request the Next Task Prompt — LinuxONE Environment and Deployment

Copy the prompt below into the same AI coding assistant you use for this project after completing your current assigned task.

---
You are continuing your assigned role for SentinelAI. First inspect the current repository and read `PROJECT_CONTEXT.md`, `API_CONTRACT.md`, `TASK_BOARD.md`, and `leads/lead-3-linuxone/CHECKLIST.md`. Inspect Git status and recent commits; do not assume prior work succeeded.

My role: LinuxONE Environment and Deployment.
My branch: `lead-3/linuxone`.
My owned paths: deploy/, ENVIRONMENT_SETUP.md, LINUXONE_DEPLOYMENT.md, docs/linuxone-compatibility.md.
Dependencies: Needs actual organizer-provided access and the stack/dependency declarations from owners. Does not rewrite app logic.

Identify the next highest-priority incomplete task from my checklist and the shared task board, based on the current repository state and remaining time. Do not ask me to restate the project. Before proposing work, verify that the task is not already completed and does not overlap another lead's ownership.

Return a task-specific implementation prompt that includes:
1. exact objective and acceptance criteria;
2. files allowed to inspect/modify;
3. files that must not be changed;
4. dependencies and API contracts to preserve;
5. ordered implementation steps;
6. tests/commands to run and evidence to report;
7. fallback if blocked;
8. a requirement to inspect existing code and avoid overwriting work;
9. a short handoff format: changed files, tests actually run/results, known limitations, next blocker.

Choose the smallest task that advances the end-to-end prototype. Do not add optional features while the core video/event/risk/dashboard path is incomplete. Do not claim tests passed unless run. Follow the official Datathon rules and do not invent IBM deployment status.
---

After the AI generates the task-specific prompt, review it against the shared contracts before authorizing implementation.
