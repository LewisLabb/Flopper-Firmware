"""Packaging, export, and import of shareable Flopper bundles."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

from flopper.manifest import (
    PackManifest,
    load_manifest_from_dict,
)


class BundleError(Exception):
    """Base exception for bundle packaging and extraction errors."""


def export_bundle(manifest: PackManifest, destination: str | Path) -> Path:
    """Package a PackManifest and its embedded contents into a shareable .tar.gz archive."""
    dest_path = Path(destination)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_dict: dict[str, object] = {
        "name": manifest.name,
        "version": manifest.version,
        "description": manifest.description,
        "settings": manifest.settings,
        "apps": [],
        "assets": [],
    }

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
        # 1. Add apps
        for idx, app in enumerate(manifest.apps):
            app_arc_path = f"apps/{app.category}/{app.filename}"
            app_data = app.content or b""
            tar_info = tarfile.TarInfo(name=app_arc_path)
            tar_info.size = len(app_data)
            tar.addfile(tar_info, io.BytesIO(app_data))

            app_meta = {
                "name": app.name,
                "category": app.category,
                "filename": app.filename,
                "bundle_path": app_arc_path,
                "sha256": hashlib.sha256(app_data).hexdigest(),
            }
            manifest_dict["apps"].append(app_meta)  # type: ignore[union-attr]

        # 2. Add assets
        for idx, asset in enumerate(manifest.assets):
            clean_dest = asset.destination_path.lstrip("/")
            asset_arc_path = f"assets/{clean_dest}"
            asset_data = asset.content or b""
            tar_info = tarfile.TarInfo(name=asset_arc_path)
            tar_info.size = len(asset_data)
            tar.addfile(tar_info, io.BytesIO(asset_data))

            asset_meta = {
                "destination_path": asset.destination_path,
                "bundle_path": asset_arc_path,
                "sha256": hashlib.sha256(asset_data).hexdigest(),
            }
            manifest_dict["assets"].append(asset_meta)  # type: ignore[union-attr]

        # 3. Add manifest.json
        manifest_bytes = json.dumps(manifest_dict, indent=2).encode()
        m_info = tarfile.TarInfo(name="manifest.json")
        m_info.size = len(manifest_bytes)
        tar.addfile(m_info, io.BytesIO(manifest_bytes))

    dest_path.write_bytes(tar_stream.getvalue())
    return dest_path


def import_bundle(bundle_path: str | Path) -> PackManifest:
    """Load, validate and unpack a PackManifest from a bundle archive (with best-effort SHA256 check)."""
    path = Path(bundle_path)
    if not path.exists():
        raise BundleError(f"Le fichier bundle '{bundle_path}' n'existe pas.")

    # Support direct JSON files
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return load_manifest_from_dict(data)
        except Exception as exc:
            raise BundleError(
                f"Impossible de lire le manifeste JSON '{bundle_path}' : {exc}"
            ) from exc

    try:
        with tarfile.open(path, mode="r:*") as tar:
            try:
                m_file = tar.extractfile("manifest.json")
            except KeyError as exc:
                raise BundleError(
                    f"Le bundle '{bundle_path}' ne contient pas de fichier 'manifest.json'."
                ) from exc

            if m_file is None:
                raise BundleError(
                    f"Impossible d'extraire 'manifest.json' du bundle '{bundle_path}'."
                )

            data = json.loads(m_file.read().decode("utf-8"))

            for app_meta in data.get("apps", []):
                arc_path = app_meta.get("bundle_path")
                content = b""
                if arc_path:
                    try:
                        f = tar.extractfile(arc_path)
                        if f is not None:
                            content = f.read()
                    except KeyError:
                        pass
                expected = app_meta.get("sha256")
                if expected and hashlib.sha256(content).hexdigest() != expected:
                    raise BundleError(
                        f"Somme de contrôle invalide pour '{arc_path}' dans le bundle "
                        f"'{bundle_path}' (fichier corrompu ou altéré)."
                    )
                app_meta["content"] = content

            for asset_meta in data.get("assets", []):
                arc_path = asset_meta.get("bundle_path")
                content = b""
                if arc_path:
                    try:
                        f = tar.extractfile(arc_path)
                        if f is not None:
                            content = f.read()
                    except KeyError:
                        pass
                expected = asset_meta.get("sha256")
                if expected and hashlib.sha256(content).hexdigest() != expected:
                    raise BundleError(
                        f"Somme de contrôle invalide pour '{arc_path}' dans le bundle "
                        f"'{bundle_path}' (fichier corrompu ou altéré)."
                    )
                asset_meta["content"] = content

            return load_manifest_from_dict(data)
    except Exception as exc:
        if isinstance(exc, BundleError):
            raise
        raise BundleError(
            f"Erreur lors de la lecture de l'archive bundle '{bundle_path}' : {exc}"
        ) from exc
