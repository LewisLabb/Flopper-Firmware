"""Unit tests for bundle packaging, export, and import."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from momentum_ultra.bundle import BundleError, export_bundle, import_bundle
from momentum_ultra.manifest import AppEntry, AssetEntry, PackManifest


def test_bundle_roundtrip(tmp_path: Path) -> None:
    """Test exporting a pack to a tar.gz bundle and importing it back."""
    manifest = PackManifest(
        name="community-bundle",
        version="2.1.0",
        description="A great test bundle",
        apps=[
            AppEntry(
                name="AppOne",
                category="Tools",
                filename="one.fap",
                content=b"FAP_ONE_BINARY",
            ),
            AppEntry(
                name="AppTwo",
                category="Games",
                filename="two.fap",
                content=b"FAP_TWO_BINARY",
            ),
        ],
        assets=[
            AssetEntry(
                destination_path="/ext/dolphin/custom.bm",
                content=b"ANIMATION_CUSTOM_DATA",
            ),
        ],
        settings={"volume": 100, "custom_theme": True},
    )

    bundle_file = tmp_path / "custom_pack.tar.gz"
    exported_path = export_bundle(manifest, bundle_file)
    assert exported_path.exists()

    imported = import_bundle(exported_path)
    assert imported.name == "community-bundle"
    assert imported.version == "2.1.0"
    assert imported.description == "A great test bundle"
    assert len(imported.apps) == 2
    assert imported.apps[0].name == "AppOne"
    assert imported.apps[0].content == b"FAP_ONE_BINARY"
    assert imported.apps[1].name == "AppTwo"
    assert imported.apps[1].content == b"FAP_TWO_BINARY"
    assert len(imported.assets) == 1
    assert imported.assets[0].destination_path == "/ext/dolphin/custom.bm"
    assert imported.assets[0].content == b"ANIMATION_CUSTOM_DATA"
    assert imported.settings == {"volume": 100, "custom_theme": True}


def test_import_bundle_json_file(tmp_path: Path) -> None:
    """Test importing a bundle from a direct JSON manifest file."""
    json_data = {
        "name": "json-pack",
        "version": "1.0.0",
        "description": "Json based pack",
        "apps": [
            {
                "name": "JApp",
                "category": "Tools",
                "filename": "j.fap",
                "content": "raw_content",
            }
        ],
        "assets": [],
        "settings": {},
    }
    json_path = tmp_path / "manifest.json"
    json_path.write_text(json.dumps(json_data), encoding="utf-8")

    imported = import_bundle(json_path)
    assert imported.name == "json-pack"
    assert len(imported.apps) == 1
    assert imported.apps[0].content == b"raw_content"


def test_import_bundle_non_existent_file() -> None:
    """Test error when bundle file does not exist."""
    with pytest.raises(BundleError, match="n'existe pas"):
        import_bundle("non_existent_bundle_12345.tar.gz")


def test_import_bundle_invalid_tar(tmp_path: Path) -> None:
    """Test error when bundle archive is corrupt or invalid."""
    corrupt_file = tmp_path / "corrupt.tar.gz"
    corrupt_file.write_bytes(b"not a valid tar stream")

    with pytest.raises(BundleError, match="Erreur lors de la lecture"):
        import_bundle(corrupt_file)
