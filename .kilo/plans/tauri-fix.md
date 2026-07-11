# ShadowBox — Tauri Build Fix Plan

## Date
2026-06-15

## Project
`frontend/src-tauri/` in ShadowBox (`/Users/joshua/Projects/ShadowBox`)

## Rust version
1.96.0

## Target OS
macOS (Apple Silicon)

## Root Cause Summary

Two distinct problems causing `cargo check` to fail. Both must be fixed together.

1. `tauri.conf.json` uses Tauri v1 schema in a v2 project
2. `Cargo.toml` pins to exact `2.3.0` but that version has a known trait-bound bug in `tauri-runtime-wry`

## Fix 1 — Replace `tauri.conf.json`

File: `frontend/src-tauri/tauri.conf.json`

Replace entire file with:
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

Key changes:
- Added `"$schema"` — triggers correct schema validation in `tauri-build`
- Replaced the missing `tauri {}` block with the correct `app {}` block
- Added `windows` array inside `app` — required; without it the app has no webview
- `security.csp: null` moved inside `app` where it belongs in v2

## Fix 2 — Replace `Cargo.toml`

File: `frontend/src-tauri/Cargo.toml`

Replace `[build-dependencies]` and `[dependencies]` sections:
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

Key change: Remove the `=` prefix from `"=2.3.0"` on both `tauri` and `tauri-build`.

## Fix 3 — Commands After Saving Both Files

From inside `frontend/src-tauri/`:
```zsh
rm -rf target/ Cargo.lock
cargo update
cargo check
```

## Fix 4 — Verify `capabilities/default.json` Exists

Tauri 2 requires at least one capability file. Confirm the file exists at:
`frontend/src-tauri/capabilities/default.json`

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

The `windows` value `"main"` must match the `label` field set in `tauri.conf.json`.

## Summary Checklist

| Step | Action | File |
|------|--------|------|
| 1 | Replace entire file | `frontend/src-tauri/tauri.conf.json` |
| 2 | Remove `=` from version pins | `frontend/src-tauri/Cargo.toml` |
| 3 | `rm -rf target/ Cargo.lock && cargo update && cargo check` | terminal |
| 4 | Confirm directory is `capabilities/` not `capacities/` | `frontend/src-tauri/capabilities/default.json` |

## What Is NOT Changing

- All Python backend code, tests, Docker files, and Dockerfiles are unaffected
- The React UI (`frontend/src/App.tsx`) is unaffected
- Rust command logic (`commands.rs`, `main.rs`) is unaffected
- No Rust toolchain version change is needed — 1.96.0 is compatible with Tauri 2.x

## If the Build Still Fails After These Steps

If `tauri-runtime-wry` closure lifetime mismatch surfaces, run:
```zsh
cargo update -p tauri-runtime-wry
cargo check
```
