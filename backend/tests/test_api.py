from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from shadowbox.main import app


client = TestClient(app)


def _make_container(name: str, status: str = "running") -> MagicMock:
    container = MagicMock()
    container.name = name
    container.status = status
    exec_result = MagicMock()
    exec_result.exit_code = 0
    container.exec_run.return_value = exec_result
    container.logs.return_value = b"Bootstrapped 100%"
    return container


def _docker_client() -> MagicMock:
    client = MagicMock()
    client.containers.get.return_value = _make_container("shadowbox-tor-default")
    client.containers.run.return_value = _make_container("shadowbox-tor-default")
    client.networks.get.return_value = MagicMock()
    client.volumes.get.return_value = MagicMock()
    return client


@patch("shadowbox.main.docker")
def test_health(mock_docker: MagicMock) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "up"


@patch("shadowbox.main.docker")
def test_start(mock_docker: MagicMock) -> None:
    mock_docker.from_env.return_value = _docker_client()
    r = client.post("/start", json={"workspace": "default"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "running"
    assert body["url"] == "http://localhost:6901"


@patch("shadowbox.main.docker")
def test_stop(mock_docker: MagicMock) -> None:
    mock_docker.from_env.return_value = _docker_client()
    client.post("/start", json={"workspace": "default"})
    r = client.post("/stop", json={"workspace": "default", "keep_downloads": False})
    assert r.status_code == 200
    assert r.json()["status"] == "stopped"


@patch("shadowbox.main.docker")
def test_status(mock_docker: MagicMock) -> None:
    mock_docker.from_env.return_value = _docker_client()
    client.post("/start", json={"workspace": "default"})
    r = client.get("/status?workspace=default")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "running"
    assert payload["workspace"] == "default"
    assert "storage_bytes" in payload


@patch("shadowbox.main.docker")
def test_persistence(mock_docker: MagicMock) -> None:
    r = client.post(
        "/persistence",
        json={
            "workspace": "default",
            "keep_downloads": True,
            "keep_cookies": True,
        },
    )
    assert r.status_code == 200
    p = r.json()["persistence"]
    assert p["downloads"] is True
    assert p["cookies"] is True


@patch("shadowbox.main.docker")
def test_identity_new(mock_docker: MagicMock) -> None:
    mock_docker.from_env.return_value = _docker_client()
    client.post("/start", json={"workspace": "default"})
    r = client.post("/identity/new", json={"workspace": "default"})
    assert r.status_code == 200
    assert r.json()["status"] == "rotated"


@patch("shadowbox.main.docker")
def test_purge(mock_docker: MagicMock) -> None:
    mock_docker.from_env.return_value = _docker_client()
    client.post("/start", json={"workspace": "default"})
    r = client.post("/purge")
    assert r.status_code == 200
    assert r.json()["status"] == "purged"
