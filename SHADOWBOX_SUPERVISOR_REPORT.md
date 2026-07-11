# ShadowBox — Supervisor Handoff Report

**Date:** 2026-07-11
**Repo:** https://github.com/jb8250/shadowbox

---

## What We Have

| Layer | Status |
|---|---|
| Python/FastAPI backend | **Done** — 7/7 tests passing |
| React/TypeScript UI | **Done** — type-checks clean |
| Docker Compose (Tor + Chromium) | **Drafted** — ready for review |
| Tauri desktop shell | **Blocked** — needs your help |

---

## The Blocker

`cargo check` fails in `frontend/src-tauri/` with Tauri build macro errors. The root cause is a version mismatch between the Tauri crate matrix and the Rust 1.96.0 toolchain on macOS Apple Silicon. No combination of dependency pinning has resolved it from this environment.

The error:

```
error: invalid type: map, expected path string
  --> src/main.rs:24:14
   |
24 |         .run(tauri::generate_context!())
   |              ^^^^^^^^^^^^^^^^^^^^^^^^^^
```

---

## What We Need From You

1. **A working `Cargo.toml` + `tauri.conf.json` + `Cargo.lock`** — the exact Tauri 2.x dependency versions and config that build successfully on your macOS environment. The known-good pairing is what's missing.
2. **Which Rust version to use** — should we switch toolchains, or are you using a specific stable that works?
3. **Colima verification** — once the build is fixed, we need confirmation that the Docker images (`jlesage/ungoogled-chromium`, `dperson/torproxy`) work on Colima on Apple Silicon.

---

## How To Help

If you have a working Rust/Tauri setup on macOS, please run this and share the output:

```zsh
cd /path/to/shadowbox/frontend/src-tauri
rm -rf target/ Cargo.lock
cargo update
cargo check
```

Then share:
- The `Cargo.lock` file (or at least the `tauri-*` and `wry` version lines)
- Your Rust version (`rustc --version`)
- The full `cargo check` output

Alternatively, if there's a specific Tauri 2.x release + Rust stable that's known to work on macOS Apple Silicon, just point us to it and we can adjust.

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