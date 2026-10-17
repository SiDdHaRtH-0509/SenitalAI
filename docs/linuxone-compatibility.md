# LinuxONE Compatibility Matrix — Empirical Verification Results

**Project:** SentinelAI  
**Verification Date:** October 17, 2026  
**Target Architecture:** IBM LinuxONE (`s390x`, Big-Endian)  
**Host Environment:** Windows 11 AMD64 (WSL2 Docker with QEMU binfmt s390x emulation)  

---

## 1. Verified Compatibility Matrix

| Component | Target Architecture | Pin / Version | Command / Verification Evidence | Empirical Status | Deployment Strategy |
|---|---|---|---|---|---|
| **OS / Container Runtime** | `linux/s390x` | Debian GNU/Linux 13 (trixie) (glibc 2.41) | `cat /etc/os-release`, `uname -m` $\to$ `s390x`, `sys.byteorder` $\to$ `big` | **VERIFIED (QEMU Emulation)** | Base image `python:3.11-slim` (`linux/s390x`) under Docker Desktop QEMU `binfmt_misc` user-space emulation |
| **Physical IBM Hardware** | `s390x` | IBM z16 / LinuxONE III/IV | N/A (no physical mainframe hardware available in dev environment) | **UNVERIFIED** | Physical hardware compatibility unverified; validated via QEMU user-space emulation |
| **Python Runtime** | `s390x` | Python 3.11.17 | `python3 -c "import platform, sys; print(platform.machine(), sys.byteorder)"` $\to$ `s390x big` | **VERIFIED** | Native s390x CPython interpreter |
| **Node.js Runtime** | `s390x` | Node.js v20.20.2 | `docker run --rm --platform linux/s390x node:20-slim node -v` $\to$ `v20.20.2` (Not installed in backend image) | **VERIFIED (Standalone)** | Official Node.js s390x binaries |
| **FastAPI / Starlette** | `s390x` | 0.110.0+ / 0.143.3 | `pytest app/tests/ -v` (55 passed, 2 skipped, 0 failed) | **VERIFIED** | Pure Python wheel (`py3-none-any.whl`) |
| **Uvicorn ASGI Server** | `s390x` | 0.54.0 | Compiled `uvloop` & `httptools` wheels on s390x | **VERIFIED** | `uvicorn-0.54.0` with `httptools` / `uvloop` |
| **Pydantic / pydantic-core** | `s390x` | 2.14.1 / 2.50.1 | Downloaded `pydantic_core-2.50.1-...-manylinux2014_s390x.whl` | **VERIFIED** | Pre-built official manylinux s390x wheel on PyPI |
| **SQLAlchemy ORM** | `s390x` | 2.1.5 | `pytest app/tests/test_persistence.py` passed | **VERIFIED** | Pure Python wheel (`py3-none-any.whl`) |
| **SQLite3 Storage Engine** | `s390x` | Debian `sqlite3` + WAL | Data survives container restarts; foreign keys & WAL verified | **VERIFIED** | Native s390x libsqlite3 C library |
| **HTTPX / PyJWT** | `s390x` | 0.28.1 / 2.15.1 | Authenticated test client & JWT signing verified | **VERIFIED** | Pure Python wheels |
| **PyTorch (`torch`)** | `s390x` | 2.x | `pip install --dry-run torch` $\to$ `from versions: none` | **UNSUPPORTED on PyPI** | No pre-built s390x wheels on standard PyPI |
| **Ultralytics YOLOv8** | `s390x` | 8.x | Blocked by missing `torch` dependency on PyPI | **UNSUPPORTED on PyPI** | Run on edge workstation; stream events to s390x |
| **OpenCV (`opencv-python`)**| `s390x` | 4.x | No s390x wheel; requires compiling 82MB source tarball | **IMPRACTICAL via pip** | Use Debian `python3-opencv` or run CV on edge |
| **MediaMTX RTSP Gateway** | `linux/amd64` | v1.21.2 | `rtsp://127.0.0.1:8554/live/north_ridge` stream ingested | **VERIFIED** | Edge streaming proxy |
| **Frontend Production Build** | Browser / Nginx | Vite 5.4.21 / React 18 | `npm run build` $\to$ `dist/` (built in 2.45s) | **VERIFIED** | Hosted on edge / web tier pointing to s390x API |

---

## 2. Architectural Conclusion

In alignment with `LINUXONE_DEPLOYMENT.md` and `IBM_Z_PLAN.md`, SentinelAI operates in a **Distributed Hybrid Architecture**:
- **Central LinuxONE Node (s390x):** Hosts the FastAPI REST API, rule-based risk evaluation engine, SQLite persistence, cryptographic SHA-256 audit chaining, and operator triage endpoints.
- **Surveillance Edge Node (x86_64 / Jetson / Station):** Ingests live RTSP video feeds via `RTSPVideoSource`, runs `YOLOv8n` deep learning person detection and polygon ray-casting incursion math, and transmits authenticated `SecurityEvent` JSON to the central LinuxONE backend via HTTP 201/409.

### Explicit Operational Boundaries & Limitations
1. **Physical IBM LinuxONE Hardware:** **UNVERIFIED.** Testing was executed in an authentic `linux/s390x` container using Docker Desktop QEMU `binfmt_misc` user-space emulation on a Windows 11 host. Physical IBM z16/LinuxONE III/IV mainframes were not accessible.
2. **Native YOLO on s390x:** **UNSUPPORTED on PyPI.** Standard PyPI provides no pre-compiled `torch` wheels for `s390x` (`from versions: none`). Therefore, deep learning inference must execute on the edge node.
3. **Physical CCTV Hardware:** **UNVERIFIED.** Testing was performed against a live RTSP MediaMTX H.264 server streaming real multi-person surveillance footage. While compliant with RTSP/RTP standards, physical RTSP camera hardware interoperability must be confirmed per camera model.
