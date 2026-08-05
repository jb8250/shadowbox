import logging
import os
import time

import docker
from docker.errors import DockerException, NotFound

logger = logging.getLogger(__name__)

# Default Tor control password for the dockurr/tor image (env PASSWORD=password).
# Can be overridden via the TOR_CONTROL_PASSWORD environment variable.
_DEFAULT_CONTROL_PASSWORD = "password"


class TorController:
    def __init__(self, client: docker.DockerClient) -> None:
        self.client = client
        self.container_name_prefix = "shadowbox-tor-"
        self.network_name = "shadowbox-net"
        self.control_port = 9051
        self.socks_port = 9050
        self.image = "dockurr/tor:latest"
        self.control_password = os.environ.get(
            "TOR_CONTROL_PASSWORD", _DEFAULT_CONTROL_PASSWORD
        )

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
                self.image,
                name=container_name,
                detach=True,
                ports={f"{self.socks_port}/tcp": self.socks_port},
                environment={
                    "TZ": "UTC",
                    "RUN_AS_ROOT": "true",
                    "PASSWORD": self.control_password,
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

    # ── NEWNYM: bash /dev/tcp implementation ──────────────────────────

    def _build_newnym_script(self) -> str:
        """Build a bash script that sends AUTHENTICATE + SIGNAL NEWNYM + QUIT.

        Uses ``bash /dev/tcp`` (a bash built-in) instead of ``nc``, which is
        not installed in the ``dockurr/tor`` Alpine image.  The control port
        (9051) binds to ``127.0.0.1`` inside the container, so the command
        runs *inside* the container via ``exec_run``.

        The password is read from the container's own ``$PASSWORD`` env var
        (set by the image's Dockerfile and our ``start()`` method), so it
        never appears in the script string or in any log output.
        """
        return (
            "exec 3<>/dev/tcp/127.0.0.1/{port} "
            "|| {{ echo 'CONTROL_PORT_UNREACHABLE'; exit 1; }}; "
            "printf 'AUTHENTICATE \"%s\"\\r\\nSIGNAL NEWNYM\\r\\nQUIT\\r\\n' "
            '"$PASSWORD" >&3; '
            "cat <&3; "
            "exec 3>&-"
        ).format(port=self.control_port)

    def _parse_newnym_response(self, output: str) -> None:
        """Parse the Tor control-protocol response from a NEWNYM sequence.

        Validates that both AUTHENTICATE and SIGNAL NEWNYM returned a
        ``250`` status code.  Raises ``RuntimeError`` with a **safe** message
        (no password, no raw response body) on any failure.

        Tor control-protocol status codes we check:
          - ``250`` / ``250 OK`` — success
          - ``515`` — bad authentication (wrong password)
          - ``5xx`` — other server errors
          - ``CONTROL_PORT_UNREACHABLE`` — our script's own marker
        """
        lines = [l.strip() for l in output.split("\r\n") if l.strip()]

        # Check for our own control-port-unreachable marker.
        if "CONTROL_PORT_UNREACHABLE" in lines:
            raise RuntimeError(
                "Tor control port not reachable inside container "
                "(port 9051 may not be configured)"
            )

        # Check for authentication failure.
        for line in lines:
            if line.startswith("515"):
                raise RuntimeError(
                    "Tor authentication failed (incorrect password)"
                )

        # Count successful 250 responses (AUTHENTICATE + SIGNAL NEWNYM).
        ok_count = sum(1 for l in lines if l.startswith("250"))
        if ok_count < 2:
            # Return only the numeric status codes, never the full text.
            codes = [l.split()[0] for l in lines if l and l[:1].isdigit()]
            raise RuntimeError(
                f"Tor NEWNYM signal failed: unexpected response "
                f"(status codes: {codes})"
            )

    def new_identity(self, workspace_name: str) -> None:
        """Rotate Tor circuits by sending SIGNAL NEWNYM to the control port.

        Uses ``container.exec_run`` with a bash ``/dev/tcp`` script instead
        of shelling out to ``nc`` (not installed in the Alpine-based
        ``dockurr/tor`` image) or a host-side Python socket (the control port
        only listens on 127.0.0.1 *inside* the container).

        The ``$PASSWORD`` env var is used inside the script so the control
        password never appears in the command string, process list, or any
        error message.
        """
        container_name = f"{self.container_name_prefix}{workspace_name}"
        container = self.client.containers.get(container_name)

        script = self._build_newnym_script()
        exec_result = container.exec_run(["bash", "-c", script])

        # exec_run returns ExecResult; output is bytes when stream=False (default).
        raw_output: bytes = exec_result.output  # type: ignore[assignment]

        if exec_result.exit_code != 0:
            output = raw_output.decode("utf-8", errors="replace").strip()
            # Handle the control-port-unreachable marker from the script.
            if "CONTROL_PORT_UNREACHABLE" in output:
                raise RuntimeError(
                    "Tor control port not reachable inside container "
                    "(port 9051 may not be configured)"
                )
            raise RuntimeError(
                f"Tor NEWNYM command failed (exit code {exec_result.exit_code})"
            )

        output = raw_output.decode("utf-8", errors="replace")
        self._parse_newnym_response(output)
        logger.info("Tor identity rotated for workspace %s", workspace_name)

    # ── Lifecycle ──────────────────────────────────────────────────────

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
