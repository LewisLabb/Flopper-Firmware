"""Predictive keyboard dictionaries and pre-filled quick values for Flipper Zero."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from momentum_ultra.manifest import AssetEntry


class DictionaryCategory(str, Enum):
    """Category of predictive dictionary entries."""

    SSID = "ssids"
    IPS = "ips"
    PAYLOADS = "payloads"
    WORDS = "words"


@dataclass(frozen=True)
class DictionaryEntry:
    """Single entry in a predictive dictionary."""

    category: DictionaryCategory
    value: str
    frequency: int = 1


@dataclass(frozen=True)
class PredictiveDictionary:
    """Collection of dictionary entries organized by category."""

    entries: list[DictionaryEntry]


def get_default_dictionaries() -> PredictiveDictionary:
    """Return default curated predictive dictionaries."""
    entries: list[DictionaryEntry] = [
        # SSIDs
        DictionaryEntry(DictionaryCategory.SSID, "Home-WiFi", 10),
        DictionaryEntry(DictionaryCategory.SSID, "Lab-Internal", 9),
        DictionaryEntry(DictionaryCategory.SSID, "Guest-Access", 8),
        DictionaryEntry(DictionaryCategory.SSID, "Flipper-Hotspot", 7),
        DictionaryEntry(DictionaryCategory.SSID, "Office-Network", 6),
        DictionaryEntry(DictionaryCategory.SSID, "ESP32-AP", 5),
        # IPs
        DictionaryEntry(DictionaryCategory.IPS, "192.168.1.1", 10),
        DictionaryEntry(DictionaryCategory.IPS, "192.168.0.1", 9),
        DictionaryEntry(DictionaryCategory.IPS, "10.0.0.1", 8),
        DictionaryEntry(DictionaryCategory.IPS, "172.16.0.1", 7),
        DictionaryEntry(DictionaryCategory.IPS, "1.1.1.1", 6),
        DictionaryEntry(DictionaryCategory.IPS, "8.8.8.8", 5),
        DictionaryEntry(DictionaryCategory.IPS, "127.0.0.1", 4),
        # BadUSB / Scripting Payloads
        DictionaryEntry(DictionaryCategory.PAYLOADS, "STRING ", 10),
        DictionaryEntry(DictionaryCategory.PAYLOADS, "DELAY 500", 9),
        DictionaryEntry(DictionaryCategory.PAYLOADS, "ENTER", 8),
        DictionaryEntry(DictionaryCategory.PAYLOADS, "GUI r", 7),
        DictionaryEntry(DictionaryCategory.PAYLOADS, "CTRL ALT DEL", 6),
        DictionaryEntry(DictionaryCategory.PAYLOADS, "REM ", 5),
        # Common Words for predictive typing
        DictionaryEntry(DictionaryCategory.WORDS, "admin", 10),
        DictionaryEntry(DictionaryCategory.WORDS, "password", 9),
        DictionaryEntry(DictionaryCategory.WORDS, "flipper", 8),
        DictionaryEntry(DictionaryCategory.WORDS, "momentum", 7),
        DictionaryEntry(DictionaryCategory.WORDS, "default", 6),
        DictionaryEntry(DictionaryCategory.WORDS, "capture", 5),
    ]
    return PredictiveDictionary(entries=entries)


def export_dictionary_assets(
    dictionary: PredictiveDictionary,
) -> list[AssetEntry]:
    """Convert predictive dictionaries into Flipper SD card AssetEntry files."""
    by_category: dict[DictionaryCategory, list[DictionaryEntry]] = {
        cat: [] for cat in DictionaryCategory
    }
    for entry in dictionary.entries:
        by_category[entry.category].append(entry)

    assets: list[AssetEntry] = []
    for cat, items in by_category.items():
        sorted_items = sorted(items, key=lambda x: x.frequency, reverse=True)
        lines = [item.value for item in sorted_items]
        content = "\n".join(lines).encode()
        dest_path = f"/ext/momentum/dicts/{cat.value}.txt"
        assets.append(AssetEntry(destination_path=dest_path, content=content))

    return assets
