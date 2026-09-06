"""Unit tests for external hardware modules and GPIO configuration."""

from __future__ import annotations

import json

from flopper.installer import build_modules_settings_action
from flopper.manifest import ActionType
from flopper.modules import (
    ModuleType,
    export_modules_settings,
    get_default_module_configs,
)


def test_get_default_module_configs() -> None:
    """Test standard module configurations exist for all types."""
    configs = get_default_module_configs()
    assert ModuleType.CC1101 in configs
    assert ModuleType.NRF24 in configs
    assert ModuleType.ESP32_MARAUDER in configs
    assert ModuleType.COMBO_2IN1 in configs

    cc1101 = configs[ModuleType.CC1101]
    assert cc1101.pinout.cs_pin == "17"
    assert cc1101.pinout.mosi_pin == "15"


def test_export_modules_settings_empty() -> None:
    """Test exporting empty modules configuration (default)."""
    settings = export_modules_settings([])
    assert settings["enabled"] is False
    assert settings["active_modules"] == []


def test_export_modules_settings_active() -> None:
    """Test exporting modules settings to dictionary with active modules."""
    settings = export_modules_settings([ModuleType.CC1101, ModuleType.ESP32_MARAUDER])
    assert settings["enabled"] is True
    assert len(settings["active_modules"]) == 2
    assert settings["active_modules"][0]["type"] == "cc1101"
    assert settings["active_modules"][0]["cs_pin"] == "17"
    assert settings["active_modules"][1]["type"] == "esp32"


def test_build_modules_settings_action() -> None:
    """Test building the install plan action for modules settings."""
    action = build_modules_settings_action([ModuleType.CC1101])
    assert action.action_type == ActionType.WRITE_FILE
    assert action.target_path == "/ext/settings/modules.json"
    assert action.source_content is not None
    data = json.loads(action.source_content.decode("utf-8"))
    assert data["enabled"] is True
    assert len(data["active_modules"]) == 1
    assert data["active_modules"][0]["type"] == "cc1101"
