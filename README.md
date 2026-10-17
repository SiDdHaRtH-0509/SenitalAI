# SentinelAI — IBM Z Datathon 2026 Repository

SentinelAI is a human-in-the-loop video event intelligence prototype for CCTV-style footage. It detects a small set of predefined observable events, converts them into structured records, applies transparent rule-based prioritization, and presents them to a human operator.

> **Scope:** a datathon prototype, not a validated operational border-surveillance system. A person entering a zone is an observable event, not evidence of malicious intent.

## Start here

**Repository name:** `sentinel-ai`  
**Default branch:** `main`  
**Status:** GitHub-ready starter scaffold; not a completed surveillance application.

1. Read `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, and `API_CONTRACT.md`.
2. Read `TEAM_ROLES.md` and the folder for your assigned lead under `leads/`.
3. Confirm the official Datathon rules for permitted AI assistance, code timing, pretrained models, external APIs, datasets, and IBM environment access.
4. Create/confirm the shared GitHub repository and branches.
5. Use `TASK_BOARD.md` as the live source of task status.

## Project roles
- **Overall Lead (user):** project architecture, shared contracts, backend/risk engine, integration decisions, final validation and submission.
- **Lead 1:** frontend and operator dashboard.
- **Lead 2:** computer vision and event generation.
- **Lead 3:** LinuxONE deployment and environment compatibility support.
- **Lead 4:** QA, documentation, sample-data checks and demo support.

This assigns one accountable owner to each workstream. The Overall Project Lead coordinates the four Leads, owns backend/API integration, and approves merges. Leads 1–4 own the workstreams listed in `TEAM_ROLES.md`.

## Target MVP
- One authorized prerecorded CCTV-style video.
- One existing pretrained person detector that is compatible with the available environment.
- One configured zone and a documented entry rule.
- Structured `RESTRICTED_ZONE_ENTRY` events.
- Backend event validation, storage and deterministic rule-based risk explanations.
- Dashboard event list, risk reasons, status and a clear connection indicator.
- Demonstrable, honest IBM LinuxONE integration according to the environment actually provided.

## Repository map
```text
sentinel-ai/
├── README.md
├── PROJECT_CONTEXT.md
├── ARCHITECTURE.md
├── API_CONTRACT.md
├── TEAM_ROLES.md
├── TASK_BOARD.md
├── EXECUTION_PLAN.md
├── ENVIRONMENT_SETUP.md
├── LINUXONE_DEPLOYMENT.md
├── INTEGRATION_TESTING.md
├── IBM_Z_PLAN.md
├── DEMO_SCRIPT.md
├── .env.example
├── .gitignore
├── leads/
│   ├── lead-1-frontend/
│   ├── lead-2-computer-vision/
│   ├── lead-3-linuxone/
│   └── lead-4-support/
├── backend/                  # Overall Lead creates/owns this module
├── frontend/                 # Lead 1
├── cv-engine/                # Lead 2
├── deploy/                   # Lead 3; create only as needed
├── tests/                    # shared tests; module owners own their tests
├── sample-data/              # keep large/private footage out of Git
└── docs/
```

## GitHub setup
Follow `GITHUB_SETUP.md` to initialize this folder as a Git repository and push it to GitHub. Use `CONTRIBUTING.md` for the branch/PR workflow.

## Development-to-deployment workflow
1. Clone the repository and create the assigned branch.
2. Create a supported local environment using `ENVIRONMENT_SETUP.md`.
3. Implement only your owned module and follow `API_CONTRACT.md`.
4. Test the module in isolation and record the actual result.
5. Push a small commit and open a pull request.
6. Overall Lead reviews and merges; run `INTEGRATION_TESTING.md`.
7. Follow `LINUXONE_DEPLOYMENT.md` only after confirming the actual IBM environment and architecture.
8. Rehearse `DEMO_SCRIPT.md`, keep a clearly labelled fallback, and submit according to official rules.

## Local startup (starter scaffold)
Backend:
```bash
cd backend
python -m venv .venv
# Activate the environment for your shell; see ENVIRONMENT_SETUP.md
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Computer vision:
```bash
cd cv-engine
python -m venv .venv
python -m pip install -r requirements.txt
python video_processor.py --help
```

The folders contain ownership notes and placeholders; implementation files must be added by the assigned lead. Do not claim the application is implemented merely because the repository scaffold exists.

## Security and repository hygiene
- Never commit `.env`, API keys, credentials, private keys, or unlicensed/private footage.
- Use `.env.example` for variable names only.
- Keep model weights and large video files out of Git unless explicitly approved.
- Do not expose secrets in screenshots or logs.
- Do not make unsupported claims about model accuracy, latency, threat probability, IBM deployment, or production readiness.

## LinuxONE caution
LinuxONE commonly uses `s390x`/IBM Z architecture. Do not assume x86-64 wheels, model runtimes, native libraries, or container images work on it. Check `uname -m`, Python/Node versions, wheel availability, image manifests and the actual organizer-provided environment before selecting a deployment path. See `ENVIRONMENT_SETUP.md` and `LINUXONE_DEPLOYMENT.md`.

## Compliance
This repository is a planning and documentation starter kit. Follow the official IBM Z Datathon rules for when implementation may begin, what code or assets may be reused, AI assistant usage, and submission evidence. Do not prebuild or misrepresent implementation work.
