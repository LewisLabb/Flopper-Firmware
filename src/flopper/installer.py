"""Installation pipeline executor for Flopper packages."""

from __future__ import annotations

import json
from collections.abc import Callable

from flopper.badusb import export_payload_assets, get_default_payloads
from flopper.dictionaries import (
    export_dictionary_assets,
    get_default_dictionaries,
)
from flopper.flipper_client import FlipperClient
from flopper.manifest import (
    ActionType,
    AppEntry,
    AssetEntry,
    PackManifest,
    PlanAction,
)
from flopper.modules import ModuleType, export_modules_settings
from flopper.regions import (
    RegionCode,
    RegionProfile,
    export_region_config,
    get_region_profile,
)
from flopper.theme import (
    ThemeName,
    export_theme_settings,
    get_theme_assets,
    get_theme_profile,
)


def get_default_pack(
    region: RegionCode | str = RegionCode.EU,
    modules: list[ModuleType] | None = None,
    theme: ThemeName | str = ThemeName.DEFAULT,
) -> PackManifest:
    """Return the built-in curated Flopper pack configured for a region, modules, and theme."""
    profile = get_region_profile(region)
    region_data = export_region_config(profile)
    theme_profile = get_theme_profile(theme)
    theme_data = export_theme_settings(theme_profile)
    theme_assets = get_theme_assets(theme_profile)
    dict_assets = export_dictionary_assets(get_default_dictionaries())
    payload_assets = export_payload_assets(get_default_payloads())
    modules_list = modules if modules is not None else []
    modules_data = export_modules_settings(modules_list)

    return PackManifest(
        name="Flopper-Curated-Pack",
        version="1.0.0",
        description=f"Pack de démarrage optimisé avec applications curées, profil {profile.name} et thème {theme_profile.title}.",
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
            *theme_assets,
            *payload_assets,
        ],
        settings={
            "profile_name": "Flopper Default",
            "dark_mode": True,
            "animations_enabled": True,
            "log_level": "info",
            "region": region_data,
            "modules": modules_data,
            "theme": theme_data,
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


def build_region_settings_action(profile: RegionProfile) -> PlanAction:
    """Build the install-plan action that writes the region-specific settings file."""
    content = json.dumps(export_region_config(profile), indent=2).encode()
    return PlanAction(
        action_type=ActionType.WRITE_FILE,
        target_path="/ext/settings/region.json",
        source_content=content,
        description="Écriture du profil régional dans /ext/settings/region.json",
    )


def build_modules_settings_action(active_modules: list[ModuleType]) -> PlanAction:
    """Build the install-plan action that writes the modules settings file."""
    content = json.dumps(export_modules_settings(active_modules), indent=2).encode()
    return PlanAction(
        action_type=ActionType.WRITE_FILE,
        target_path="/ext/settings/modules.json",
        source_content=content,
        description="Écriture de la configuration des modules dans /ext/settings/modules.json",
    )
