# Lead 3 Checklist — LinuxONE / Environment

## Primary tasks
- [ ] Read official organizer instructions and confirm access method. **Done when:** allowed runtime, network and deployment requirements are recorded.
- [ ] Inspect actual target OS and architecture. **Done when:** OS release and `uname -m` outputs are saved.
- [ ] Record Python, Node, Git, and available container/deployment tools. **Done when:** versions/availability are documented.
- [ ] Obtain pinned requirements from backend and CV owners. **Done when:** compatibility audit uses real versions, not guesses.
- [ ] Audit native dependencies and ML runtimes for s390x support. **Done when:** each dependency is marked verified, unverified or unsupported with evidence.
- [ ] Check container image architecture manifests if containers are used. **Done when:** `linux/s390x` support is verified or a fallback is documented.
- [ ] Create `docs/linuxone-compatibility.md`. **Done when:** it lists component, version, target, verification and fallback.
- [ ] Update deployment docs/commands to match actual access method. **Done when:** no assumed service or tool is presented as guaranteed.
- [ ] Test deployment of the agreed component if access allows. **Done when:** actual health/event request succeeds and evidence is recorded.
- [ ] Document which components run on LinuxONE vs another approved host. **Done when:** architecture diagram and report agree.
- [ ] Commit docs/scripts and open PR. **Done when:** lead reviews a scoped diff.

## Secondary tasks
- [ ] Validate browser-facing API URL, allowed port and routing with organizers.
- [ ] Add rollback/restart instructions if a real deployment path exists.
- [ ] Help debug architecture/package failures without rewriting module code.

## Tertiary / optional
- [ ] Add container build files only if organizer environment supports containers and dependencies have compatible images.
- [ ] Add process manager/service unit only if allowed and necessary.

## Completion criteria
The team has an evidence-backed deployment path for the actual LinuxONE environment, an architecture compatibility matrix, and an honest report of what was and was not deployed.
