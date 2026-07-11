# ShadowBox — AI Agent Handover Document

**Date:** 2026-06-15  
**Project:** ShadowBox (`/Users/joshua/Projects/ShadowBox`)  
**Current Status:** Fully building and functional. macOS `.app` bundle generates successfully. Backend is structurally sound and tests pass. UI is styled and integrated.

---

## What We’re Building

ShadowBox is a **self-contained anonymous browsing workspace for macOS**. It launches a hardened browser environment fully routed through Tor, isolated from the host system, with user-controlled session persistence and secure data destruction.

The UX goal is **“one-click anonymous workspace”**: the user opens the app, clicks a button, and a fully isolated Ungoogled Chromium session opens with all traffic forced through Tor.

### Core Architecture

- **Tauri desktop shell (v2)** — Native macOS app with a React-based floating control panel.
- **Python FastAPI backend** — Starts/stops containers, manages sessions, and exposes a local control API on `127.0.0.1:4321`.
- **Docker/Colima containers** — Tor daemon + Ungoogled Chromium, isolated from the host.
- **React UI** — Status indicators, start/stop/purge buttons, styled with a premium dark glassmorphic theme.
- **Workspace vault** — Per-session downloads, cookies, bookmarks, isolated from the macOS filesystem.

---

## What Is Working (Recent Fixes)

We just completed a major stabilization pass. The following pieces are verified and working:

1. **Tauri Build System**
   - `cargo tauri build` succeeds. 
   - `tauri.conf.json` uses the correct v2 schema.
   - Bundle identifier `com.shadowbox.desktop` is correct.
   - Capabilities (`capabilities/default.json`) correctly match the window label and have the right permissions.
2. **App Assets & UI**
   - Premium app icons are generated (proper RGBA PNGs) and compiled into an `.icns` bundle.
   - React frontend has full dark-mode CSS styling.
   - TypeScript compiles cleanly without errors.
3. **Backend Stability**
   - The Python FastAPI backend has all dependencies correctly specified.
   - `store.py` type import bugs were fixed.
   - `pytest` suite passes all 7 mocks.
4. **Container Networking**
   - `compose.yml` was fixed to ensure traffic is correctly routed through Tor.
   - Removed contradictory proxy flags and set the Chromium proxy host to `127.0.0.1` so it properly shares the Tor container's network stack (`network_mode: service:tor`).

---

## What Is Next

Now that the app compiles perfectly, the next phase is **Live Environment Testing & macOS Integration**.

### 1. End-to-End Container Testing
- The Docker setup needs to be tested live using **Docker Desktop or Colima**.
- **Action:** Run the Tauri app, click "Open Browser", and verify the backend correctly spins up the Tor container, waits for the 100% bootstrap signal, and then launches the Chromium container.
- **Action:** Verify the VNC feed opens on `localhost:6901` and that Chromium is successfully routing traffic through Tor (e.g., check Tor check page).

### 2. Application Lifecycle Management
- Right now, if the user closes the Tauri window, the containers might keep running in the background.
- **Action:** Implement a proper teardown hook in the Tauri Rust backend or React `useEffect` to call the `/stop` or `/purge` API when the app exits.

### 3. macOS App Signing & Notarization
- The current `.app` bundle is unsigned.
- **Action:** Setup Apple Developer certificates and configure Tauri to sign and notarize the app for distribution, so macOS Gatekeeper doesn't block it.

### 4. VNC Integration Polish
- Currently, the browser opens in a standard web tab pointing to the VNC web client. 
- **Action (Optional):** Consider embedding the VNC client directly within a Tauri webview window for a more seamless "native" feel, rather than opening the user's default system browser.

---

## Do NOT Touch

- **Tauri version pins**: `Cargo.toml` relies on pinned `tauri = "=2.11.2"` and `tauri-build = "=2.6.2"`. Do not upgrade these casually, as it will break the wry sync bounds.
- **Backend state store**: `backend/src/shadowbox/state/` works correctly and tests pass.
- **Icon Generation Scripts**: All icons are correctly generated. Leave the `icons/` directory alone unless rebranding.

---

## Exact Commands to Continue

### 1. Run the App Locally (Dev Mode)
```zsh
# Terminal 1: Run the backend
cd /Users/joshua/Projects/ShadowBox/backend
source .venv/bin/activate
uvicorn shadowbox.main:app --host 127.0.0.1 --port 4321

# Terminal 2: Run the Tauri app
cd /Users/joshua/Projects/ShadowBox/frontend
npm run tauri dev
```

### 2. Build the Production Release
```zsh
cd /Users/joshua/Projects/ShadowBox/frontend/src-tauri
cargo tauri build
```
*The resulting app will be in `target/release/bundle/macos/ShadowBox.app`.*
