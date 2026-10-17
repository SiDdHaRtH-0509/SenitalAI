# LinuxONE Compatibility Matrix — Fill During Event

Do not mark a component compatible based only on online claims; test the exact version/environment where possible.

| Component | Version/pin | Target architecture | Evidence/command | Status (verified/unverified/unsupported) | Fallback |
|---|---|---|---|---|---|
| OS/runtime | | | `uname -m`, OS release | | |
| Python | | | `python3 --version` | | |
| FastAPI/Uvicorn | | | install + run health endpoint | | |
| SQLite driver | | | create/write/read test | | |
| Node/Vite | | | `node --version`, build | | |
| OpenCV | | | import + read sample video | | |
| ML framework | | | import/inference test | | |
| Model weights | | | model load + inference | | |
| Container image (if any) | | `linux/s390x`? | inspect image manifest | | |

Record command outputs without secrets. If a package cannot run on s390x, use an approved compatible alternative, run inference on another permitted host and send structured events to the LinuxONE service, or use a clearly labelled replay fallback.
