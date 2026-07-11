import time
from typing import Optional
import docker
from docker.errors import DockerException, NotFound


FLAGS = [
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--disable-component-extensions-with-background-pages",
    "--disable-background-networking",
    "--disable-sync",
    "--disable-translate",
    "--disable-default-apps",
    "--no-proxy-server",
    "--proxy-server=\"socks5://tor:9050\"",
    "--host-resolver-rules=\"MAP * ~NOTFOUND , EXCLUDE tor\"",
    "--disable-quic",
    "--disable-webrtc",
    "--disable-password-generation",
    "--disable-autofill-keyboard-accessory-view",
    "--disable-features=OptimizationHints,OptimizationTargetPrediction,PredictivePrefetching",
    "--disable-logging",
    "--metrics-recording-only",
    "--mute-audio",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
]


class BrowserController:
    def __init__(self, client: docker.DockerClient) -> None:
        self.client = client
        self.network_name = "shadowbox-net"
        self.container_name_prefix = "shadowbox-browser-"
        self.volume_prefix = "shadowbox-"
        self.vnc_port = 3001
        self.image = "lscr.io/linuxserver/ungoogled-chromium:latest"

    def start(self, workspace_name: str) -> str:
        volume_name = f"{self.volume_prefix}{workspace_name}"
        try:
            self.client.volumes.get(volume_name)
        except NotFound:
            self.client.volumes.create(volume_name)

        container_name = f"{self.container_name_prefix}{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            if container.status != "running":
                container.start()
        except NotFound:
            container = self.client.containers.run(
                self.image,
                name=container_name,
                detach=True,
                ports={f"{self.vnc_port}/tcp": self.vnc_port},
                volumes={volume_name: {"bind": "/config", "mode": "rw"}},
                environment={
                    "DISPLAY": ":1",
                    "VNC_PASSWORD": "",
                    "UMASK": "000",
                },
                network=self.network_name,
                command=FLAGS,
                labels={"shadowbox": "browser"},
            )
        self._wait_vnc_ready(container)
        return container_name

    def _wait_vnc_ready(self, container, timeout: int = 90) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            container.reload()
            if container.status == "running":
                return
            time.sleep(1)
        raise RuntimeError("Browser container failed to start within timeout")

    def stop(self, workspace_name: str, keep: bool = False) -> None:
        container_name = f"{self.container_name_prefix}{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            if not keep:
                volume_name = f"{self.volume_prefix}{workspace_name}"
                try:
                    self.client.volumes.get(volume_name).remove()
                except NotFound:
                    pass
                container.remove(v=True)
        except NotFound:
            pass

    def remove(self, workspace_name: str) -> None:
        container_name = f"{self.container_name_prefix}{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            container.remove(v=True, force=True)
        except NotFound:
            pass
        volume_name = f"{self.volume_prefix}{workspace_name}"
        try:
            vol = self.client.volumes.get(volume_name)
            vol.remove()
        except NotFound:
            pass

    def vnc_url(self, workspace_name: str) -> str:
        return f"http://localhost:{self.vnc_port}"
