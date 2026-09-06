"""External hardware modules and GPIO expansion board management for Flipper Zero."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ModuleType(str, Enum):
    """Supported external hardware modules."""

    CC1101 = "cc1101"
    NRF24 = "nrf24"
    ESP32_MARAUDER = "esp32"
    COMBO_2IN1 = "combo_2in1"


@dataclass(frozen=True)
class ModulePinout:
    """Pin mapping configuration for an external module."""

    cs_pin: str
    mosi_pin: str = "15"
    miso_pin: str = "16"
    sck_pin: str = "13"
    gdo0_pin: str | None = None
    extra_pins: dict[str, str] | None = None


@dataclass(frozen=True)
class ModuleConfig:
    """Configuration and status of an external module."""

    module_type: ModuleType
    name: str
    enabled: bool
    pinout: ModulePinout
    description: str


_DEFAULT_CONFIGS: dict[ModuleType, ModuleConfig] = {
    ModuleType.CC1101: ModuleConfig(
        module_type=ModuleType.CC1101,
        name="Module CC1101 (Sub-GHz externe)",
        enabled=True,
        pinout=ModulePinout(
            cs_pin="17",
            mosi_pin="15",
            miso_pin="16",
            sck_pin="13",
            gdo0_pin="2",
        ),
        description="Module émetteur-récepteur Sub-GHz longue portée externe.",
    ),
    ModuleType.NRF24: ModuleConfig(
        module_type=ModuleType.NRF24,
        name="Module nRF24L01 (2.4 GHz)",
        enabled=True,
        pinout=ModulePinout(
            cs_pin="17",
            mosi_pin="15",
            miso_pin="16",
            sck_pin="13",
            extra_pins={"ce": "2"},
        ),
        description="Module 2.4 GHz pour détection, sniffing et recherche de périphériques sans fil.",
    ),
    ModuleType.ESP32_MARAUDER: ModuleConfig(
        module_type=ModuleType.ESP32_MARAUDER,
        name="Module ESP32 / Wi-Fi Marauder",
        enabled=True,
        pinout=ModulePinout(
            cs_pin="N/A (UART)",
            extra_pins={"tx": "13", "rx": "14", "boot": "4"},
        ),
        description="Carte d'extension ESP32 dédiée à l'audit et l'analyse des réseaux Wi-Fi et BLE.",
    ),
    ModuleType.COMBO_2IN1: ModuleConfig(
        module_type=ModuleType.COMBO_2IN1,
        name="Carte Combo 2-en-1 (CC1101 + nRF24)",
        enabled=True,
        pinout=ModulePinout(
            cs_pin="17 (CC1101) / 10 (nRF24)",
            mosi_pin="15",
            miso_pin="16",
            sck_pin="13",
            gdo0_pin="2",
            extra_pins={"nrf_ce": "7"},
        ),
        description="Carte combinée double antenne pour Sub-GHz longue portée et 2.4 GHz unifiés.",
    ),
}


def get_default_module_configs() -> dict[ModuleType, ModuleConfig]:
    """Return standard pinout configurations for all supported modules."""
    return dict(_DEFAULT_CONFIGS)


def export_modules_settings(active_modules: list[ModuleType]) -> dict[str, Any]:
    """Export active modules configuration dictionary for /ext/settings/modules.json."""
    configs = get_default_module_configs()
    modules_data: list[dict[str, Any]] = []

    for mod_type in active_modules:
        if mod_type in configs:
            cfg = configs[mod_type]
            modules_data.append(
                {
                    "type": cfg.module_type.value,
                    "name": cfg.name,
                    "cs_pin": cfg.pinout.cs_pin,
                    "mosi_pin": cfg.pinout.mosi_pin,
                    "miso_pin": cfg.pinout.miso_pin,
                    "sck_pin": cfg.pinout.sck_pin,
                    "gdo0_pin": cfg.pinout.gdo0_pin,
                    "extra_pins": cfg.pinout.extra_pins or {},
                }
            )

    return {
        "enabled": len(modules_data) > 0,
        "active_modules": modules_data,
    }
