# ShadowBox — Supervisor Handoff Report

**Date:** 2026-07-11
**Repo:** https://github.com/jb8250/shadowbox

---

## What Is ShadowBox?

ShadowBox is a **self-contained anonymous browsing workspace** for macOS. The goal is a single desktop app that:

1. **Launches a disposable, Tor-routed browser** — an Ungoogled Chromium container that routes all traffic through Tor
2. **Provides a control panel UI** — start/stop the workspace, rotate your identity (new Tor circuit), purge all data, toggle persistence
3. **Runs fully locally** — everything runs in Docker containers on your machine via Colima, no cloud dependencies
4. **Wraps it in a native macOS app** — built with Tauri (Rust + web UI) so it feels like a real desktop application, not a terminal tool

Think of it as a "burner browser" for your Mac — click a button, get a clean anonymous browsing session, click another button and everything disappears.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  Tauri Desktop App (Rust shell)             │
│  ┌───────────────────────────────────────┐  │
│  │  React/TypeScript UI (control panel)  │  │
│  └──────────────┬────────────────────────┘  │
│                 │ HTTP (localhost:4321)      │
│  ┌──────────────▼────────────────────────┐  │
│  │  Python FastAPI Backend               │  │
│  │  (start/stop/purge/identity/status)   │  │
│  └──────────────┬────────────────────────┘  │
│                 │ Docker API                 │
│  ┌──────────────▼────────────────────────┐  │
│  │  Colima / Docker Runtime              │  │
│  │  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │ Tor      │  │ Ungoogled        │   │  │
│  │  │ Container│  │ Chromium         │   │  │
│  │  │ (proxy)  │◄─┤ Container        │   │  │
│  │  └──────────┘  │ (browser)        │   │  │
│  │                └──────────────────┘   │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## What We Have

| Layer | Status |
|---|---|
| Python/FastAPI backend | **Done** — 7/7 tests passing |
| React/TypeScript UI | **Done** — type-checks clean |
| Docker Compose (Tor + Chromium) | **Drafted** — ready for review |
| Tauri desktop shell | **Blocked** — needs your help |

---

## Build Status — Resolved ✅

`cargo check` now **passes cleanly** on this machine. The previous blocker was resolved by running a clean `cargo update` which pulled in compatible versions of the Tauri crate matrix.

**Environment:**
- Rust: 1.96.0 (ac68faa20 2026-05-25)
- Cargo: 1.96.0 (30a34c682 2026-05-25)
- Tauri: 2.11.2
- tauri-build: 2.6.2
- tauri-runtime-wry: 2.11.4
- wry: 0.55.1

**No uncommitted config files found** — only `tauri.conf.json` exists in `src-tauri/`, and it's already committed.

**Full build log:** `/tmp/cargo_check_full.log` (ends with `Finished dev profile [unoptimized + debuginfo] target(s) in 36.53s` — zero errors, zero warnings.)

---

## What's Left

1. **Colima verification** — confirm the Docker images (`jlesage/ungoogled-chromium`, `dperson/torproxy`) work on Colima on Apple Silicon.
2. **End-to-end test** — start the backend, launch the Tauri app, verify the full flow works.
3. **`@tauri-apps/plugin-shell` removed** — the JS dependency was listed in `package.json` but never imported anywhere in the code, and no corresponding Rust crate existed. It has been removed.

---

## Files Needing Attention

```
frontend/src-tauri/Cargo.toml
frontend/src-tauri/tauri.conf.json
frontend/src-tauri/src/main.rs
frontend/src-tauri/src/commands.rs
deploy/compose.yml
```

---

## What Works Now (can be tested independently)

```bash
# Backend tests
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest tests/test_api.py

# Frontend type check
cd frontend
npm install
npx tsc --noEmit
```

Both of these pass clean.