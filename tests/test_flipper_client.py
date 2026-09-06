"""Unit tests for FlipperClient serial communication and storage safety."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import serial

from flopper.flipper_client import (
    CLI_ETX,
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
        self.raise_on_write: Exception | None = None
        self.raise_on_read: Exception | None = None
        self.raise_on_close: Exception | None = None

    def write(self, data: bytes) -> int:
        """Record written data or raise configured exception."""
        if self.raise_on_write is not None:
            raise self.raise_on_write
        self.written.append(data)
        return len(data)

    def read(self, size: int = 1) -> bytes:
        """Read bytes from the current response queue or raise exception."""
        if self.raise_on_read is not None:
            raise self.raise_on_read
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
        """Close mock stream or raise exception."""
        if self.raise_on_close is not None:
            raise self.raise_on_close
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


def test_list_dir_firmware_format() -> None:
    """Test parsing directory listing from literal firmware storage list output."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"\t[D] apps\r\n\t[F] key.sub 1024b\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3") as client,
    ):
        items = client.list_dir("/ext")
        assert items == [
            StorageItem(name="apps", is_dir=True, size=0),
            StorageItem(name="key.sub", is_dir=False, size=1024),
        ]


def test_list_dir_empty_folder() -> None:
    """Test list_dir on empty directory returns empty list without error."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"\tEmpty\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3") as client,
    ):
        items = client.list_dir("/ext/empty_dir")
        assert items == []


def test_list_dir_error() -> None:
    """Test list_dir raises FlipperCommandError on firmware storage error."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"Storage error: Directory not found\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3") as client,
        pytest.raises(FlipperCommandError) as exc_info,
    ):
        client.list_dir("/ext/invalid")
    assert "Erreur lors de la lecture du dossier" in str(exc_info.value)


def test_write_file_dry_run() -> None:
    """Test write_file does not write data when dry_run=True."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=True) as client,
    ):
        assert client.write_file("/ext/test.txt", b"hello") is True
        assert len(mock_serial.written) == 1  # Only initial sync


def test_write_file_real_mode_success() -> None:
    """Test write_file following exact firmware interactive flow."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",  # initial sync
            b"Just write your text data. New line by Ctrl+Enter, exit by Ctrl+C.\r\n",  # response to storage write
            b">: ",  # prompt after ETX
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=False) as client,
    ):
        content = b"TEST_PAYLOAD_DATA"
        assert client.write_file("/ext/test.txt", content) is True

        assert len(mock_serial.written) == 4
        assert mock_serial.written[0] == b"\r\n"
        assert mock_serial.written[1] == b"storage write /ext/test.txt\r\n"
        assert mock_serial.written[2] == content
        assert mock_serial.written[3] == CLI_ETX


def test_write_file_real_mode_error() -> None:
    """Test write_file when firmware returns storage error immediately."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",  # initial sync
            b"Storage error: fichier verrouille\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=False) as client,
        pytest.raises(FlipperCommandError) as exc_info,
    ):
        client.write_file("/ext/locked.txt", b"data")

    assert "fichier verrouille" in str(exc_info.value)
    # Verify neither content nor ETX was sent
    assert b"data" not in mock_serial.written
    assert CLI_ETX not in mock_serial.written


def test_read_file_dry_run_returns_empty() -> None:
    """read_file is a no-op returning empty bytes in dry_run (no command sent)."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=True) as client,
    ):
        assert client.read_file("/ext/nfc/card.nfc") == b""
        assert len(mock_serial.written) == 1  # only the initial sync


def test_read_file_binary_fidelity() -> None:
    """read_file returns the exact bytes, even non-UTF-8 ones embedding the prompt."""
    raw = b"\x00\x01" + b">: " + b"\xff\xfe\x89\x00"  # embeds the prompt marker
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",  # initial sync
            f"Size: {len(raw)}\r\n".encode(),  # size header
            raw,  # exactly len(raw) raw bytes
            b">: ",  # final prompt
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=False) as client,
    ):
        assert client.read_file("/ext/nfc/card.nfc") == raw
        assert mock_serial.written[1] == b"storage read /ext/nfc/card.nfc\r\n"


def test_read_file_storage_error() -> None:
    """read_file raises FlipperCommandError when the firmware reports an error."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"Storage error: file not found\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=False) as client,
        pytest.raises(FlipperCommandError, match="file not found"),
    ):
        client.read_file("/ext/nfc/missing.nfc")


def test_mkdir_dry_run() -> None:
    """Test mkdir does not write when dry_run=True."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=True) as client,
    ):
        assert client.mkdir("/ext/apps_new") is True
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
        assert b"storage remove" not in written_data


def test_send_cmd_modifying_blocked_in_dry_run() -> None:
    """Test that send_cmd blocks modifying commands when dry_run=True."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=True) as client,
    ):
        with pytest.raises(FlipperClientError, match="interdite en mode simulation"):
            client.send_cmd("storage remove /ext/apps")
        # Ensure no byte was sent on the serial port for this command
        assert len(mock_serial.written) == 1  # Only initial sync


def test_send_cmd_read_allowed_in_dry_run() -> None:
    """Test that send_cmd allows read commands when dry_run=True."""
    mock_serial = MockSerialStream(
        [
            b"\r\n>: ",
            b"\t[D] apps\r\n>: ",
        ]
    )
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=True) as client,
    ):
        output = client.send_cmd("storage list /ext")
        assert "[D] apps" in output


def test_serial_exception_wrapped_on_io() -> None:
    """Test that SerialException during read or write is wrapped into FlipperClientError."""
    mock_serial = MockSerialStream([b"\r\n>: "])
    with (
        patch("serial.Serial", return_value=mock_serial),
        FlipperClient(port="COM3", dry_run=False) as client,
    ):
        # Trigger write failure
        mock_serial.raise_on_write = serial.SerialException("Device disconnected")
        with pytest.raises(FlipperClientError, match="Erreur d'écriture"):
            client.send_cmd("storage info")

        # Trigger read failure
        mock_serial.raise_on_write = None
        mock_serial.raise_on_read = serial.SerialException("Read timed out")
        with pytest.raises(FlipperClientError, match="Erreur de lecture"):
            client.send_cmd("storage info")


def test_timeout_error() -> None:
    """Test timeout during prompt read raises FlipperTimeoutError."""
    mock_serial = MockSerialStream([])
    with (
        patch("serial.Serial", return_value=mock_serial),
        pytest.raises(FlipperTimeoutError) as exc_info,
    ):
        client = FlipperClient(port="COM3", timeout=0.03)
        client.connect()
    assert "Délai d'attente dépassé" in str(exc_info.value)
