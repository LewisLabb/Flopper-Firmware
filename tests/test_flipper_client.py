"""Unit tests for FlipperClient serial communication and storage safety."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import serial

from momentum_ultra.flipper_client import (
    DEFAULT_BACKUP_DIR,
    FlipperClient,
    FlipperClientError,
    FlipperCommandError,
    FlipperTimeoutError,
    StorageItem,
)


class MockSerialStream:
    """Mock serial port that feeds predefined byte responses."""

    def __init__(self, responses: list[bytes] | None = None) -> None:
        """Initialize mock stream with optional queued responses."""
        self.responses: list[bytes] = (
            list(responses) if responses is not None else [b"\r\n>: "]
        )
        self.written: list[bytes] = []
        self.is_open: bool = True
        self._current_response: bytes = b""
        self._pos: int = 0

    def write(self, data: bytes) -> int:
        """Record written data."""
        self.written.append(data)
        return len(data)

    def read(self, size: int = 1) -> bytes:
        """Read bytes from the current response queue."""
        if self._pos >= len(self._current_response):
            if self.responses:
                self._current_response = self.responses.pop(0)
                self._pos = 0
            else:
                return b""
        chunk = self._current_response[self._pos : self._pos + size]
        self._pos += len(chunk)
        return chunk

    def reset_input_buffer(self) -> None:
        """Reset input buffer stub."""

    def close(self) -> None:
        """Close mock stream."""
        self.is_open = False


def test_default_dry_run_is_true() -> None:
    """Test that FlipperClient enables dry_run mode by default."""
    client = FlipperClient(port="COM3")
    assert client.dry_run is True


def test_connect_and_context_manager() -> None:
    """Test connection lifecycle via context manager."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3") as client,
    ):
        assert client._serial is not None
        assert client._serial.is_open is True
    assert client._serial is None
    assert mock_serial.is_open is False


def test_connect_failure() -> None:
    """Test connection failure raises FlipperClientError."""
    with (
        patch("serial.Serial", side_effect=serial.SerialException("Port busy")),
        pytest.raises(FlipperClientError) as exc_info,
        FlipperClient(port="COM3"),
    ):
        pass
    assert "Impossible d'ouvrir le port série" in str(exc_info.value)


def test_send_cmd_success() -> None:
    """Test sending command and receiving parsed output."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",  # for initial sync
            b"storage list /ext\r\n[DIR] apps\r\n[FILE] test.txt 42B\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3") as client,
    ):
        output = client.send_cmd("storage list /ext")
        assert "[DIR] apps" in output
        assert "[FILE] test.txt 42B" in output


def test_list_dir_parsing() -> None:
    """Test parsing directory listing from storage list."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"storage list /ext\r\n[DIR] apps\r\n[DIR] assets\r\n[FILE] config.txt 100B\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3") as client,
    ):
        items = client.list_dir("/ext")
        assert len(items) == 3
        assert items[0] == StorageItem(name="apps", is_dir=True, size=0)
        assert items[1] == StorageItem(name="assets", is_dir=True, size=0)
        assert items[2] == StorageItem(name="config.txt", is_dir=False, size=100)


def test_list_dir_error() -> None:
    """Test list_dir raises FlipperCommandError on storage error."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"storage list /ext/invalid\r\nStorage error: Directory not found\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3") as client,
        pytest.raises(FlipperCommandError) as exc_info,
    ):
        client.list_dir("/ext/invalid")
    assert "Erreur lors de la lecture du dossier" in str(exc_info.value)


def test_mkdir_dry_run() -> None:
    """Test mkdir does not write when dry_run=True."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=True) as client,
    ):
        assert client.mkdir("/ext/apps_new") is True
        # Only the initial sync write occurred
        assert len(mock_serial.written) == 1
        assert b"storage mkdir" not in mock_serial.written[0]


def test_mkdir_real_mode() -> None:
    """Test mkdir sends command when dry_run=False."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"storage mkdir /ext/apps_new\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=False) as client,
    ):
        assert client.mkdir("/ext/apps_new") is True
        written_commands = b"".join(mock_serial.written)
        assert b"storage mkdir /ext/apps_new\r\n" in written_commands


def test_write_file_dry_run() -> None:
    """Test write_file does not write data when dry_run=True."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=True) as client,
    ):
        assert client.write_file("/ext/test.txt", b"hello") is True
        assert len(mock_serial.written) == 1


def test_write_file_real_mode() -> None:
    """Test write_file sends write command and bytes when dry_run=False."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"storage write /ext/test.txt\r\n>: ",
            b">: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=False) as client,
    ):
        assert client.write_file("/ext/test.txt", b"hello world") is True
        written_data = b"".join(mock_serial.written)
        assert b"storage write /ext/test.txt" in written_data
        assert b"hello world" in written_data


def test_backup_item_dry_run() -> None:
    """Test backup_item calculates target path without executing commands in dry_run."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=True) as client,
    ):
        target = client.backup_item("/ext/apps")
        assert target == f"{DEFAULT_BACKUP_DIR}/apps"
        assert len(mock_serial.written) == 1


def test_backup_item_real_mode() -> None:
    """Test backup_item executes rename in real mode without any delete call."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"storage mkdir /ext/backup\r\n>: ",
            b"storage rename /ext/apps /ext/backup/apps\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=False) as client,
    ):
        target = client.backup_item("/ext/apps")
        assert target == "/ext/backup/apps"
        written_data = b"".join(mock_serial.written)
        assert b"storage rename /ext/apps /ext/backup/apps" in written_data
        # Strictly verify storage remove is never sent
        assert b"storage remove" not in written_data


def test_timeout_error() -> None:
    """Test timeout during prompt read raises FlipperTimeoutError."""
    mock_serial = MockSerialStream([])  # No bytes returned -> triggers timeout
    with (
        patch("serial.Serial", return_value=mock_serial),
        pytest.raises(FlipperTimeoutError) as exc_info,
    ):
        client = FlipperClient(port="COM3", timeout=0.03)
        client.connect()
    assert "Délai d'attente dépassé" in str(exc_info.value)
