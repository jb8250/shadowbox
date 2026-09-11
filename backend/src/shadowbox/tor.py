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
                "dockurr/tor:latest",
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
        """Send a genuine NEWNYM signal to the Tor control port to rotate circuits.

        The dockurr/tor image uses password authentication by default with
        PASSWORD="password". AUTHENTICATE must include the password in quotes.
        """
        container_name = f"{self.container_name_prefix}{workspace_name}"
        container = self.client.containers.get(container_name)
        # Send AUTHENTICATE "password" + SIGNAL NEWNYM + QUIT to control port 9051
        cmd = (
            'printf "AUTHENTICATE \\\"password\\\"\\r\\nSIGNAL NEWNYM\\r\\nQUIT\\r\\n" | '
            'timeout 5 nc 127.0.0.1 9051'
        )
        exec_result = container.exec_run(["sh", "-c", cmd])
        if exec_result.exit_code != 0:
            raise RuntimeError(
                f"Tor NEWNYM signal failed (exit {exec_result.exit_code}): "
                f"{exec_result.output.decode('utf-8', errors='replace').strip()}"
            )
        output = exec_result.output.decode("utf-8", errors="replace").strip()
        if "250 OK" not in output:
            raise RuntimeError(f"Tor NEWNYM signal rejected: {output}")

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
