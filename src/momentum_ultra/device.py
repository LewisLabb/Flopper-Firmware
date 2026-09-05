"""Module for Flipper Zero device detection and serial port management."""

from __future__ import annotations

from dataclasses import dataclass

import serial
import serial.tools.list_ports

FLIPPER_VID: int = 0x0483
FLIPPER_PID: int = 0x5740


class FlipperDeviceError(Exception):
    """Base exception for Flipper device detection and connection issues."""


class FlipperNotFoundError(FlipperDeviceError):
    """Raised when no Flipper Zero is detected on available serial ports."""


class MultipleFlipperFoundError(FlipperDeviceError):
    """Raised when more than one Flipper Zero is connected."""


class FlipperPortBusyError(FlipperDeviceError):
    """Raised when the Flipper Zero serial port is in use by another application."""


@dataclass(frozen=True)
class FlipperDevice:
    """Represents a detected Flipper Zero device."""

    port: str
    description: str
    serial_number: str | None = None


def find_flipper() -> FlipperDevice:
    """Find a connected Flipper Zero using USB VID and PID."""
    ports = serial.tools.list_ports.comports()
    flippers = [p for p in ports if p.vid == FLIPPER_VID and p.pid == FLIPPER_PID]

    if not flippers:
        raise FlipperNotFoundError(
            "Aucun Flipper Zero détecté. Vérifiez la connexion USB."
        )

    if len(flippers) > 1:
        raise MultipleFlipperFoundError(
            f"Plusieurs Flipper Zero détectés ({len(flippers)} appareils). Veuillez n'en brancher qu'un seul."
        )

    match = flippers[0]
    return FlipperDevice(
        port=match.device,
        description=match.description or "Flipper Zero",
        serial_number=match.serial_number,
    )


def is_port_available(port: str) -> bool:
    """Check if a serial port can be opened without conflict."""
    try:
        ser = serial.Serial(port=port, timeout=1.0)
        ser.close()
        return True
    except (serial.SerialException, OSError):
        return False
