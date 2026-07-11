import time
import docker
from docker.errors import DockerException, NotFound


class TorController:
    def __init__(self, client: docker.DockerClient) -> None:
        self.client = client
        self.container_name_prefix = "shadowbox-tor-"
        self.network_name = "shadowbox-net"
        self.control_port = 9051
        self.socks_port = 9050

    def ensure_network(self) -> None:
        try:
            self.client.networks.get(self.network_name)
        except NotFound:
            self.client.networks.create(self.network_name, driver="bridge")

    def start(self, workspace_name: str) -> str:
        self.ensure_network()
        container_name = f"{self.container_name_prefix}{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            if container.status != "running":
                container.start()
            self._wait_until_ready(container)
        except NotFound:
            container = self.client.containers.run(
                "dperson/torproxy:latest",
                name=container_name,
                detach=True,
                ports={f"{self.socks_port}/tcp": self.socks_port},
                environment={
                    "TZ": "UTC",
                    "RUN_AS_ROOT": "true",
                },
                network=self.network_name,
                restart_policy={"Name": "unless-stopped"},
            )
            self._wait_until_ready(container)
        return container_name

    def _wait_until_ready(self, container, timeout: int = 90) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            container.reload()
            if container.status == "running":
                logs = container.logs(tail=20).decode("utf-8", errors="ignore")
                if "Bootstrapped 100%" in logs:
                    return
            time.sleep(1)
        raise RuntimeError("Tor container failed to bootstrap within timeout")

    def new_identity(self, workspace_name: str) -> None:
        container_name = f"{self.container_name_prefix}{workspace_name}"
        container = self.client.containers.get(container_name)
        exec_result = container.exec_run(
            "torify curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip"
        )
        if exec_result.exit_code != 0:
            raise RuntimeError("Tor identity reset (NEWNYM) not yet available")

    def stop(self, workspace_name: str) -> None:
        container_name = f"{self.container_name_prefix}{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            container.stop()
        except NotFound:
            pass

    def remove(self, workspace_name: str) -> None:
        container_name = f"{self.container_name_prefix}{workspace_name}"
        try:
            container = self.client.containers.get(container_name)
            container.remove(v=True)
        except NotFound:
            pass
