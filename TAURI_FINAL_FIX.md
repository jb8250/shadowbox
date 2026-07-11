# ShadowBox — Final Tauri Fix

## Root Cause
The lock is unresolvable because `tauri 2.6.2` depends on `webkit2gtk = "=2.0.1"`, and that version conflicts with newer dependencies needed for `tauri-runtime-wry 2.11.2`. No combination of `Cargo.toml` pins can reconcile this snapshot.

## Fix — Regenerate Lock from Tauri CLI Scaffolding

Run these commands on your Mac:

```zsh
# 1. Back up our source files
cd /Users/joshua/Projects/ShadowBox/frontend/src-tauri
mkdir -p /tmp/tauri-backup
cp src/main.rs src/commands.rs /tmp/tauri-backup/

# 2. Scaffold a fresh Tauri project in a temp dir (generates a working Cargo.toml + Cargo.lock)
cd /tmp
cargo tauri init --ci none --name shadowbox-ui --dev-url http://localhost:5173 --before-dev-command "npm run dev" --before-build-command "npm run build" --frontend-dist ../dist 2>&1 | tail -20

# 3. Copy the working Cargo.toml and Cargo.lock back
cp /tmp/shadowbox-ui/Cargo.toml /Users/joshua/Projects/ShadowBox/frontend/src-tauri/
cp /tmp/shadowbox-ui/Cargo.lock /Users/joshua/Projects/ShadowBox/frontend/src-tauri/

# 4. Restore our source files
cp /tmp/tauri-backup/main.rs /Users/joshua/Projects/ShadowBox/frontend/src-tauri/src/
cp /tmp/tauri-backup/commands.rs /Users/joshua/Projects/ShadowBox/frontend/src-tauri/src/

# 5. Verify it compiles
cd /Users/joshua/Projects/ShadowBox/frontend/src-tauri
cargo check
```

## If `cargo tauri init` fails
Alternative: create the lock from a newer Tauri init:
```zsh
cd /tmp
cargo tauri init --ci none --name shadowbox-ui
cp /tmp/shadowbox-ui/Cargo.toml /Users/joshua/Projects/ShadowBox/frontend/src-tauri/
cp /tmp/shadowbox-ui/Cargo.lock /Users/joshua/Projects/ShadowBox/frontend/src-tauri/
cp /tmp/tauri-backup/main.rs /Users/joshua/Projects/ShadowBox/frontend/src-tauri/src/
cp /tmp/tauri-backup/commands.rs /Users/joshua/Projects/ShadowBox/frontend/src-tauri/src/
```

Then edit the fresh `Cargo.toml` to add back:
```toml
[lints.rust]
unexpected_cfgs = { level = "warn", check-cfg = ["cfg(mobile)"] }
```

Then `cargo check`.
