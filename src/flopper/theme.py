"""Custom preference-profile management for Flopper (not native Momentum asset packs)."""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from flopper.manifest import AssetEntry


class ThemeName(str, Enum):
    """Available curated UI themes."""

    DEFAULT = "default"
    DARK_STEALTH = "dark_stealth"
    RETRO_GAMER = "retro_gamer"
    CYBERPUNK = "cyberpunk"


class StatusBarStyle(str, Enum):
    """Battery and indicator layout for the top status bar."""

    FULL = "full"
    MINIMAL = "minimal"
    BAR_PERCENT = "bar_percent"


@dataclass(frozen=True)
class ThemeProfile:
    """Configuration profile for Momentum UI styling."""

    name: ThemeName
    title: str
    description: str
    status_bar: StatusBarStyle
    show_clock: bool
    animations_pack: str
    accent_color_hint: str


_THEME_PROFILES: dict[ThemeName, ThemeProfile] = {
    ThemeName.DEFAULT: ThemeProfile(
        name=ThemeName.DEFAULT,
        title="Momentum Classic",
        description="Thème orange et blanc emblématique de Momentum avec affichage complet.",
        status_bar=StatusBarStyle.FULL,
        show_clock=True,
        animations_pack="momentum_default",
        accent_color_hint="orange",
    ),
    ThemeName.DARK_STEALTH: ThemeProfile(
        name=ThemeName.DARK_STEALTH,
        title="Dark Stealth",
        description="Thème sombre épuré et tactique, minimisant les indicateurs visuels.",
        status_bar=StatusBarStyle.MINIMAL,
        show_clock=False,
        animations_pack="stealth_dark",
        accent_color_hint="monochrome",
    ),
    ThemeName.RETRO_GAMER: ThemeProfile(
        name=ThemeName.RETRO_GAMER,
        title="Retro Gamer",
        description="Esthétique rétro 8-bit inspirée des consoles portables des années 90.",
        status_bar=StatusBarStyle.BAR_PERCENT,
        show_clock=True,
        animations_pack="retro_pixel",
        accent_color_hint="green_tint",
    ),
    ThemeName.CYBERPUNK: ThemeProfile(
        name=ThemeName.CYBERPUNK,
        title="Cyberpunk",
        description="Style futuriste à fort contraste axé sur la télémétrie technique.",
        status_bar=StatusBarStyle.FULL,
        show_clock=True,
        animations_pack="cyber_neon",
        accent_color_hint="cyan",
    ),
}


def get_available_themes() -> list[ThemeName]:
    """List all available theme names."""
    return list(_THEME_PROFILES.keys())


def get_theme_profile(name: ThemeName | str) -> ThemeProfile:
    """Retrieve theme configuration profile by name."""
    if isinstance(name, str):
        try:
            name = ThemeName(name.lower())
        except ValueError:
            valid_names = ", ".join(t.value for t in ThemeName)
            raise ValueError(f"Thème inconnu '{name}'. Thèmes valides : {valid_names}.")
    if name not in _THEME_PROFILES:
        raise ValueError(f"Thème non répertorié : {name}")
    return _THEME_PROFILES[name]


def export_theme_settings(profile: ThemeProfile) -> dict[str, Any]:
    """Generate settings dictionary for /ext/settings/momentum_ui.json."""
    return {
        "theme_name": profile.name.value,
        "title": profile.title,
        "status_bar_style": profile.status_bar.value,
        "show_clock": profile.show_clock,
        "animations_pack": profile.animations_pack,
        "accent_color": profile.accent_color_hint,
    }


def get_theme_assets(profile: ThemeProfile) -> list[AssetEntry]:
    """Return this project's own preference-profile asset entries.

    Ceci configure un profil de préférences interne à Flopper, PAS un
    asset pack Momentum natif (pas de frames .bm/.bmx, pas de manifest.txt).
    Sans effet sur l'affichage réel d'un Flipper sous le firmware standard tant que le
    format natif des asset packs n'est pas implémenté séparément.
    """
    settings_data = export_theme_settings(profile)
    manifest_bytes = json.dumps(settings_data, indent=2).encode("utf-8")
    dolphin_info = (
        f"Flopper — profil de préférences : {profile.title}\n"
        f"Pack : {profile.animations_pack}\n"
        f"Barre d'état : {profile.status_bar.value}\n"
        "Ce fichier ne modifie pas l'affichage natif de Momentum : c'est une "
        "extension de préférences propre à Flopper.\n"
    ).encode()

    return [
        AssetEntry(
            destination_path="/ext/settings/momentum_ui.json",
            content=manifest_bytes,
        ),
        AssetEntry(
            destination_path="/ext/settings/momentum_ui_info.txt",
            content=dolphin_info,
        ),
    ]
