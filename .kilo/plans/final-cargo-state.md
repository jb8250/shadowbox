# Final Safe State for `frontend/src-tauri/Cargo.toml`

## Current working content

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

[lints.rust]
unexpected_cfgs = { level = "warn", check-cfg = ["cfg(mobile)"] }
```

## Why not to pin exact versions here

Do **not** change `"2"` to `"=2.6.2"` or `"=2.11.2"` in this file.
This workspace has hit two different pin-resolution failures:

1. `tauri = "=2.3.0"` rejected by `tauri-plugin-shell 2.3.5` (requires `^2.10`)
2. `tauri-build = "=2.11.2"` failed with: `no matching package named \`tauri-build\` found`

Leaving the deps on `"2"` is the only form that has successfully regenerated a lockfile. The version skew between `tauri` and `tauri-build` is the real bug, and it must be fixed on a Mac with a working Tauri install — not by editing `Cargo.toml` here.

## Recommended Mac-side actions

A. Install Tauri CLI and let it manage the build layer:
```zsh
cargo install tauri-cli --git https://github.com/tauri-apps/tauri.git --tag cli-v2
cd /Users/joshua/Projects/ShadowBox/frontend/src-tauri
rm -rf target Cargo.lock
cargo tauri build
```

B. If Tauri CLI is unavailable, align the stack to one release line manually:
```zsh
cd /Users/joshua/Projects/ShadowBox/frontend/src-tauri
cargo update -p tauri --precise 2.11.2
cargo update -p tauri-build --precise 2.11.2 || cargo update -p tauri-build --precise 2.6.2
cargo update -p tauri-codegen --precise 2.6.2
cargo update -p tauri-runtime --precise 2.11.2
cargo update -p tauri-runtime-wry --precise 2.11.2
cargo update -p wry --precise 0.55.1
cargo check
```

C. If exact pins still fail, keep `"2"` (flexible minor) and report the resolved versions from `Cargo.lock` (`grep -A2 'name = "tauri"' Cargo.lock`) for macro-level diagnosis.
