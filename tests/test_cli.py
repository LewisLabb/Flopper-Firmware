"""Tests for the command-line interface."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import serial

from momentum_ultra import __version__
from momentum_ultra.bundle import export_bundle
from momentum_ultra.cli import _build_parser, main
from momentum_ultra.device import FLIPPER_PID, FLIPPER_VID
from momentum_ultra.manifest import AppEntry, PackManifest


def _make_mock_flipper_port(device: str = "COM3") -> MagicMock:
    """Create a mock Flipper serial port."""
    port = MagicMock()
    port.device = device
    port.vid = FLIPPER_VID
    port.pid = FLIPPER_PID
    port.description = "Flipper Zero Virtual COM Port"
    port.serial_number = "flip_12345"
    return port


class MockSerialClient:
    """Mock serial stream for CLI testing."""

    def __init__(self, response_text: str = "") -> None:
        """Initialize mock serial connection."""
        self.is_open: bool = True
        self.written: list[bytes] = []
        self.response_text = response_text

    def write(self, data: bytes) -> int:
        """Record written bytes."""
        self.written.append(data)
        return len(data)

    def read(self, size: int = 1) -> bytes:
        """Return prompt marker with optional response text."""
        last_written = self.written[-1] if self.written else b""
        if self.response_text and last_written not in (b"\r\n", b""):
            out = f"{self.response_text}\r\n>: ".encode()
            self.response_text = ""
            return out
        return b">: "

    def reset_input_buffer(self) -> None:
        """Stub reset buffer."""

    def close(self) -> None:
        """Close mock stream."""
        self.is_open = False


def test_main_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that --version displays the version string and exits with 0."""
    exit_code = main(["--version"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert __version__ in (captured.out + captured.err)


def test_main_no_args_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that running with no arguments prints help and exits with 0."""
    exit_code = main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "momentum-ultra" in captured.out


def test_dry_run_flag_parsing() -> None:
    """Test that dry-run is True by default and False with --no-dry-run."""
    parser = _build_parser()
    args_default = parser.parse_args([])
    assert args_default.dry_run is True

    args_no_dry_run = parser.parse_args(["--no-dry-run"])
    assert args_no_dry_run.dry_run is False

    args_dry_run = parser.parse_args(["--dry-run"])
    assert args_dry_run.dry_run is True


def test_main_detect_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --detect when Flipper Zero is connected and port is available."""
    mock_port = _make_mock_flipper_port("COM3")
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial"),
    ):
        exit_code = main(["--detect"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Flipper Zero détecté sur COM3." in captured.out


def test_main_detect_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --detect when no Flipper Zero is connected."""
    with patch("serial.tools.list_ports.comports", return_value=[]):
        exit_code = main(["--detect"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Aucun Flipper Zero détecté" in captured.err


def test_main_detect_port_busy(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --detect when Flipper is found but port is locked by another program."""
    mock_port = _make_mock_flipper_port("COM3")
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", side_effect=serial.SerialException("Access denied")),
    ):
        exit_code = main(["--detect"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "mais le port est occupé" in captured.err


def test_main_diagnose_modules(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --diagnose-modules detects connected hardware modules."""
    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient(response_text="SPI device: CC1101 active")
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
    ):
        exit_code = main(["--diagnose-modules"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "CC1101" in captured.out


def test_main_install_dry_run_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install runs in simulation mode by default without prompt."""
    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient()
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
    ):
        exit_code = main(["--install"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "SIMULATION (--dry-run)" in captured.out
        assert "Préparation terminée avec succès" in captured.out
        assert "Conseils pour le premier démarrage" in captured.out


def test_main_install_with_region_us(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install with --region US."""
    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient()
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
    ):
        exit_code = main(["--install", "--region", "US"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "États-Unis" in captured.out


def test_main_install_with_region_world_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --install with --region WORLD displays legal notice."""
    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient()
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
    ):
        exit_code = main(["--install", "--region", "WORLD"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Avertissement Légal" in captured.out


def test_main_install_no_dry_run_cancelled(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --install with --no-dry-run is cancelled when user inputs 'n'."""
    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient()
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
        patch("builtins.input", return_value="n"),
    ):
        exit_code = main(["--install", "--no-dry-run"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Installation annulée par l'utilisateur." in captured.out


def test_main_install_no_dry_run_yes_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --install with --no-dry-run and -y flag executes real mode directly."""
    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient()
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
    ):
        exit_code = main(["--install", "--no-dry-run", "-y"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "ÉCRITURE RÉELLE" in captured.out
        assert "Préparation terminée avec succès !" in captured.out


def test_main_export_bundle(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test --export-bundle writes a tar.gz bundle."""
    dest = tmp_path / "exported.tar.gz"
    exit_code = main(["--export-bundle", str(dest)])
    assert exit_code == 0
    assert dest.exists()
    captured = capsys.readouterr()
    assert "exporté avec succès" in captured.out


def test_main_install_custom_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --install with --bundle using a custom pack."""
    custom_pack = PackManifest(
        name="custom-pack-xyz",
        version="3.0.0",
        apps=[
            AppEntry(name="AppX", category="Tools", filename="x.fap", content=b"123")
        ],
    )
    bundle_file = tmp_path / "custom.tar.gz"
    export_bundle(custom_pack, bundle_file)

    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient()
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
    ):
        exit_code = main(["--install", "--bundle", str(bundle_file)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "custom-pack-xyz" in captured.out
        assert "Préparation terminée avec succès" in captured.out


def test_main_install_with_theme(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install with --theme option."""
    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient()
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
    ):
        exit_code = main(["--install", "--theme", "dark_stealth"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Dark Stealth" in captured.out


def test_main_backup_captures(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --backup-captures command."""
    mock_port = _make_mock_flipper_port("COM3")
    mock_serial = MockSerialClient(response_text="[F] key.sub 128B")
    dest_dir = tmp_path / "captures_out"
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
    ):
        exit_code = main(["--backup-captures", str(dest_dir)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Sauvegarde terminée" in captured.out
