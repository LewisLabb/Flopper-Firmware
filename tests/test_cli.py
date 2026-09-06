"""Tests for the command-line interface."""

from __future__ import annotations

import json
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import serial

from flopper import __version__
from flopper.bundle import export_bundle
from flopper.cli import _build_parser, main
from flopper.device import FLIPPER_PID, FLIPPER_VID
from flopper.manifest import PackManifest


def _make_mock_flipper_port(device: str = "COM3") -> MagicMock:
    """Create a mock Flipper serial port."""
    return MagicMock(
        device=device,
        vid=FLIPPER_VID,
        pid=FLIPPER_PID,
        description="Flipper Zero Virtual COM Port",
        serial_number="flip_12345",
    )


class MockSerialClient:
    """Mock serial stream for CLI testing."""

    def __init__(self, response_text: str = "") -> None:
        self.is_open: bool = True
        self.written: list[bytes] = []
        self.response_text = response_text
        self._queue: bytes = b"\r\n>: "

    def open(self) -> None:
        self.is_open = True

    def write(self, data: bytes) -> int:
        self.written.append(data)
        if data.startswith(b"storage write"):
            self._queue = b"Just write text data. Exit by Ctrl+C.\r\n"
        elif self.response_text and data not in (b"\r\n", b"", b"\x03"):
            self._queue = f"{self.response_text}\r\n>: ".encode()
            self.response_text = ""
        else:
            self._queue = b"\r\n>: "
        return len(data)

    def read(self, size: int = 1) -> bytes:
        chunk, self._queue = self._queue[:size], self._queue[size:]
        return chunk or b">: "

    def reset_input_buffer(self) -> None:
        self._queue = b"\r\n>: "

    def close(self) -> None:
        self.is_open = False


@contextmanager
def _mock_flipper(
    device: str = "COM3", response_text: str = ""
) -> Generator[MockSerialClient, None, None]:
    mock_port = _make_mock_flipper_port(device)
    mock_serial = MockSerialClient(response_text)

    def _factory(*_args: object, **_kwargs: object) -> MockSerialClient:
        mock_serial.is_open = True
        return mock_serial

    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", side_effect=_factory),
    ):
        yield mock_serial


def test_main_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that --version displays the version string and exits with 0."""
    assert main(["--version"]) == 0
    assert __version__ in "".join(capsys.readouterr())


def test_main_no_args_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that running with no arguments prints help and exits with 0."""
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "flopper" in output.lower()
    assert "momentum-ultra" not in output.lower()


def test_main_help_theme_unqualified_absent(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --help does not include unqualified 'Thème visuel Momentum'."""
    main(["--help"])
    captured = capsys.readouterr().out
    assert "Thème visuel Momentum" not in captured
    assert "Profil de préférences visuelles Flopper" in captured


def test_dry_run_flag_parsing() -> None:
    """Test that dry-run is True by default and False with --no-dry-run."""
    parser = _build_parser()
    assert parser.parse_args([]).dry_run is True
    assert parser.parse_args(["--no-dry-run"]).dry_run is False
    assert parser.parse_args(["--dry-run"]).dry_run is True


def test_main_detect_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --detect when Flipper Zero is connected and port is available."""
    with _mock_flipper("COM3"):
        assert main(["--detect"]) == 0
        assert "Flipper Zero détecté sur COM3." in capsys.readouterr().out


def test_main_detect_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --detect when no Flipper Zero is connected."""
    with patch("serial.tools.list_ports.comports", return_value=[]):
        assert main(["--detect"]) == 1
        assert "Aucun Flipper Zero détecté" in capsys.readouterr().err


def test_main_detect_port_busy(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --detect when Flipper is found but port is locked by another program."""
    mock_port = _make_mock_flipper_port("COM3")
    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", side_effect=serial.SerialException("Access denied")),
    ):
        assert main(["--detect"]) == 1
        assert "mais le port est occupé" in capsys.readouterr().err


def test_main_detect_enumeration_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --detect handles serial enumeration errors gracefully without unhandled exception."""
    with patch(
        "serial.tools.list_ports.comports",
        side_effect=serial.SerialException("USB bus error"),
    ):
        assert main(["--detect"]) == 1
        assert "Impossible d'énumérer les ports série" in capsys.readouterr().err


def test_main_diagnose_modules(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --diagnose-modules prints supported modules offline without device."""
    assert main(["--diagnose-modules"]) == 0
    captured = capsys.readouterr().out
    assert "Modules externes pris en charge" in captured
    assert "CC1101" in captured


def test_main_install_dry_run_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install runs in simulation mode by default without prompt."""
    with _mock_flipper():
        assert main(["--install"]) == 0
        out = capsys.readouterr().out
        assert "SIMULATION (--dry-run)" in out
        assert "Préparation terminée avec succès" in out


def test_main_install_with_region_us(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install with --region US."""
    with _mock_flipper():
        assert main(["--install", "--region", "US"]) == 0
        assert "États-Unis" in capsys.readouterr().out


def test_main_install_with_region_world_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --install with --region WORLD displays legal notice."""
    with _mock_flipper():
        assert main(["--install", "--region", "WORLD"]) == 0
        notice = (
            "Attention : Le profil WORLD déverrouille les restrictions fréquentielles."
        )
        assert notice in capsys.readouterr().out


def test_main_install_no_dry_run_cancelled(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install with --no-dry-run is cancelled when user inputs 'n'."""
    with _mock_flipper(), patch("builtins.input", return_value="n"):
        assert main(["--install", "--no-dry-run"]) == 0
        assert "Installation annulée par l'utilisateur." in capsys.readouterr().out


def test_main_install_no_dry_run_yes_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install with --no-dry-run and -y flag executes real mode directly."""
    with _mock_flipper():
        assert main(["--install", "--no-dry-run", "-y"]) == 0
        out = capsys.readouterr().out
        assert "ÉCRITURE RÉELLE" in out
        assert "Préparation terminée avec succès !" in out


def test_main_install_modules_declared() -> None:
    """Test --install with --modules writes declared modules into modules.json."""
    with (
        _mock_flipper(),
        patch("flopper.cli.execute_install_plan") as mock_exec,
    ):
        assert main(["--install", "--modules", "cc1101,nrf24", "--dry-run"]) == 0
        plan = mock_exec.call_args.args[1]
        action = next(a for a in plan if a.target_path == "/ext/settings/modules.json")
        assert action.source_content is not None
        data = json.loads(action.source_content.decode("utf-8"))
        assert data["enabled"] is True
        assert [m["type"] for m in data["active_modules"]] == ["cc1101", "nrf24"]


def test_main_install_modules_default_empty() -> None:
    """Test --install without --modules writes empty active_modules list in modules.json."""
    with (
        _mock_flipper(),
        patch("flopper.cli.execute_install_plan") as mock_exec,
    ):
        assert main(["--install", "--dry-run"]) == 0
        plan = mock_exec.call_args.args[1]
        action = next(a for a in plan if a.target_path == "/ext/settings/modules.json")
        assert action.source_content is not None
        data = json.loads(action.source_content.decode("utf-8"))
        assert data["enabled"] is False
        assert data["active_modules"] == []


def test_main_install_modules_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install with unknown module fails with French error message."""
    with _mock_flipper():
        assert main(["--install", "--modules", "inconnu", "--dry-run"]) == 1
        assert "Module inconnu 'inconnu'" in capsys.readouterr().err


def test_main_export_bundle(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test --export-bundle writes a tar.gz bundle."""
    dest = tmp_path / "exported.tar.gz"
    assert main(["--export-bundle", str(dest)]) == 0
    assert dest.exists()
    assert "exporté avec succès" in capsys.readouterr().out


def test_main_install_custom_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --install with --bundle using a custom pack."""
    pack = PackManifest(name="custom-pack-xyz", version="3.0.0", apps=[])
    bundle_file = tmp_path / "custom.tar.gz"
    export_bundle(pack, bundle_file)
    with _mock_flipper():
        assert main(["--install", "--bundle", str(bundle_file)]) == 0
        assert "custom-pack-xyz" in capsys.readouterr().out


def test_main_install_custom_bundle_with_world_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --install with --bundle and --region WORLD displays legal notice."""
    pack = PackManifest(name="custom-world", version="1.0.0", apps=[])
    bundle_file = tmp_path / "world_bundle.tar.gz"
    export_bundle(pack, bundle_file)
    with _mock_flipper():
        cmd = [
            "--install",
            "--region",
            "WORLD",
            "--bundle",
            str(bundle_file),
            "--dry-run",
        ]
        assert main(cmd) == 0
        assert "Attention : Le profil WORLD déverrouille" in capsys.readouterr().out


def test_main_install_with_theme(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install with --theme option."""
    with _mock_flipper():
        assert main(["--install", "--theme", "dark_stealth"]) == 0
        assert "Dark Stealth" in capsys.readouterr().out


def test_main_backup_captures(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --backup-captures command."""
    dest_dir = tmp_path / "captures_out"
    with _mock_flipper(response_text="\t[F] key.sub 128b"):
        assert main(["--backup-captures", str(dest_dir)]) == 0
        assert "Sauvegarde terminée" in capsys.readouterr().out


def test_main_list_payloads(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --list-payloads command."""
    assert main(["--list-payloads"]) == 0
    assert "Bibliothèque de payloads BadUSB" in capsys.readouterr().out
