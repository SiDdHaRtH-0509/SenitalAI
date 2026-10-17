# Lead 2 Checklist — Computer Vision

## Primary tasks
- [ ] Read project context, architecture and event contract. **Done when:** payload and ownership are understood.
- [ ] Verify sample video permission, format and path. **Done when:** team can legally use it and access is documented.
- [ ] Inspect Python/OS/architecture and existing model availability. **Done when:** chosen runtime is tested or a blocker is reported.
- [ ] Create/verify `cv-engine/` environment and requirements. **Done when:** setup steps are reproducible.
- [ ] Implement video reading. **Done when:** frames are read and invalid paths fail clearly.
- [ ] Integrate a compatible pretrained person detector. **Done when:** a sample frame produces a detection or documented fallback is activated.
- [ ] Implement one configurable zone. **Done when:** zone is visible/configurable and geometry is documented.
- [ ] Implement zone-entry logic. **Done when:** representative point and entry rule are deterministic.
- [ ] Add temporal confirmation. **Done when:** a single noisy frame does not immediately create an event.
- [ ] Add event cooldown/deduplication. **Done when:** continuous presence does not flood backend.
- [ ] Build event payload exactly as API contract. **Done when:** schema validation succeeds.
- [ ] POST event to backend. **Done when:** event appears in backend storage/dashboard.
- [ ] Add model/video/API error handling. **Done when:** failures are visible and recoverable.
- [ ] Commit and open PR. **Done when:** lead can review isolated CV changes.

## Secondary tasks
- [ ] Add CLI options for video path, zone config, camera ID and backend URL.
- [ ] Save a short test log showing generated event fields.
- [ ] Add a clearly labelled deterministic replay fallback.

## Tertiary / optional
- [ ] Add vehicle detection only if person/zone pipeline is already integrated.
- [ ] Add tracking only if needed to stabilize zone entry and time remains.

## Completion criteria
One authorized video produces a valid zone-entry event through the shared API, duplicate events are controlled, and setup/limitations are documented.
