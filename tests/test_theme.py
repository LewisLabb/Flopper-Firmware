"""Unit tests for Momentum UI theme management."""

import json

import pytest

from momentum_ultra.manifest import AssetEntry
from momentum_ultra.theme import (
    StatusBarStyle,
    ThemeName,
    export_theme_settings,
    get_available_themes,
    get_theme_assets,
    get_theme_profile,
)


def test_get_available_themes() -> None:
    """Check that all 4 themes are available."""
    themes = get_available_themes()
    assert len(themes) == 4
    assert ThemeName.DEFAULT in themes
    assert ThemeName.DARK_STEALTH in themes
    assert ThemeName.RETRO_GAMER in themes
    assert ThemeName.CYBERPUNK in themes


def test_get_theme_profile_by_enum_and_str() -> None:
    """Check that retrieving theme works with enum and string."""
    profile_default = get_theme_profile(ThemeName.DEFAULT)
    assert profile_default.name == ThemeName.DEFAULT
    assert profile_default.status_bar == StatusBarStyle.FULL
    assert profile_default.show_clock is True

    profile_dark = get_theme_profile("dark_stealth")
    assert profile_dark.name == ThemeName.DARK_STEALTH
    assert profile_dark.status_bar == StatusBarStyle.MINIMAL
    assert profile_dark.show_clock is False

    profile_retro = get_theme_profile("RETRO_GAMER")
    assert profile_retro.name == ThemeName.RETRO_GAMER
    assert profile_retro.status_bar == StatusBarStyle.BAR_PERCENT

    profile_cyber = get_theme_profile("cyberpunk")
    assert profile_cyber.name == ThemeName.CYBERPUNK


def test_get_theme_profile_invalid() -> None:
    """Check that an unknown theme raises ValueError."""
    with pytest.raises(ValueError, match="Thème inconnu"):
        get_theme_profile("unknown_theme")


def test_export_theme_settings() -> None:
    """Check exporting theme profile to settings dictionary."""
    profile = get_theme_profile(ThemeName.CYBERPUNK)
    settings = export_theme_settings(profile)
    assert settings["theme_name"] == "cyberpunk"
    assert settings["status_bar_style"] == "full"
    assert settings["show_clock"] is True
    assert settings["animations_pack"] == "cyber_neon"
    assert settings["accent_color"] == "cyan"


def test_get_theme_assets() -> None:
    """Check generating theme asset entries."""
    profile = get_theme_profile(ThemeName.DARK_STEALTH)
    assets = get_theme_assets(profile)
    assert len(assets) == 2

    settings_asset = next(
        a for a in assets if a.destination_path == "/ext/settings/momentum_ui.json"
    )
    dolphin_asset = next(
        a for a in assets if a.destination_path == "/ext/dolphin/theme_info.txt"
    )

    assert isinstance(settings_asset, AssetEntry)
    data = json.loads(settings_asset.content.decode("utf-8"))
    assert data["theme_name"] == "dark_stealth"
    assert b"Dark Stealth" in dolphin_asset.content
