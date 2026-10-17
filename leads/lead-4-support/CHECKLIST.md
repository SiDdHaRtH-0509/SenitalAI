# Lead 4 Checklist — Support / QA / Demo

## Primary tasks
- [ ] Read shared project files and API contract. **Done when:** can identify each module owner and integration flow.
- [ ] Verify README/setup commands from a clean clone where possible. **Done when:** actual command results are recorded.
- [ ] Prepare a QA run sheet using `INTEGRATION_TESTING.md`. **Done when:** every test can be marked PASS/FAIL/NOT RUN with evidence.
- [ ] Verify sample video provenance/permission. **Done when:** the team knows where it came from and may use it.
- [ ] Check `.gitignore` and repository status for secrets/large private data. **Done when:** no credential or unapproved media is committed.
- [ ] Run health/event/dashboard end-to-end checks when integrated. **Done when:** failures have reproduction steps and owners.
- [ ] Maintain `TASK_BOARD.md` and blocker log. **Done when:** statuses reflect actual progress.
- [ ] Prepare concise demo script and sequence. **Done when:** every shown feature is working or clearly labelled replay.
- [ ] Capture real screenshots and backup recording. **Done when:** recording matches current build and has no secrets.
- [ ] Review final claims and limitations. **Done when:** no unsupported accuracy, IBM deployment or production claims remain.
- [ ] Commit support/docs changes and open PR. **Done when:** lead reviews changes.

## Secondary tasks
- [ ] Help a core owner reproduce a bug using exact logs and steps.
- [ ] Test clean restart and setup on a second machine if available.
- [ ] Verify README links point to existing files.

## Tertiary / optional
- [ ] Add an isolated health-check/test fixture only after the lead approves it.
- [ ] Improve presentation visuals only after end-to-end tests pass.

## Completion criteria
The setup and demo are reproducible, test outcomes are honest, blockers are assigned, and the final presentation reflects actual application behavior.
