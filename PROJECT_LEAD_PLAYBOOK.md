# Overall Lead Playbook

## Your ownership
You are the architecture and integration authority and own `backend/`, API contracts, risk engine, merge decisions, end-to-end validation and final submission. Lead 1 owns frontend, Lead 2 owns computer vision, Lead 3 owns LinuxONE environment/deployment, and Lead 4 owns QA/documentation/demo support.

## Before parallel work
- [ ] Confirm official implementation window and AI/tool rules.
- [ ] Confirm LinuxONE access, architecture, permitted services and deployment requirements.
- [ ] Create GitHub repository and add collaborators.
- [ ] Commit shared root docs before Lead work begins.
- [ ] Create branches: `lead/backend-integration`, `lead-1/frontend`, `lead-2/cv-engine`, `lead-3/linuxone`, `lead-4/support`.
- [ ] Assign each person their dedicated folder and prompt.
- [ ] Freeze `API_CONTRACT.md` and explain how contract changes are approved.

## During build
- [ ] Implement backend health/create/list/stats endpoints and deterministic risk engine.
- [ ] Require small commits and early PRs.
- [ ] Review lead changes; never merge blindly.
- [ ] At hour 6 require backend sample event, frontend fixture rendering and CV video read.
- [ ] At hour 10 require CV POST to backend and frontend fetch.
- [ ] At hour 12 freeze optional features if end-to-end demo is not working.
- [ ] Track LinuxONE evidence separately from local success.
- [ ] Keep a known-good commit/tag for demo rollback.

## Pull request review
- Does it stay inside owned paths?
- Does it preserve the API contract?
- Are dependencies necessary and compatible?
- Are secrets or private data included?
- Are tests actually run and results recorded?
- Does it introduce an unapproved feature or unsupported claim?

## Final acceptance
- [ ] Fresh start follows README.
- [ ] Event is generated or clearly labelled replayed.
- [ ] Event is stored and risk reasons are returned.
- [ ] Dashboard shows backend output.
- [ ] LinuxONE deployment is accurately described with evidence.
- [ ] Demo and backup work.
- [ ] Repository is clean and submission format is correct.
