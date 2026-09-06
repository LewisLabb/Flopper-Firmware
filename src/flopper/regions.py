"""Regulatory region profiles and frequency configurations for Flipper Zero."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RegionCode(str, Enum):
    """Supported geographical regulatory regions."""

    EU = "EU"
    US = "US"
    JP = "JP"
    WORLD = "WORLD"


@dataclass(frozen=True)
class FrequencyBand:
    """Frequency band specification in Hz."""

    start_hz: int
    end_hz: int
    duty_cycle: float | None = None
    max_power_dbm: int | None = None


@dataclass(frozen=True)
class RegionProfile:
    """Regional regulatory profile with legal frequency bands."""

    code: RegionCode
    name: str
    regulatory_body: str
    subghz_tx_bands: list[FrequencyBand]
    description: str


_PROFILES: dict[RegionCode, RegionProfile] = {
    RegionCode.EU: RegionProfile(
        code=RegionCode.EU,
        name="Union Européenne / CE",
        regulatory_body="ETSI / CE",
        subghz_tx_bands=[
            FrequencyBand(start_hz=433_050_000, end_hz=434_790_000, duty_cycle=0.1),
            FrequencyBand(start_hz=868_150_000, end_hz=868_550_000, duty_cycle=0.01),
        ],
        description="Profil conforme aux normes européennes CE (bandes ISM 433 MHz et 868 MHz).",
    ),
    RegionCode.US: RegionProfile(
        code=RegionCode.US,
        name="États-Unis / Canada (FCC / ISED)",
        regulatory_body="FCC / ISED",
        subghz_tx_bands=[
            FrequencyBand(start_hz=304_100_000, end_hz=321_950_000),
            FrequencyBand(start_hz=433_050_000, end_hz=434_790_000),
            FrequencyBand(start_hz=915_000_000, end_hz=928_000_000),
        ],
        description="Profil conforme FCC Part 15 (bandes 315 MHz, 433 MHz et 915 MHz).",
    ),
    RegionCode.JP: RegionProfile(
        code=RegionCode.JP,
        name="Japon / MIC",
        regulatory_body="MIC (Telec)",
        subghz_tx_bands=[
            FrequencyBand(start_hz=312_000_000, end_hz=315_250_000),
            FrequencyBand(start_hz=920_500_000, end_hz=923_500_000),
        ],
        description="Profil conforme à la réglementation japonaise MIC.",
    ),
    RegionCode.WORLD: RegionProfile(
        code=RegionCode.WORLD,
        name="Monde / Déverrouillé (Expérimental)",
        regulatory_body="Utilisateur (Loi locale applicable)",
        subghz_tx_bands=[
            FrequencyBand(start_hz=300_000_000, end_hz=348_000_000),
            FrequencyBand(start_hz=387_000_000, end_hz=464_000_000),
            FrequencyBand(start_hz=779_000_000, end_hz=928_000_000),
        ],
        description="Plages de fréquences élargies pour tests de laboratoire et recherche.",
    ),
}


def get_available_regions() -> list[RegionCode]:
    """List all available region codes."""
    return list(RegionCode)


def get_region_profile(code: RegionCode | str) -> RegionProfile:
    """Get regulatory profile by code."""
    lookup_code = code if isinstance(code, RegionCode) else None
    if lookup_code is None:
        try:
            lookup_code = RegionCode(str(code).upper())
        except ValueError as err:
            valid_codes = ", ".join(r.value for r in RegionCode)
            raise ValueError(
                f"Région inconnue '{code}'. Régions valides : {valid_codes}"
            ) from err

    return _PROFILES[lookup_code]


def export_region_config(profile: RegionProfile) -> dict[str, object]:
    """Export region profile to Flipper settings dictionary."""
    bands_data = [
        {
            "start": b.start_hz,
            "end": b.end_hz,
            "duty_cycle": b.duty_cycle,
            "max_power_dbm": b.max_power_dbm,
        }
        for b in profile.subghz_tx_bands
    ]
    return {
        "region_code": profile.code.value,
        "region_name": profile.name,
        "regulatory_body": profile.regulatory_body,
        "tx_bands": bands_data,
    }
