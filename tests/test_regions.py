"""Unit tests for regional profiles and radio frequency regulations."""

from __future__ import annotations

import pytest

from momentum_ultra.regions import (
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
