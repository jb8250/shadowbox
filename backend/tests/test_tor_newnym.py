"""Unit tests for TorController NEWNYM (circuit rotation) functionality.

Tests cover:
  - Successful Tor authentication + SIGNAL NEWNYM
  - Authentication failure (wrong password → 515)
  - Control-port connection failure
  - Unexpected Tor responses
  - Script generation correctness (no password leakage in command string)

All tests use mocks — no real Docker or Tor containers required.
"""

import pytest
from unittest.mock import MagicMock, patch

from shadowbox.tor import TorController


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_exec_result(exit_code: int, output: bytes) -> MagicMock:
    """Create a mock ExecResult with the given exit code and output."""
    result = MagicMock()
    result.exit_code = exit_code
    result.output = output
    return result


def _make_tor_controller() -> TorController:
    """Create a TorController with a mocked Docker client."""
    client = MagicMock()
    return TorController(client)


# ── Script generation tests ─────────────────────────────────────────────────

class TestBuildNewnymScript:
    """Test that _build_newnym_script produces a safe, correct bash script."""

    def test_script_does_not_contain_password(self) -> None:
        """The control password must never appear in the script string."""
        tc = _make_tor_controller()
        tc.control_password = "super_secret_123"
        script = tc._build_newnym_script()
        assert "super_secret_123" not in script
        assert "password" not in script.lower() or "$PASSWORD" in script

    def test_script_references_password_env_var(self) -> None:
        """Script should read the password from $PASSWORD env var."""
        tc = _make_tor_controller()
        script = tc._build_newnym_script()
        assert "$PASSWORD" in script

    def test_script_uses_dev_tcp(self) -> None:
        """Script should use bash /dev/tcp built-in, not nc."""
        tc = _make_tor_controller()
        script = tc._build_newnym_script()
        assert "/dev/tcp/127.0.0.1/9051" in script
        assert "nc " not in script

    def test_script_sends_authenticate_newnym_quit(self) -> None:
        """Script should send AUTHENTICATE, SIGNAL NEWNYM, and QUIT."""
        tc = _make_tor_controller()
        script = tc._build_newnym_script()
        assert "AUTHENTICATE" in script
        assert "SIGNAL NEWNYM" in script
        assert "QUIT" in script

    def test_script_uses_control_port(self) -> None:
        """Script should reference the configured control port."""
        tc = _make_tor_controller()
        tc.control_port = 9051
        script = tc._build_newnym_script()
        assert "9051" in script

    def test_script_includes_control_port_unreachable_marker(self) -> None:
        """Script should emit CONTROL_PORT_UNREACHABLE on connection failure."""
        tc = _make_tor_controller()
        script = tc._build_newnym_script()
        assert "CONTROL_PORT_UNREACHABLE" in script


# ── Response parsing tests ──────────────────────────────────────────────────

class TestParseNewnymResponse:
    """Test _parse_newnym_response with various Tor control-protocol outputs."""

    def test_successful_newnym(self) -> None:
        """Two 250 OK responses = success."""
        tc = _make_tor_controller()
        output = "250 OK\r\n250 OK\r\n"
        # Should not raise
        tc._parse_newnym_response(output)

    def test_successful_newnym_with_extra_whitespace(self) -> None:
        """Success with extra CRLF padding."""
        tc = _make_tor_controller()
        output = "\r\n250 OK\r\n\r\n250 OK\r\n\r\n"
        tc._parse_newnym_response(output)

    def test_authentication_failure_515(self) -> None:
        """515 response = bad password → RuntimeError with safe message."""
        tc = _make_tor_controller()
        output = "515 Bad authentication\r\n"
        with pytest.raises(RuntimeError, match="authentication failed"):
            tc._parse_newnym_response(output)

    def test_authentication_failure_no_password_in_message(self) -> None:
        """Error message must not contain the password."""
        tc = _make_tor_controller()
        tc.control_password = "my_secret_pw"
        output = "515 Bad authentication\r\n"
        with pytest.raises(RuntimeError) as exc_info:
            tc._parse_newnym_response(output)
        assert "my_secret_pw" not in str(exc_info.value)

    def test_control_port_unreachable(self) -> None:
        """CONTROL_PORT_UNREACHABLE marker → RuntimeError."""
        tc = _make_tor_controller()
        output = "CONTROL_PORT_UNREACHABLE\r\n"
        with pytest.raises(RuntimeError, match="control port not reachable"):
            tc._parse_newnym_response(output)

    def test_unexpected_response_single_250(self) -> None:
        """Only one 250 (e.g., AUTHENTICATE succeeded but NEWNYM failed)."""
        tc = _make_tor_controller()
        output = "250 OK\r\n510 Command not recognized\r\n"
        with pytest.raises(RuntimeError, match="unexpected response"):
            tc._parse_newnym_response(output)

    def test_unexpected_response_empty(self) -> None:
        """No response lines at all."""
        tc = _make_tor_controller()
        output = ""
        with pytest.raises(RuntimeError, match="unexpected response"):
            tc._parse_newnym_response(output)

    def test_unexpected_response_no_password_in_message(self) -> None:
        """Error message must not leak password even on unexpected response."""
        tc = _make_tor_controller()
        tc.control_password = "leaked_pw_test"
        output = "552 Unrecognized command\r\n"
        with pytest.raises(RuntimeError) as exc_info:
            tc._parse_newnym_response(output)
        assert "leaked_pw_test" not in str(exc_info.value)

    def test_5xx_error(self) -> None:
        """Generic 5xx error from Tor."""
        tc = _make_tor_controller()
        output = "510 Command not recognized\r\n"
        with pytest.raises(RuntimeError, match="unexpected response"):
            tc._parse_newnym_response(output)


# ── new_identity integration tests (mocked exec_run) ─────────────────────

class TestNewIdentity:
    """Test new_identity() with mocked container exec_run."""

    def _setup_container(self, exec_result: MagicMock) -> tuple[TorController, MagicMock]:
        """Create a TorController with a mock container returning exec_result."""
        client = MagicMock()
        container = MagicMock()
        container.exec_run.return_value = exec_result
        client.containers.get.return_value = container
        tc = TorController(client)
        return tc, container

    def test_successful_newnym(self) -> None:
        """Successful NEWNYM with two 250 OK responses."""
        exec_result = _make_exec_result(0, b"250 OK\r\n250 OK\r\n")
        tc, container = self._setup_container(exec_result)

        tc.new_identity("default")

        # Verify exec_run was called with ["bash", "-c", script]
        container.exec_run.assert_called_once()
        call_args = container.exec_run.call_args
        cmd_list = call_args[0][0]  # first positional arg is the list
        assert cmd_list[0] == "bash"
        assert cmd_list[1] == "-c"

    def test_authentication_failure(self) -> None:
        """515 response raises RuntimeError about authentication."""
        exec_result = _make_exec_result(0, b"515 Bad authentication\r\n")
        tc, _ = self._setup_container(exec_result)

        with pytest.raises(RuntimeError, match="authentication failed"):
            tc.new_identity("default")

    def test_control_port_connection_failure_exit_nonzero(self) -> None:
        """exec_run returns exit code 1 with CONTROL_PORT_UNREACHABLE."""
        exec_result = _make_exec_result(1, b"CONTROL_PORT_UNREACHABLE\r\n")
        tc, _ = self._setup_container(exec_result)

        with pytest.raises(RuntimeError, match="control port not reachable"):
            tc.new_identity("default")

    def test_exec_command_failure_exit_nonzero(self) -> None:
        """exec_run returns non-zero exit code without unreachable marker."""
        exec_result = _make_exec_result(127, b"command not found\r\n")
        tc, _ = self._setup_container(exec_result)

        with pytest.raises(RuntimeError, match="exit code 127"):
            tc.new_identity("default")

    def test_unexpected_tor_response(self) -> None:
        """Tor returns a response without enough 250 codes."""
        exec_result = _make_exec_result(0, b"250 OK\r\n510 Command not recognized\r\n")
        tc, _ = self._setup_container(exec_result)

        with pytest.raises(RuntimeError, match="unexpected response"):
            tc.new_identity("default")

    def test_password_not_in_exec_command(self) -> None:
        """The control password must never appear in the exec command."""
        exec_result = _make_exec_result(0, b"250 OK\r\n250 OK\r\n")
        tc, container = self._setup_container(exec_result)
        tc.control_password = "super_secret_xyz"

        tc.new_identity("default")

        call_args = container.exec_run.call_args
        cmd_list = call_args[0][0]  # first positional arg is the list
        script_arg = cmd_list[2]
        assert "super_secret_xyz" not in script_arg

    def test_script_not_nc_based(self) -> None:
        """The exec command must not invoke nc."""
        exec_result = _make_exec_result(0, b"250 OK\r\n250 OK\r\n")
        tc, container = self._setup_container(exec_result)

        tc.new_identity("default")

        call_args = container.exec_run.call_args
        cmd_list = call_args[0][0]
        script_arg = cmd_list[2]
        assert "nc " not in script_arg
        assert "ncat" not in script_arg
        assert "netcat" not in script_arg


# ── Start/container tests ──────────────────────────────────────────────────

from docker.errors import NotFound as _NotFound


class TestStartContainer:
    """Test that start() uses the dockurr/tor image and sets PASSWORD env."""

    def _make_mock_client(self) -> MagicMock:
        """Create a mock Docker client where the container doesn't exist yet."""
        client = MagicMock()
        # ensure_network: networks.get raises NotFound → networks.create called
        client.networks.get.side_effect = _NotFound("not found")
        client.networks.create.return_value = MagicMock()
        # start: containers.get raises NotFound → containers.run called
        client.containers.get.side_effect = _NotFound("not found")
        container = MagicMock()
        container.status = "running"
        container.logs.return_value = b"Bootstrapped 100%"
        client.containers.run.return_value = container
        return client

    def test_uses_dockurr_tor_image(self) -> None:
        """start() should use dockurr/tor:latest, not dperson/torproxy."""
        client = self._make_mock_client()

        tc = TorController(client)
        tc.start("default")

        call_args = client.containers.run.call_args
        # image is passed as first positional arg to containers.run()
        image_arg = call_args[0][0]
        assert image_arg == "dockurr/tor:latest"

    def test_sets_password_env(self) -> None:
        """start() should pass PASSWORD env var to the container."""
        client = self._make_mock_client()

        tc = TorController(client)
        tc.control_password = "test_password_123"
        tc.start("default")

        call_kwargs = client.containers.run.call_args[1]
        env = call_kwargs["environment"]
        assert env["PASSWORD"] == "test_password_123"

    def test_does_not_use_dperson_torproxy(self) -> None:
        """Image must NOT be dperson/torproxy (the abandoned image)."""
        client = self._make_mock_client()

        tc = TorController(client)
        tc.start("default")

        call_args = client.containers.run.call_args
        image_arg = call_args[0][0]
        assert "dperson" not in image_arg
        assert "torproxy" not in image_arg
