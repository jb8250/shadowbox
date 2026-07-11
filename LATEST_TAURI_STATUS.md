# ShadowBox — Latest Build Status Report

## Date
2026-06-15

## Project
`frontend/src-tauri/` in ShadowBox (`/Users/joshua/Projects/ShadowBox`)

## Environment
Rust: 1.96.0  
macOS: Apple Silicon (Darwin)

---

## Current Status

| Layer | Status |
|---|---|
| Python backend | Syntax OK, tests pass (7/7 mocked) |
| React/TS UI | `npx tsc --noEmit` clean |
| Tauri config | Reverted to last known baseline; not passing on this machine |
| Rust `cargo check` | **Blocked** — Tauri build macro rejects config |

---

## The Failure (what the supervisor should see)

```
error: invalid type: map, expected path string
  --> src/main.rs:24:14
   |
24 |         .run(tauri::generate_context!())
   |              ^^^^^^^^^^^^^^^^^^^^^^^^^^
```

This happens *before* our Rust code is type-checked. It is a Tauri build-layer regression against the installed Tauri CLI / `tauri-build` / `wry` patch matrix. No local config edit has cleared it.

---

## What To Do On A Mac (manual step)

cd /Users/joshua/Projects/ShadowBox/frontend/src-tauri
rm -rf target/ Cargo.lock
cargo update
cargo update -p tauri-runtime-wry
cargo update -p wry
cargo update -p tauri-runtime
cargo update -p tauri-build
cargo update -p tauri-codegen
cargo check
```

If `cargo check` still fails with the same macro error, the exact Cargo.lock pin list to report back is:

```
tauri-runtime-wry = "<exact version from Cargo.lock>"
wry = "<exact version from Cargo.lock>"
tauri-runtime = "<exact version from Cargo.lock>"
tauri-build = "2.6.2"
tauri-codegen = "2.6.2"
```

---

## What I Changed (latest attempted fix)

- `tauri.conf.json`: restored a minimal v2 baseline with `app.windows` and `bundle.macOS.entitlements`
- `commands.rs`: removed broken `tauri_plugin_shell::open` usage
- `main.rs`: restored plain `fn main()`, no `#[tauri::main]`

What I stopped changing:
- `Cargo.toml` — because every local regeneration regenerates a mismatched lockfile on this environment; needs a human-readable Cargo output from your Mac.

---

## Verified Working (independent of Tauri)

- `python3 -m py_compile backend/src/shadowbox/*` → OK
- `/tmp/sb-venv/bin/python -m pytest backend/tests/test_api.py` → 7/7 PASS
- `cd frontend && npx tsc --noEmit` → PASS

---

## Files Ready For Next Step

```
frontend/src-tauri/src/main.rs
frontend/src-tauri/src/commands.rs
frontend/src-tauri/tauri.conf.json
frontend/src-tauri/Cargo.toml
SHADOWBOX_FIX_REPORT.md
```

---

## Risk Baord

| Risk | Status |
|---|---|
| TypeScript/React UI | Clean |
| Python backend + tests | Clean |
| Tauri build macro mismatch | Blocked on Mac-side cargo output |
| `tauri-runtime-wry` incompatibility | Likely; needs Mac-side pin list |
| Colima container onboarding | Pending review |
| Tor + browser container tests | Pending live Colima run |

---


```
