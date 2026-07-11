# ShadowBox Setup

## Prerequisites

- macOS Apple Silicon
-Colima (recommended) or Docker Desktop
- Python 3.11+
- Node.js 20+ (for Tauri dev, optional)
- Rust 1.75+ (for Tauri dev, optional)

## Quick Start (Backend)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Backend

```bash
uvicorn shadowbox.main:app --host 127.0.0.1 --port 4321
```

## Container Runtime (Colima)

```bash
brew install colima
colima start --mount-type=virtiofs
docker context use colima
```

## Development / Build

Tauri frontend requires additional setup. See `frontend/src-tauri/` for Rust dependencies.

## Security Notes

This is an early prototype. Do not rely on it for production anonymity.
