"""Unit tests for external hardware modules and GPIO configuration."""

from __future__ import annotations

from momentum_ultra.modules import (
    ModuleType,
    detect_connected_modules,
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


def test_detect_connected_modules_cc1101() -> None:
    """Test detecting CC1101 from output."""
    raw = "SPI device: CC1101 SubGHz_Ext initialized on pin 17"
    detected = detect_connected_modules(raw)
    assert detected == [ModuleType.CC1101]


def test_detect_connected_modules_nrf24() -> None:
    """Test detecting nRF24 from output."""
    raw = "SPI device: nRF24 2.4GHz module ready"
    detected = detect_connected_modules(raw)
    assert detected == [ModuleType.NRF24]


def test_detect_connected_modules_esp32() -> None:
    """Test detecting ESP32 Marauder from UART output."""
    raw = "UART: ESP32 Marauder firmware v0.13.0 bridge connected"
    detected = detect_connected_modules(raw)
    assert detected == [ModuleType.ESP32_MARAUDER]


def test_detect_connected_modules_combo() -> None:
    """Test detecting Combo 2-in-1 board."""
    raw = "Dual module: Combo 2in1 CC1101 + nRF24 attached"
    detected = detect_connected_modules(raw)
    assert detected == [ModuleType.COMBO_2IN1]


def test_detect_connected_modules_none() -> None:
    """Test detecting when no module is connected."""
    raw = "GPIO status: all pins float"
    detected = detect_connected_modules(raw)
    assert detected == []


def test_export_modules_settings() -> None:
    """Test exporting modules settings to dictionary."""
    settings = export_modules_settings([ModuleType.CC1101, ModuleType.ESP32_MARAUDER])
    assert settings["enabled"] is True
    assert len(settings["active_modules"]) == 2
    assert settings["active_modules"][0]["type"] == "cc1101"
    assert settings["active_modules"][1]["type"] == "esp32"
