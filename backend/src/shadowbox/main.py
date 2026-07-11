from fastapi import FastAPI
from pydantic import BaseModel
from shadowbox.state.store import store
from shadowbox.state.models import WorkspaceStatus
from shadowbox.tor import TorController
from shadowbox.browser import BrowserController
from shadowbox.vault import VaultManager
import docker


app = FastAPI(title="ShadowBox Controller", version="0.1.0")


class StartRequest(BaseModel):
    workspace: str = "default"


class StopRequest(BaseModel):
    workspace: str = "default"
    keep_downloads: bool = False


class PersistenceToggleRequest(BaseModel):
    workspace: str = "default"
    keep_downloads: bool = False
    keep_cookies: bool = False
    keep_extensions: bool = False
    keep_bookmarks: bool = False
    keep_session: bool = False


class IdentityRequest(BaseModel):
    workspace: str = "default"


_client: docker.DockerClient | None = None


def get_docker_client() -> docker.DockerClient:
    global _client
    if _client is None:
        _client = docker.from_env()
        _client.ping()
    return _client


@app.get("/health")
def health() -> dict:
    return {"service": "shadowbox-backend", "status": "up"}


@app.post("/start")
def start(req: StartRequest) -> dict:
    state = store.ensure(req.workspace)
    state.persistence.cookies = True
    client = get_docker_client()
    tor = TorController(client)
    browser = BrowserController(client)
    state.tor_container = tor.start(req.workspace)
    state.browser_container = browser.start(req.workspace)
    store.set_status(req.workspace, WorkspaceStatus.RUNNING)
    url = browser.vnc_url(req.workspace)
    return {"status": "running", "workspace": req.workspace, "url": url}


@app.post("/stop")
def stop(req: StopRequest) -> dict:
    state = store.ensure(req.workspace)
    client = get_docker_client()
    tor = TorController(client)
    browser = BrowserController(client)
    tor.stop(req.workspace)
    browser.stop(req.workspace, keep=req.keep_downloads)
    store.set_status(req.workspace, WorkspaceStatus.STOPPED)
    return {"status": "stopped"}


@app.get("/status")
def status(workspace: str = "default") -> dict:
    state = store.ensure(workspace)
    size = VaultManager(workspace).usage_bytes()
    return {
        "workspace": workspace,
        "status": state.status.value,
        "identity": state.tor_identity,
        "storage_bytes": size,
    }


@app.post("/persistence")
def set_persistence(req: PersistenceToggleRequest) -> dict:
    state = store.ensure(req.workspace)
    state.persistence.downloads = req.keep_downloads
    state.persistence.cookies = req.keep_cookies
    state.persistence.extensions = req.keep_extensions
    state.persistence.bookmarks = req.keep_bookmarks
    state.persistence.session = req.keep_session
    return {"status": "ok", "persistence": state.persistence.__dict__}


@app.post("/identity/new")
def new_identity(req: IdentityRequest) -> dict:
    state = store.ensure(req.workspace)
    client = get_docker_client()
    tor = TorController(client)
    tor.new_identity(req.workspace)
    state.tor_identity = "new"
    return {"status": "rotated"}


@app.post("/purge")
def purge() -> dict:
    client = get_docker_client()
    tor = TorController(client)
    browser = BrowserController(client)
    for name in list(store._workspaces.keys()):
        tor.stop(name)
        browser.remove(name)
        VaultManager(name).destroy()
        store._workspaces.pop(name, None)
    store.create("default")
    tor.start("default")
    return {"status": "purged"}
