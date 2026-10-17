# Integration Testing Checklist

Mark a box only after the test is actually performed. Record commit hash, environment, result, and a brief log in the team notes.

## A. Repository and environment
- [ ] Fresh clone succeeds for all active developers.
- [ ] Each branch contains only its owner's intended changes.
- [ ] No `.env`, keys, passwords, private footage or large model weights are committed.
- [ ] Python/Node/runtime versions and machine architecture are recorded.
- [ ] LinuxONE compatibility has been checked for native packages and images.

## B. Backend
- [ ] `GET /api/health` returns a healthy response.
- [ ] Valid event POST returns stored event and risk result.
- [ ] Invalid confidence/timestamp/payload is rejected with a useful 4xx.
- [ ] Duplicate `event_id` does not create duplicate records.
- [ ] `GET /api/events` returns stored events newest first.
- [ ] `GET /api/stats` matches stored records.
- [ ] Risk score includes reasons and does not claim threat probability.
- [ ] Database survives the expected restart, if persistence is required.

## C. Computer vision
- [ ] Authorized video opens and frames are read.
- [ ] Detector/model is loaded successfully in the declared environment.
- [ ] Zone geometry is visible and configured correctly.
- [ ] Confirmed zone entry creates the expected event.
- [ ] Continuous presence does not flood the API due to missing cooldown.
- [ ] Timestamp and confidence semantics match the contract.
- [ ] Missing model/invalid video/backend outage produces a clear error.
- [ ] Replay fallback is visibly labelled and uses the same API contract.

## D. Frontend
- [ ] Dashboard loads without console-breaking errors.
- [ ] Real backend events appear after refresh/poll.
- [ ] Risk score, reasons, status and timestamps match API data.
- [ ] Empty/loading/error/disconnected states work.
- [ ] Browser-facing API URL is configured correctly.
- [ ] Acknowledgement control is shown only if the endpoint exists.
- [ ] Simulated/replay data is labelled.

## E. End-to-end
- [ ] Start all required components from documented commands.
- [ ] Trigger or replay one event.
- [ ] Verify event reaches API and is stored.
- [ ] Verify risk reasons and score appear in the dashboard.
- [ ] Restart the application and repeat.
- [ ] Capture a reproducible run log and screenshots.

## F. LinuxONE
- [ ] Actual target architecture and OS are recorded.
- [ ] Required service runs on the intended target.
- [ ] Architecture-compatible package/image use is verified.
- [ ] Approved network path works.
- [ ] Health check and event POST succeed against the deployed service.
- [ ] Actual deployment evidence is saved without credentials.
- [ ] Components running elsewhere are explicitly identified.

## G. Submission
- [ ] README commands match the tested build.
- [ ] Demo has been rehearsed at least twice.
- [ ] Backup recording/fixtures are ready.
- [ ] Claims are supported by logs or observable behavior.
- [ ] Limitations and human-in-the-loop design are explained.
- [ ] Official submission requirements are checked.

## Result log template
| Test | Environment/commit | Result (PASS/FAIL/NOT RUN) | Evidence/notes |
|---|---|---|---|
| | | | |
