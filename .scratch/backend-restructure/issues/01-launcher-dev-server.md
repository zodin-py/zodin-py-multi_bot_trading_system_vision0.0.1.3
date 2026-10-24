# 01: Launcher + Dev Server

**What to build:** A single `launcher.py` entry point that starts FastAPI on port 8000 and Angular Dev Server (`ng serve`) on port 4200 in parallel, with a 1-3 second delay to ensure FastAPI is ready before Angular starts. Ctrl+C stops both processes cleanly.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `launcher.py` created at backend root
- [ ] FastAPI started via `uvicorn` subprocess (or threading) on port 8000
- [ ] Angular Dev Server started via `subprocess.Popen(["ng", "serve"])` on port 4200
- [ ] 1-3 second delay between FastAPI start and `ng serve` start
- [ ] Shared shutdown event: Ctrl+C terminates both subprocesses gracefully
- [ ] `--dev` flag (default) and `--prod` flag (serves Angular build via FastAPI StaticFiles) — `--prod` can be stubbed for now
- [ ] Logging shows both server URLs on startup
- [ ] Works from project root: `python backend/launcher.py`