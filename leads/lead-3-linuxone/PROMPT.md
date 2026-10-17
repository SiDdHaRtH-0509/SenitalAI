# Initial Master Prompt — Lead 3: LinuxONE / Environment

Read root `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `IBM_Z_PLAN.md`, `ENVIRONMENT_SETUP.md`, `LINUXONE_DEPLOYMENT.md`, `INTEGRATION_TESTING.md`, and your `CHECKLIST.md`.

## Goal
Make deployment practical and truthful for the actual IBM LinuxONE environment. First inspect organizer-provided access and rules; never assume a particular shell, cloud, container engine, IDE or service is available.

## Ownership
Own deployment/configuration documentation and `deploy/` only. Do not change backend/frontend/CV application logic without the owner's approval.

## Required
- Record actual OS, `uname -m`, runtime versions and available tools.
- Check architecture-sensitive dependencies, Python wheels/native libraries, model runtime, and container image manifests for `linux/s390x`.
- Coordinate with module owners to get their actual pinned requirements.
- Create `docs/linuxone-compatibility.md` with verified/unverified status and fallback.
- Prepare only deployment scripts/config that match the actual environment and official rules.
- Verify approved network path and health/event API if access is available.
- Capture real evidence without secrets.
- Distinguish IMPLEMENTED, TESTED and PROPOSED components.

If ML inference cannot run on s390x, evaluate an approved separate inference host that sends structured events to the LinuxONE backend, or a clearly labelled replay fallback. Do not assume x86-64 binaries/images will run. Do not claim deployment unless tested. Use `NEXT_TASK_PROMPT.md` after each completed task to ask your AI for the next bounded task based on the repository and remaining time.
