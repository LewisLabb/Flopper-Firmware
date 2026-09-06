"""Manifest definitions and installation plan generation for Flopper."""

from __future__ import annotations

import json
import posixpath
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def _validate_path_segment(value: object, field_name: str) -> str:
    """Validate that value is a valid single path segment."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"Le champ '{field_name}' doit être une chaîne non vide.")
    if "/" in value or "\\" in value or value in {".", ".."}:
        raise ValueError(
            f"Le champ '{field_name}' ne doit pas contenir de séparateur ni être '.' ou '..' : {value!r}"
        )
    return value


class ActionType(str, Enum):
    """Type of installation action."""

    CREATE_DIR = "create_dir"
    WRITE_FILE = "write_file"
    BACKUP = "backup"


@dataclass(frozen=True)
class PlanAction:
    """Single installation plan action."""

    action_type: ActionType
    target_path: str
    source_content: bytes | None = None
    description: str = ""


@dataclass(frozen=True)
class AppEntry:
    """Application to be installed on Flipper Zero."""

    name: str
    category: str
    filename: str
    content: bytes = field(repr=False, default=b"")


@dataclass(frozen=True)
class AssetEntry:
    """Asset file to deploy on Flipper SD card."""

    destination_path: str
    content: bytes = field(repr=False, default=b"")


@dataclass(frozen=True)
class PackManifest:
    """Manifest describing a curated curation pack."""

    name: str
    version: str
    description: str = ""
    apps: list[AppEntry] = field(default_factory=list)
    assets: list[AssetEntry] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)


def load_manifest_from_dict(data: dict[str, Any]) -> PackManifest:
    """Load and validate a PackManifest from a dictionary."""
    if not isinstance(data, dict):
        raise TypeError("Le format du manifeste est invalide (dictionnaire attendu).")

    name = data.get("name")
    if not name or not isinstance(name, str):
        raise ValueError("Le champ 'name' est obligatoire dans le manifeste.")

    version = data.get("version")
    if not version or not isinstance(version, str):
        raise ValueError("Le champ 'version' est obligatoire dans le manifeste.")

    description = data.get("description", "")
    if not isinstance(description, str):
        description = str(description)

    apps: list[AppEntry] = []
    raw_apps = data.get("apps", [])
    if not isinstance(raw_apps, list):
        raise TypeError("Le champ 'apps' doit être une liste.")

    for item in raw_apps:
        if not isinstance(item, dict):
            raise TypeError("Chaque élément de 'apps' doit être un objet.")
        app_name = item.get("name")
        category = item.get("category")
        filename = item.get("filename")
        if not app_name or not category or not filename:
            raise ValueError(
                "Chaque application doit spécifier 'name', 'category' et 'filename'."
            )
        if not isinstance(app_name, str):
            raise TypeError("Le champ 'name' d'une application doit être une chaîne.")
        clean_category = _validate_path_segment(category, "category")
        clean_filename = _validate_path_segment(filename, "filename")

        content = item.get("content", b"")
        if isinstance(content, str):
            content = content.encode()
        if not isinstance(content, bytes):
            raise TypeError(
                f"Le champ 'content' doit être une chaîne ou des octets, reçu {type(content).__name__}."
            )
        apps.append(
            AppEntry(
                name=app_name,
                category=clean_category,
                filename=clean_filename,
                content=content,
            )
        )

    assets: list[AssetEntry] = []
    raw_assets = data.get("assets", [])
    if not isinstance(raw_assets, list):
        raise TypeError("Le champ 'assets' doit être une liste.")

    for item in raw_assets:
        if not isinstance(item, dict):
            raise TypeError("Chaque élément de 'assets' doit être un objet.")
        destination = item.get("destination_path")
        if not destination or not isinstance(destination, str):
            raise ValueError(
                "Chaque asset doit spécifier un 'destination_path' valide."
            )
        if not destination.startswith("/"):
            raise ValueError(
                f"'destination_path' doit être un chemin absolu commençant par /ext/ : {destination!r}"
            )
        normalized = posixpath.normpath(destination)
        if normalized != "/ext" and not normalized.startswith("/ext/"):
            raise ValueError(
                f"'destination_path' doit rester sous /ext/ une fois normalisé : "
                f"{destination!r} -> {normalized!r}"
            )
        content = item.get("content", b"")
        if isinstance(content, str):
            content = content.encode()
        if not isinstance(content, bytes):
            raise TypeError(
                f"Le champ 'content' doit être une chaîne ou des octets, reçu {type(content).__name__}."
            )
        assets.append(AssetEntry(destination_path=normalized, content=content))

    settings = data.get("settings", {})
    if not isinstance(settings, dict):
        raise TypeError("Le champ 'settings' doit être un dictionnaire.")

    return PackManifest(
        name=name,
        version=version,
        description=description,
        apps=apps,
        assets=assets,
        settings=settings,
    )


def generate_install_plan(
    manifest: PackManifest,
    backup_existing: bool = True,
) -> list[PlanAction]:
    """Generate the ordered list of PlanAction items needed to install the pack."""
    actions: list[PlanAction] = []

    # 1. Backups if requested
    if backup_existing and manifest.apps:
        actions.append(
            PlanAction(
                action_type=ActionType.BACKUP,
                target_path="/ext/apps",
                description="Sauvegarde préventive du dossier /ext/apps",
            )
        )

    # 2. Base directory creations
    created_dirs: set[str] = set()

    def _ensure_dir(dir_path: str, desc: str) -> None:
        clean = dir_path.rstrip("/")
        if clean not in created_dirs:
            actions.append(
                PlanAction(
                    action_type=ActionType.CREATE_DIR,
                    target_path=clean,
                    description=desc,
                )
            )
            created_dirs.add(clean)

    _ensure_dir("/ext/apps", "Création du dossier principal des applications")

    # 3. Application categories and binaries
    for app in manifest.apps:
        cat_dir = f"/ext/apps/{app.category}"
        _ensure_dir(cat_dir, f"Création de la catégorie d'applications {app.category}")
        target_file = f"{cat_dir}/{app.filename}"
        actions.append(
            PlanAction(
                action_type=ActionType.WRITE_FILE,
                target_path=target_file,
                source_content=app.content,
                description=f"Installation de l'application {app.name} ({app.filename})",
            )
        )

    # 4. Assets
    for asset in manifest.assets:
        parent_dir = "/".join(asset.destination_path.rstrip("/").split("/")[:-1])
        if parent_dir:
            _ensure_dir(parent_dir, f"Création du dossier pour asset {parent_dir}")
        actions.append(
            PlanAction(
                action_type=ActionType.WRITE_FILE,
                target_path=asset.destination_path,
                source_content=asset.content,
                description=f"Copie de l'asset {asset.destination_path}",
            )
        )

    # 5. Settings profile
    if manifest.settings:
        _ensure_dir("/ext/settings", "Création du dossier des réglages")
        profile_content = json.dumps(manifest.settings, indent=2).encode()
        actions.append(
            PlanAction(
                action_type=ActionType.WRITE_FILE,
                target_path="/ext/settings/momentum_profile.json",
                source_content=profile_content,
                description="Application du profil de réglages Momentum",
            )
        )

    return actions
