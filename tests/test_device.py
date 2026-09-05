"""Unit tests for Flipper device detection and serial port availability."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import serial

from momentum_ultra.device import (
    FLIPPER_PID,
    FLIPPER_VID,
    FlipperDevice,
    FlipperNotFoundError,
    MultipleFlipperFoundError,
    find_flipper,
    is_port_available,
)


def _make_mock_port(
    device: str,
    vid: int | None = None,
    pid: int | None = None,
    description: str = "Test Port",
    serial_number: str | None = None,
) -> MagicMock:
    """Create a mock serial port information object."""
    port = MagicMock()
    port.device = device
    port.vid = vid
    port.pid = pid
    port.description = description
    port.serial_number = serial_number
    return port


def test_find_flipper_success() -> None:
    """Test finding exactly one connected Flipper Zero."""
    mock_port = _make_mock_port(
        device="COM3",
        vid=FLIPPER_VID,
        pid=FLIPPER_PID,
        description="Flipper Zero Virtual COM Port",
        serial_number="flip_12345",
    )
    with patch("serial.tools.list_ports.comports", return_value=[mock_port]):
        device = find_flipper()
        assert isinstance(device, FlipperDevice)
        assert device.port == "COM3"
        assert device.description == "Flipper Zero Virtual COM Port"
        assert device.serial_number == "flip_12345"


def test_find_flipper_not_found_empty_ports() -> None:
    """Test finding Flipper when no ports are detected at all."""
    with patch("serial.tools.list_ports.comports", return_value=[]):
        with pytest.raises(FlipperNotFoundError) as exc_info:
            find_flipper()
        assert "Aucun Flipper Zero détecté" in str(exc_info.value)


def test_find_flipper_not_found_non_matching_vid_pid() -> None:
    """Test finding Flipper when only other USB devices are present."""
    other_port = _make_mock_port(device="COM1", vid=0x1234, pid=0x5678)
    with patch("serial.tools.list_ports.comports", return_value=[other_port]):
        with pytest.raises(FlipperNotFoundError) as exc_info:
            find_flipper()
        assert "Aucun Flipper Zero détecté" in str(exc_info.value)


def test_find_flipper_multiple_devices() -> None:
    """Test finding Flipper when more than one matching device is connected."""
    port1 = _make_mock_port(device="COM3", vid=FLIPPER_VID, pid=FLIPPER_PID)
    port2 = _make_mock_port(device="COM4", vid=FLIPPER_VID, pid=FLIPPER_PID)
    with patch("serial.tools.list_ports.comports", return_value=[port1, port2]):
        with pytest.raises(MultipleFlipperFoundError) as exc_info:
            find_flipper()
        assert "Plusieurs Flipper Zero détectés" in str(exc_info.value)


def test_is_port_available_success() -> None:
    """Test is_port_available returns True when port opens cleanly."""
    mock_serial_instance = MagicMock()
    with patch("serial.Serial", return_value=mock_serial_instance) as mock_serial:
        assert is_port_available("COM3") is True
        mock_serial.assert_called_once_with(port="COM3", timeout=1.0)
        mock_serial_instance.close.assert_called_once()


def test_is_port_available_busy() -> None:
    """Test is_port_available returns False when port opening raises SerialException."""
    with patch("serial.Serial", side_effect=serial.SerialException("Access denied")):
        assert is_port_available("COM3") is False


def test_is_port_available_os_error() -> None:
    """Test is_port_available returns False when port opening raises OSError."""
    with patch("serial.Serial", side_effect=OSError("Device not configured")):
        assert is_port_available("COM3") is False
