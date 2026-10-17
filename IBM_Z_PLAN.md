# IBM Z / LinuxONE Integration Plan

Use the organizer-provided environment as the source of truth. Confirm access method, architecture, allowed runtimes, network rules, package sources, deployment evidence, and whether actual deployment is mandatory.

## Intended integration
A meaningful service such as event ingestion, risk evaluation, or audit/history may run on LinuxONE if supported. Computer vision can run on a compatible approved host if its model runtime is unavailable on s390x, sending only structured events to the service if permitted.

## Evidence labels
- **IMPLEMENTED:** actually deployed and exercised on the named IBM environment.
- **TESTED:** actual connection/test completed, scope stated.
- **PROPOSED:** architecture only; not deployed.
Never present a proposed design as implemented.

## Architecture-dependent checks
- `uname -m` on target.
- Python and Node versions supported by the environment.
- Wheels/native libraries for each pinned dependency.
- Container image has a `linux/s390x` manifest if container use is planned.
- Model runtime and weights are compatible and licensed.
- Browser-facing API URL is reachable and approved.

See `ENVIRONMENT_SETUP.md`, `LINUXONE_DEPLOYMENT.md`, and `INTEGRATION_TESTING.md`.
