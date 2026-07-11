# Tauri Configuration Files

## Cargo.toml (`frontend/src-tauri/Cargo.toml`)

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
tauri-build = { version = "=2.3.0", features = [] }

[dependencies]
tauri = { version = "=2.3.0", features = ["tray-icon", "image-png"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
reqwest = { version = "0.12", default-features = false, features = ["json", "rustls-tls"] }
```

## tauri.conf.json (`frontend/src-tauri/tauri.conf.json`)

```json
{
  "productName": "ShadowBox",
  "version": "0.1.0",
  "identifier": "com.shadowbox.app",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist"
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
