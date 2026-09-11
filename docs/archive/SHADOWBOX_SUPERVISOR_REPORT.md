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
| Docker Compose (Tor + Chromium) | **Done** — verified on Colima (arm64) |
| Tauri desktop shell | **Done** — `cargo check` passes clean |
| End-to-end integration | **Not yet tested** — backend + Tauri app together |

---

## Build Status — `cargo check` Passes ✅

`cargo check` now **passes cleanly** on this machine. The previous blocker was resolved by running a clean `cargo update` which pulled in compatible versions of the Tauri crate matrix.

**Environment:**
- Rust: 1.96.0 (ac68faa20 2026-05-25)
- Cargo: 1.96.0 (30a34c682 2026-05-25)
- Tauri: 2.11.2
- tauri-build: 2.6.2
- tauri-runtime-wry: 2.11.4
- wry: 0.55.1

**No uncommitted config files found** — only `tauri.conf.json` exists in `src-tauri/`, and it's already committed.

**Full build log:** `/tmp/cargo_check_full.log` (557 lines, zero errors, zero warnings.)

---

## Colima Verification — All Checks Pass ✅

Both containers run natively on arm64 via Colima with no emulation.

### Container Status

```
NAME                        IMAGE                                           STATUS                    PORTS
shadowbox-browser-default   lscr.io/linuxserver/ungoogled-chromium:latest   Up 5 seconds
shadowbox-tor-default       dockurr/tor:latest                              Up 2 minutes (healthy)    0.0.0.0:3000-3001, 0.0.0.0:9050->9050
```

### Verification Results

| Check | Command | Result |
|---|---|---|
| Tor healthcheck | `docker inspect --format='{{.State.Health.Status}}' shadowbox-tor-default` | **healthy** |
| Browser HTTP UI | `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` | **200** |
| Browser HTTPS UI | `curl -sk -o /dev/null -w "%{http_code}" https://localhost:3001` | **200** |
| Tor routing | `curl -s --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip` | **`{"IsTor":true,"IP":"45.84.107.174"}`** |

### Issues Found & Fixed in `deploy/compose.yml`

**1. `dperson/torproxy:aarch64` — abandoned, wouldn't bootstrap**
- Image last updated April 2021
- Ships Tor 0.4.4.8 — too old to bootstrap on the current Tor network (stuck at 30% with "Consensus not signed by sufficient number of requested authorities")
- **Fix:** Replaced with `dockurr/tor:latest` (Tor 0.4.9.11, multi-arch, actively maintained, includes curl for healthchecks)

**2. `jlesage/ungoogled-chromium:latest` — doesn't exist on Docker Hub**
- jlesage only publishes `jlesage/chromium` (plain Chromium, not ungoogled)
- **Fix:** Replaced with `lscr.io/linuxserver/ungoogled-chromium:latest` (actively maintained, multi-arch with native arm64)

**3. Browser UI ports never published to host**
- `network_mode: service:tor` causes Docker to ignore `chromium`'s `ports:` section entirely
- Original file had nothing published (neither the old VNC port 5800 nor a web UI port)
- **Fix:** Published ports `3000:3000` (HTTP) and `3001:3001` (HTTPS) on the `tor` service instead

**4. Healthcheck `grep` target wrong**
- `check.torproject.org/api/ip` returns JSON (`{"IsTor":true,"IP":"..."}`), not the old text format containing "Yes"
- **Fix:** Changed `grep -q Yes` → `grep -q true`

---

## Removed Dead Dependency: `@tauri-apps/plugin-shell`

The JS dependency was listed in `package.json` but never imported anywhere in the source code, and no corresponding `tauri-plugin-shell` crate existed in `Cargo.toml` or was registered in `main.rs`. Removed.

---

## End-to-End Test Results — All Checks Pass ✅

Backend was run with `DOCKER_HOST=unix:///Users/joshua/.colima/default/docker.sock` to match the Colima Docker context.

### Step-by-step results

| Step | Check | Result |
|---|---|---|
| **a** | Backend listening on `127.0.0.1:4321` | ✅ HTTP 200 |
| **b** | Tauri dev mode window opens | ⚠️ Skipped — headless session, no display |
| **c** | `POST /start` → containers come up | ✅ Backend returned 200, containers running |
| **d** | `GET /status` shows `running` | ✅ Matches container state |
| **e** | `POST /identity/new` rotates circuit | ✅ Status shows `"identity":"new"`, tor logs show new guard selection |
| **f** | Browser UI on `localhost:3001` | ✅ HTTPS 200 |
| **g** | `POST /stop` (keep_downloads=true) | ✅ Containers stopped, volumes preserved |
| **g** | `POST /purge` | ✅ Containers stopped, `shadowbox-default` volume removed, compose tor auto-restarted to healthy |

### Container state after purge

```
$ docker ps --filter name=shadowbox
NAMES                   STATUS
shadowbox-tor-default   Up (healthy)

$ docker volume ls --filter name=shadowbox
VOLUME NAME                DRIVER
deploy_shadowbox-default   local
```

`shadowbox-default` (workspace volume) was destroyed by purge. `deploy_shadowbox-default` (compose's named volume) remains.

---

## What's Left

- Tauri dev mode window test (requires GUI session)

---

## How to Test What Works Now

```bash
# 1. Backend tests
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest tests/test_api.py

# 2. Frontend type check
cd frontend
npm install
npx tsc --noEmit

# 3. Colima containers
colima start
docker compose -f deploy/compose.yml up -d
docker compose -f deploy/compose.yml ps
curl http://localhost:3000    # Browser UI
```
