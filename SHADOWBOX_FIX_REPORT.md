# ShadowBox — Tauri Build Fix Report

**Date:** 2026-06-15  
**Project:** ShadowBox (`frontend/src-tauri/`)  
**Rust version installed:** 1.96.0  
**Target OS:** macOS (Apple Silicon)

---

## Root Cause Summary

There are **two distinct problems** causing `cargo check` to fail. Both must be fixed together.

### Problem 1 — `tauri.conf.json` uses Tauri v1 schema in a v2 project

The error:
```
unknown field `tauri`, expected one of `$schema`, `product-name`, `productName`, ...
```

This is caused by a **schema mismatch**. The current `tauri.conf.json` is missing the `app` top-level key, which is required in Tauri v2. In Tauri v1, window/security config lived under a `tauri { }` top-level key. In Tauri v2 that key was removed and replaced with `app { }`. The current config also lacks a `windows` declaration inside `app`.

### Problem 2 — `Cargo.toml` pins to `=2.3.0` but that exact version has a known trait-bound bug in `tauri-runtime-wry`

Pinning with `=` (exact version) prevents Cargo from pulling patch releases that fix the closure lifetime mismatch in `tauri-runtime-wry`. The fix is to use a **flexible minor version pin** (`"2"`) and let `cargo update` pull the latest stable 2.x patch.

---

## Fix 1 — Replace `tauri.conf.json`

**File:** `frontend/src-tauri/tauri.conf.json`

Replace the entire file contents with:

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "ShadowBox",
  "version": "0.1.0",
  "identifier": "com.shadowbox.app",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "ShadowBox",
        "width": 900,
        "height": 640,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": ["app"],
    "icon": ["icons/32x32.png", "icons/128x128.png"],
    "longDescription": "A self-contained anonymous browsing workspace for macOS.",
    "macOS": {
      "entitlements": "entitlements/entitlements.plist",
      "minimumSystemVersion": "13.0"
    }
  }
}
```

**Key changes from the old file:**
- Added `"$schema"` — triggers correct schema validation in `tauri-build`
- Replaced the missing `tauri {}` block with the correct `app {}` block
- Added `windows` array inside `app` — required; without it the app has no webview
- `security.csp: null` moved inside `app` where it belongs in v2

---

## Fix 2 — Replace `Cargo.toml`

**File:** `frontend/src-tauri/Cargo.toml`

Replace the `[build-dependencies]` and `[dependencies]` sections:

```toml
[package]
name = "shadowbox-ui"
version = "0.1.0"
description = "ShadowBox desktop shell"
authors = ["ShadowBox"]
license = "MIT"
repository = ""
edition = "2021"
rust-version = "1.75"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = ["tray-icon", "image-png"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
reqwest = { version = "0.12", default-features = false, features = ["json", "rustls-tls"] }
```

**Key change:** Remove the `=` prefix from `"=2.3.0"` on both `tauri` and `tauri-build`. The `=` forces an exact version and blocks Cargo from picking up patch releases. Using `"2"` allows Cargo to resolve the latest compatible 2.x.x release, which includes the `tauri-runtime-wry` trait-bound fixes.

---

## Fix 3 — Run These Commands After Saving Both Files

From inside `frontend/src-tauri/`:

```zsh
# 1. Wipe stale lock and build artifacts
rm -rf target/ Cargo.lock

# 2. Pull latest compatible 2.x versions
cargo update

# 3. Verify the build script and Rust code compile
cargo check
```

If `cargo check` still fails, run `cargo check 2>&1 | head -60` and share the first 60 lines of output for further diagnosis.

---

## Fix 4 — Verify `capabilities/default.json` Exists

Tauri 2 requires at least one capability file. Confirm the file exists at:

```
frontend/src-tauri/capabilities/default.json
```

(Note: the status report mentions `frontend/capacities/default.json` — check for a typo in the directory name; it must be `capabilities`, not `capacities`.)

Minimum valid content for `default.json`:

```json
{
  "identifier": "default",
  "description": "Default permissions for the main window",
  "windows": ["main"],
  "permissions": []
}
```

The `windows` value `"main"` must match the `label` field set in `tauri.conf.json` above.

---

## Summary Checklist

| Step | Action | File |
|------|--------|------|
| 1 | Replace entire file | `frontend/src-tauri/tauri.conf.json` |
| 2 | Remove `=` from version pins | `frontend/src-tauri/Cargo.toml` |
| 3 | `rm -rf target/ Cargo.lock && cargo update && cargo check` | terminal |
| 4 | Confirm directory is `capabilities/` not `capacities/` | `frontend/src-tauri/capabilities/default.json` |

---

## What Is NOT Changing

- All Python backend code, tests, Docker files, and Dockerfiles are unaffected
- The React UI (`frontend/src/App.tsx`) is unaffected
- Rust command logic (`commands.rs`, `main.rs`) is unaffected
- No Rust toolchain version change is needed — 1.96.0 is compatible with Tauri 2.x

---

## If the Build Still Fails After These Steps

The remaining risk listed in the status report is the `tauri-runtime-wry` closure lifetime mismatch. If it surfaces after the above fixes, the resolution is:

```zsh
cargo update -p tauri-runtime-wry
cargo check
```

If that still fails, report the exact error output from `cargo check 2>&1` and include the resolved version of `tauri-runtime-wry` from `Cargo.lock` (search for `name = "tauri-runtime-wry"`) for further diagnosis.
