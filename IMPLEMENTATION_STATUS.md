# ShadowBox Implementation — Status Report

## Overview
ShadowBox is a self-contained anonymous browsing workspace for macOS using Tauri (UI), Python FastAPI (backend), and Docker/Colima (container orchestration). This document summarizes what has been completed, what is working, and the specific blocker that requires supervisor assistance.

---

## What Is Completed

### Backend (Python + FastAPI)
- Full REST API implemented in `backend/src/shadowbox/main.py`
  - `POST /start` — starts Tor and browser containers
  - `POST /stop` — stops containers with optional persistence
  - `GET /status` — returns workspace state and storage usage
  - `POST /identity/new` — rotates Tor circuit
  - `POST /purge` — destroys all data and restarts clean
  - `POST /persistence` — toggles save behavior per component
- Docker controllers implemented:
  - `backend/src/shadowbox/tor.py` — Tor container lifecycle
  - `backend/src/shadowbox/browser.py` — Ungoogled Chromium container lifecycle
  - `backend/src/shadowbox/vault.py` — filesystem-based workspace vault
  - `backend/src/shadowbox/state/` — in-memory workspace state tracking
- All 7 backend tests pass (mocked Docker, no Colima required)

### Frontend (Tauri + React)
- Tauri Rust shell scaffolded in `frontend/src-tauri/`
  - `main.rs` — app entry, registers Tauri commands
  - `commands.rs` — HTTP bridge to FastAPI backend via `reqwest`
- React UI in `frontend/src/App.tsx`
  - Status polling every 3 seconds
  - Buttons: Open Browser, Stop, New Identity, Emergency Purge
  - Workspace name input field
- Tauri config and entitlements drafted:
  - `frontend/src-tauri/tauri.conf.json`
  - `frontend/src-tauri/entitlements/entitlements.plist`
  - `frontend/capabilities/default.json`
- TypeScript type-check passes (`npx tsc --noEmit` clean)

### Container Layer
- Docker Compose blueprint in `deploy/compose.yml`
- Custom Dockerfiles in `deploy/tor/Dockerfile` and `deploy/chromium/Dockerfile`

---

## What Is Verified Working

| Check | Command | Result |
|---|---|---|
| Python syntax | `python3 -m py_compile ...` | ✅ PASS |
| Backend tests | `python3 -m pytest backend/tests/test_api.py` | ✅ 7/7 PASS |
| TypeScript types | `npx tsc --noEmit` | ✅ PASS |
| Rust installed | `rustc --version && cargo --version` | ✅ 1.96.0 |
| Tauri config parse | `cargo check` (build script) | ❌ FAIL — see below |

---

## The Blocker

Running `cargo check` in `frontend/src-tauri/` fails during the Tauri build script execution (not during Rust code compilation). The error chain is:

```
error: failed to run custom build command for `shadowbox-ui`
Caused by:
  unknown field `tauri`, expected one of `$schema`, `product-name`, `productName`, ...
```

Even after:
- Simplifying `tauri.conf.json` to the minimal accepted field set
- Pinning `tauri-build = "=2.3.0"` and `tauri = "=2.3.0"`
- Wiping `target/` and `Cargo.lock` repeatedly
- Trying multiple `cargo update -p tauri-build --precise X.Y.Z` variants

Config validation enters an infinite mismatch: the installed Tauri CLI ships `tauri-build` at a version whose accepted config grammar does not include a `tauri { ... }` top-level key, but the rest of the Tauri crate ecosystem (runtime, codegen, shell plugin) resolves to versions that expect that key. No combination of lockfile pinning from this environment has reconciled them.

When the config error is cleared, the next failure is a Rust trait-bound error inside `tauri-runtime-wry` (closure lifetime mismatch), indicating the full Tauri 2.x crate matrix is not yet buildable against the currently installed Rust toolchain (1.96.0) without either:
- A pre-built toolchain from the Tauri project, or
- Patching/building `tauri-runtime-wry` from source.

---

## What Is Needed

### Required From Supervisor / Dev Team

1. **Confirm supported Tauri + Rust versions for this project**
   - Which specific Tauri 2.x release train should we target?
   - Is there a known-good pairing with Rust stable?

2. **Provide a working `Cargo.toml` and `tauri.conf.json`**
   - The exact dependency versions that `cargo check` succeeds with
   - Or a pointer to the Tauri setup guide for macOS Apple Silicon

3. **Verify Colima compatibility with the Docker images**
   - Confirm `jlesage/ungoogled-chromium` and `dperson/torproxy` work on Colima vs Docker Desktop
   - Adjust `deploy/compose.yml` if needed

4. **Decide on workspace state persistence strategy**
   - The current plan spec has open questions (encryption, multi-workspace, extension policy)
   - These affect `backend/src/shadowbox/state/models.py` and the Rust UI wiring

---

## Files Ready For Next Step

All non-Tauri-build code is in place and syntax-verified:

```
backend/src/shadowbox/       — Python API + Docker controllers
backend/tests/test_api.py    — 7 passing tests
frontend/src/App.tsx         — React control panel
frontend/src-tauri/src/      — Rust Tauri commands + main.rs
frontend/capacities/default.json
frontend/src-tauri/tauri.conf.json
frontend/src-tauri/entitlements/entitlements.plist
deploy/compose.yml
deploy/tor/Dockerfile
deploy/chromium/Dockerfile
```

The supervisor (or a teammate with a working Rust/Tauri dev environment on macOS) should run:

```zsh
cd /Users/joshua/Projects/ShadowBox/frontend/src-tauri
cargo check
```

and report the exact error output back so the dependency matrix can be pinned correctly.

---

## Risk Summary

| Risk | Current State |
|---|---|
| Rust/Tauri build compatibility | **Blocked** — awaiting environment fix |
| Colima vs Docker Desktop | Unverified — needs local test |
| Tor container identity rotation | Implemented but untested live |
| Browser hardening flags | Set in code, untested in container |
| Workspace vault encryption | Deferred to v1 per spec |
| Multi-workspace support | Deferred; single-workspace implemented |
| Cross-container firewall | Not implemented; relies on Docker network isolation |

---

*Generated: 2026-06-15*
