"""Unit tests for regional profiles and radio frequency regulations."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from flopper.cli import main
from flopper.device import FLIPPER_PID, FLIPPER_VID
from flopper.installer import build_region_settings_action
from flopper.manifest import ActionType, PlanAction
from flopper.regions import (
    RegionCode,
    export_region_config,
    get_available_regions,
    get_region_profile,
)


def test_get_available_regions() -> None:
    """Test listing all supported regions."""
    regions = get_available_regions()
    assert RegionCode.EU in regions
    assert RegionCode.US in regions
    assert RegionCode.JP in regions
    assert RegionCode.WORLD in regions


def test_get_region_profile_valid() -> None:
    """Test getting profile for each valid region code."""
    for code in RegionCode:
        profile = get_region_profile(code)
        assert profile.code == code
        assert len(profile.subghz_tx_bands) > 0
        assert profile.name
        assert profile.regulatory_body


def test_get_region_profile_case_insensitive() -> None:
    """Test string lookup with lowercase region codes."""
    profile_eu = get_region_profile("eu")
    assert profile_eu.code == RegionCode.EU

    profile_us = get_region_profile("us")
    assert profile_us.code == RegionCode.US


def test_get_region_profile_invalid() -> None:
    """Test invalid region code raises ValueError with helpful message."""
    with pytest.raises(ValueError, match="Région inconnue 'INVALID'"):
        get_region_profile("INVALID")


def test_export_region_config() -> None:
    """Test exporting profile to Flipper settings dictionary."""
    profile = get_region_profile(RegionCode.EU)
    config = export_region_config(profile)

    assert config["region_code"] == "EU"
    assert config["region_name"] == profile.name
    assert config["regulatory_body"] == "ETSI / CE"
    assert isinstance(config["tx_bands"], list)
    assert len(config["tx_bands"]) == 2
    assert config["tx_bands"][0]["start"] == 433_050_000
    assert config["tx_bands"][0]["end"] == 434_790_000


def test_build_region_settings_action() -> None:
    """Test building region settings PlanAction."""
    profile = get_region_profile(RegionCode.US)
    action = build_region_settings_action(profile)
    assert action.action_type == ActionType.WRITE_FILE
    assert action.target_path == "/ext/settings/region.json"
    assert action.source_content is not None
    loaded = json.loads(action.source_content.decode("utf-8"))
    assert loaded == export_region_config(profile)


def test_main_region_invalid_standalone(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --region with invalid code returns 1 and prints French message on stderr."""
    exit_code = main(["--region", "INVALID"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Erreur : Région inconnue 'INVALID'" in captured.err
    assert "invalid choice" not in captured.err


def test_main_install_region_invalid(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --install with invalid region returns 1 and prints French message on stderr."""
    exit_code = main(["--install", "--region", "invalid", "--dry-run"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Erreur : Région inconnue 'invalid'" in captured.err


def test_main_export_bundle_region_invalid(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --export-bundle with invalid region returns 1 and prints French message on stderr."""
    exit_code = main(["--export-bundle", "x.tar.gz", "--region", "invalid"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Erreur : Région inconnue 'invalid'" in captured.err


def test_main_install_plan_contains_both_settings_files() -> None:
    """Test --install includes both region.json and momentum_profile.json in the plan."""
    mock_port = MagicMock(
        device="COM3",
        vid=FLIPPER_VID,
        pid=FLIPPER_PID,
        description="Flipper Zero",
        serial_number="flip_123",
    )
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial.read.return_value = b">: "
    executed_plan: list[PlanAction] = []

    def mock_exec(
        client: Any, plan: list[PlanAction], on_progress: Any = None
    ) -> list[str]:
        executed_plan.extend(plan)
        return []

    with (
        patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        patch("serial.Serial", return_value=mock_serial),
        patch("flopper.cli.execute_install_plan", side_effect=mock_exec),
    ):
        exit_code = main(["--install", "--region", "US", "--dry-run"])
        assert exit_code == 0

        target_paths = [a.target_path for a in executed_plan]
        assert "/ext/settings/momentum_profile.json" in target_paths
        assert "/ext/settings/region.json" in target_paths

        region_action = next(
            a for a in executed_plan if a.target_path == "/ext/settings/region.json"
        )
        assert region_action.action_type == ActionType.WRITE_FILE
        assert region_action.source_content is not None
        assert json.loads(
            region_action.source_content.decode("utf-8")
        ) == export_region_config(get_region_profile("US"))
