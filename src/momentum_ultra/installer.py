"""Installation pipeline executor for Momentum Ultra packages."""

from __future__ import annotations

from collections.abc import Callable

from momentum_ultra.dictionaries import (
    export_dictionary_assets,
    get_default_dictionaries,
)
from momentum_ultra.flipper_client import FlipperClient
from momentum_ultra.manifest import (
    ActionType,
    AppEntry,
    AssetEntry,
    PackManifest,
    PlanAction,
)
from momentum_ultra.regions import (
    RegionCode,
    export_region_config,
    get_region_profile,
)


def get_default_pack(region: RegionCode | str = RegionCode.EU) -> PackManifest:
    """Return the built-in curated Momentum Ultra pack configured for a region."""
    profile = get_region_profile(region)
    region_data = export_region_config(profile)
    dict_assets = export_dictionary_assets(get_default_dictionaries())

    return PackManifest(
        name="Momentum-Ultra-Curated-Pack",
        version="1.0.0",
        description=f"Pack de démarrage optimisé avec applications curées et profil {profile.name}.",
        apps=[
            AppEntry(
                name="ESP32 WiFi Scanner",
                category="GPIO",
                filename="wifi_scanner.fap",
                content=b"FAP_BIN_WIFI_SCANNER",
            ),
            AppEntry(
                name="Signal Generator",
                category="GPIO",
                filename="signal_gen.fap",
                content=b"FAP_BIN_SIGNAL_GEN",
            ),
            AppEntry(
                name="Tetris Ultra",
                category="Games",
                filename="tetris_ultra.fap",
                content=b"FAP_BIN_TETRIS",
            ),
            AppEntry(
                name="TOTP Authenticator",
                category="Tools",
                filename="totp.fap",
                content=b"FAP_BIN_TOTP",
            ),
        ],
        assets=[
            AssetEntry(
                destination_path="/ext/dolphin/momentum_boot.bm",
                content=b"MOMENTUM_ANIMATION_DATA",
            ),
            *dict_assets,
        ],
        settings={
            "profile_name": "Momentum Ultra Default",
            "dark_mode": True,
            "animations_enabled": True,
            "log_level": "info",
            "region": region_data,
        },
    )


def execute_install_plan(
    client: FlipperClient,
    plan: list[PlanAction],
    on_progress: Callable[[PlanAction, int, int], None] | None = None,
) -> list[str]:
    """Execute each action in the installation plan on the Flipper Zero."""
    results: list[str] = []
    total = len(plan)

    for idx, action in enumerate(plan):
        if on_progress is not None:
            on_progress(action, idx + 1, total)

        if action.action_type == ActionType.CREATE_DIR:
            client.mkdir(action.target_path)
        elif action.action_type == ActionType.WRITE_FILE:
            client.write_file(action.target_path, action.source_content or b"")
        elif action.action_type == ActionType.BACKUP:
            client.backup_item(action.target_path)

        prefix = "SIMULATION" if client.dry_run else "SUCCÈS"
        results.append(f"[{prefix}] {action.description}")

    return results
