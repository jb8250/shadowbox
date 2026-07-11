# ShadowBox — Tauri Build Fix Report (v2)

**Date:** 2026-06-15  
**Project:** `frontend/src-tauri/` in `/Users/joshua/Projects/ShadowBox`  
**Rust:** 1.96.0 | **macOS:** Apple Silicon  
**Previous report:** SHADOWBOX_FIX_REPORT.md (config schema fix — now applied)

---

## Progress Since Last Report

The original `unknown field 'tauri'` error is gone. That schema fix worked.

The new blocker is a different, lower-level error:

```
error: invalid type: map, expected path string
  --> src/main.rs:24:14
   |
24 |         .run(tauri::generate_context!())
   |              ^^^^^^^^^^^^^^^^^^^^^^^^^^
```

This error originates inside the `tauri::generate_context!()` macro — which means it is **not a Rust code problem**. It is `tauri-codegen` failing to deserialize the `tauri.conf.json` at build time. The macro reads the config and serializes it into Rust source, and one field is giving it a type it doesn't expect.

---

## Root Cause

The error `invalid type: map, expected path string` means the macro received a **JSON object `{}`** where it expected a **plain string (file path)**.

The two most likely culprits in the current config are:

### Culprit A — `bundle.macOS.entitlements` (most likely)

In some `tauri-codegen` patch versions in the 2.x line, the `entitlements` field inside `bundle.macOS` is deserialized expecting a plain path string. When it instead receives a nested object (or when the path doesn't resolve at compile time), it throws this exact error.

**Fix:** Temporarily remove the entire `bundle.macOS` block from `tauri.conf.json` to isolate the problem. Replace it with just the minimum:

```json
"macOS": {}
```

If `cargo check` passes after that, the entitlements path is the issue — either the `.plist` file doesn't exist yet at the expected path, or the path string itself needs to be relative to the `src-tauri/` directory, not the project root.

Correct form when re-adding it:
```json
"macOS": {
  "minimumSystemVersion": "13.0",
  "entitlements": "entitlements/entitlements.plist"
}
```
The path must be **relative to `src-tauri/`**, and the file **must physically exist** on disk at `frontend/src-tauri/entitlements/entitlements.plist` — `generate_context!()` validates the path at compile time.

### Culprit B — `bundle.targets` value (less likely, worth checking)

In Tauri 2.x the `bundle.targets` field accepts either the string `"all"` or a specific array of target names. The value `["app"]` is not a valid Tauri 2 bundle target — valid values are `"dmg"`, `"app"`, `"updater"`, `"nsis"`, `"msi"`, `"deb"`, `"rpm"`, `"appimage"`, `"pacman"`, or the shorthand `"all"`. While `"app"` is actually valid on macOS, some patch versions of `tauri-codegen` reject it as a bare string vs. a recognized enum.

**Fix:** Change `"targets": ["app"]` to `"targets": "all"` for development, which is universally accepted:

```json
"bundle": {
  "active": true,
  "targets": "all",
  ...
}
```

---

## Recommended Fix Sequence

Apply these changes to `frontend/src-tauri/tauri.conf.json` in order, running `cargo check` after each to isolate the exact cause.

### Step 1 — Use this minimal working config first

Replace `tauri.conf.json` entirely with this stripped-down version that removes all optional fields that could cause type errors:

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
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png"
    ]
  }
}
```

**What was removed vs. the last version:**
- `bundle.macOS` block entirely removed (re-add after confirming build passes)
- `bundle.longDescription` removed (cosmetic, not needed for build)
- `bundle.targets` changed from `["app"]` to `"all"`

Then run:
```zsh
cd /Users/joshua/Projects/ShadowBox/frontend/src-tauri
rm -rf target/ Cargo.lock
cargo update
cargo check
```

### Step 2 — If Step 1 passes, re-add macOS config

First confirm the entitlements file physically exists:
```zsh
ls -la /Users/joshua/Projects/ShadowBox/frontend/src-tauri/entitlements/entitlements.plist
```

If it does not exist, create it:
```zsh
mkdir -p /Users/joshua/Projects/ShadowBox/frontend/src-tauri/entitlements
cat > /Users/joshua/Projects/ShadowBox/frontend/src-tauri/entitlements/entitlements.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.app-sandbox</key>
  <false/>
  <key>com.apple.security.network.client</key>
  <true/>
</dict>
</plist>
PLIST
```

Then add back to `tauri.conf.json`:
```json
"bundle": {
  "active": true,
  "targets": "all",
  "icon": ["icons/32x32.png", "icons/128x128.png"],
  "macOS": {
    "minimumSystemVersion": "13.0",
    "entitlements": "entitlements/entitlements.plist"
  }
}
```

Run `cargo check` again to confirm it still passes.

### Step 3 — Confirm capabilities/ directory name

The status report references `frontend/capacities/default.json` (typo) in one place and `frontend/capabilities/default.json` in another. Verify:

```zsh
ls /Users/joshua/Projects/ShadowBox/frontend/src-tauri/capabilities/
```

If the directory doesn't exist or is misspelled, create it:
```zsh
mkdir -p /Users/joshua/Projects/ShadowBox/frontend/src-tauri/capabilities
cat > /Users/joshua/Projects/ShadowBox/frontend/src-tauri/capabilities/default.json << 'CAP'
{
  "identifier": "default",
  "description": "Default permissions",
  "windows": ["main"],
  "permissions": []
}
CAP
```

---

## What To Report Back

If `cargo check` still fails after Step 1, paste the **full output** of:

```zsh
cargo check 2>&1
```

And also paste the output of:
```zsh
grep -A2 'name = "tauri"' Cargo.lock | head -20
grep -A2 'name = "tauri-build"' Cargo.lock | head -10
grep -A2 'name = "tauri-codegen"' Cargo.lock | head -10
grep -A2 'name = "tauri-runtime-wry"' Cargo.lock | head -10
grep -A2 'name = "wry"' Cargo.lock | head -10
```

This gives the exact resolved versions, which is the only way to pin a working matrix from outside this environment.

---

## Summary Table

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Replace `tauri.conf.json` with minimal config above | `cargo check` passes |
| 2 | Confirm `.plist` file exists, re-add `bundle.macOS` block | `cargo check` still passes |
| 3 | Fix `capabilities/` directory name and `default.json` | No capability warnings |
| 4 | If step 1 still fails, paste full `cargo check` output + Cargo.lock versions | Enables exact pin diagnosis |

---

## What Is NOT Changing

- All Python backend, tests, Dockerfiles — unaffected
- `frontend/src/App.tsx` React UI — unaffected  
- `src/main.rs` and `src/commands.rs` Rust logic — unaffected (the error is in config parsing, not Rust code)
- Rust toolchain version — 1.96.0 is fine, no change needed

