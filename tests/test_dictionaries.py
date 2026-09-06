"""Unit tests for predictive keyboard dictionaries and quick input lists."""

from __future__ import annotations

from flopper.dictionaries import (
    DictionaryCategory,
    DictionaryEntry,
    PredictiveDictionary,
    export_dictionary_assets,
    get_default_dictionaries,
)


def test_get_default_dictionaries_structure() -> None:
    """Test that default dictionaries contain entries across all categories."""
    dicts = get_default_dictionaries()
    assert isinstance(dicts, PredictiveDictionary)
    categories = {e.category for e in dicts.entries}
    assert DictionaryCategory.SSID in categories
    assert DictionaryCategory.IPS in categories
    assert DictionaryCategory.PAYLOADS in categories
    assert DictionaryCategory.WORDS in categories
    assert len(dicts.entries) >= 20


def test_export_dictionary_assets() -> None:
    """Test exporting dictionaries into Flipper SD card asset files."""
    dictionary = PredictiveDictionary(
        entries=[
            DictionaryEntry(DictionaryCategory.SSID, "FastNet", 10),
            DictionaryEntry(DictionaryCategory.SSID, "SlowNet", 2),
            DictionaryEntry(DictionaryCategory.IPS, "10.0.0.1", 5),
            DictionaryEntry(DictionaryCategory.PAYLOADS, "STRING hello", 8),
            DictionaryEntry(DictionaryCategory.WORDS, "test", 1),
        ]
    )

    assets = export_dictionary_assets(dictionary)
    destinations = [a.destination_path for a in assets]

    assert "/ext/momentum/dicts/ssids.txt" in destinations
    assert "/ext/momentum/dicts/ips.txt" in destinations
    assert "/ext/momentum/dicts/payloads.txt" in destinations
    assert "/ext/momentum/dicts/words.txt" in destinations

    ssid_asset = next(
        a for a in assets if a.destination_path == "/ext/momentum/dicts/ssids.txt"
    )
    lines = ssid_asset.content.decode().split("\n")
    assert lines == ["FastNet", "SlowNet"]  # Sorted by frequency descending
