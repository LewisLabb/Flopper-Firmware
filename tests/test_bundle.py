"""Unit tests for bundle packaging, export, and import."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from flopper.bundle import BundleError, export_bundle, import_bundle
from flopper.manifest import AppEntry, AssetEntry, PackManifest


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


def test_export_bundle_contains_sha256(tmp_path: Path) -> None:
    """Test that export_bundle includes sha256 checksums for apps and assets."""
    manifest = PackManifest(
        name="sha-pack",
        version="1.0.0",
        apps=[AppEntry(name="A", category="Tools", filename="a.fap", content=b"BIN_A")],
        assets=[AssetEntry(destination_path="/ext/dolphin/a.bm", content=b"ASSET_A")],
    )
    bundle_path = export_bundle(manifest, tmp_path / "sha_pack.tar.gz")
    with tarfile.open(bundle_path, "r:gz") as tar:
        m_file = tar.extractfile("manifest.json")
        assert m_file is not None
        data = json.loads(m_file.read().decode())
        assert data["apps"][0]["sha256"] == hashlib.sha256(b"BIN_A").hexdigest()
        assert data["assets"][0]["sha256"] == hashlib.sha256(b"ASSET_A").hexdigest()


def test_import_bundle_path_traversal_asset(tmp_path: Path) -> None:
    """Test that forged bundle with asset traversal is rejected by import_bundle."""
    tar_path = tmp_path / "evil_asset.tar.gz"
    manifest_data = {
        "name": "evil-pack",
        "version": "1.0.0",
        "apps": [],
        "assets": [
            {
                "destination_path": "../../../../etc/cron.d/evil",
                "bundle_path": "assets/evil",
            }
        ],
    }
    with tarfile.open(tar_path, "w:gz") as tar:
        m_bytes = json.dumps(manifest_data).encode()
        m_info = tarfile.TarInfo(name="manifest.json")
        m_info.size = len(m_bytes)
        tar.addfile(m_info, io.BytesIO(m_bytes))

        e_bytes = b"echo evil"
        e_info = tarfile.TarInfo(name="assets/evil")
        e_info.size = len(e_bytes)
        tar.addfile(e_info, io.BytesIO(e_bytes))

    with pytest.raises(BundleError):
        import_bundle(tar_path)


def test_import_bundle_path_traversal_app(tmp_path: Path) -> None:
    """Test that forged bundle with app category traversal is rejected by import_bundle."""
    tar_path = tmp_path / "evil_app.tar.gz"
    manifest_data = {
        "name": "evil-pack",
        "version": "1.0.0",
        "apps": [
            {
                "name": "Evil",
                "category": "../../../home/claude/.ssh",
                "filename": "evil.fap",
                "bundle_path": "apps/evil.fap",
            }
        ],
        "assets": [],
    }
    with tarfile.open(tar_path, "w:gz") as tar:
        m_bytes = json.dumps(manifest_data).encode()
        m_info = tarfile.TarInfo(name="manifest.json")
        m_info.size = len(m_bytes)
        tar.addfile(m_info, io.BytesIO(m_bytes))

        a_bytes = b"evil_fap"
        a_info = tarfile.TarInfo(name="apps/evil.fap")
        a_info.size = len(a_bytes)
        tar.addfile(a_info, io.BytesIO(a_bytes))

    with pytest.raises(BundleError):
        import_bundle(tar_path)


def test_import_bundle_tampered_content(tmp_path: Path) -> None:
    """Test that bundle with altered content raises BundleError on SHA256 mismatch."""
    manifest = PackManifest(
        name="tamper-pack",
        version="1.0.0",
        apps=[
            AppEntry(
                name="Good", category="Tools", filename="good.fap", content=b"ORIGINAL"
            )
        ],
    )
    bundle_path = export_bundle(manifest, tmp_path / "original.tar.gz")

    # Read original manifest.json to keep original sha256
    with tarfile.open(bundle_path, "r:gz") as tar:
        m_file = tar.extractfile("manifest.json")
        assert m_file is not None
        manifest_bytes = m_file.read()

    # Create forged bundle with modified binary content but original manifest sha256
    tampered_path = tmp_path / "tampered.tar.gz"
    with tarfile.open(tampered_path, "w:gz") as tar:
        m_info = tarfile.TarInfo(name="manifest.json")
        m_info.size = len(manifest_bytes)
        tar.addfile(m_info, io.BytesIO(manifest_bytes))

        altered_bytes = b"ALTERED_BINARY"
        a_info = tarfile.TarInfo(name="apps/Tools/good.fap")
        a_info.size = len(altered_bytes)
        tar.addfile(a_info, io.BytesIO(altered_bytes))

    with pytest.raises(BundleError, match="Somme de contrôle invalide"):
        import_bundle(tampered_path)


def test_import_bundle_without_sha256(tmp_path: Path) -> None:
    """Test that bundle without sha256 field still imports successfully (best-effort)."""
    tar_path = tmp_path / "no_sha.tar.gz"
    manifest_data = {
        "name": "no-sha-pack",
        "version": "1.0.0",
        "apps": [
            {
                "name": "App",
                "category": "Tools",
                "filename": "app.fap",
                "bundle_path": "apps/app.fap",
            }
        ],
        "assets": [],
    }
    with tarfile.open(tar_path, "w:gz") as tar:
        m_bytes = json.dumps(manifest_data).encode()
        m_info = tarfile.TarInfo(name="manifest.json")
        m_info.size = len(m_bytes)
        tar.addfile(m_info, io.BytesIO(m_bytes))

        a_bytes = b"app_bin"
        a_info = tarfile.TarInfo(name="apps/app.fap")
        a_info.size = len(a_bytes)
        tar.addfile(a_info, io.BytesIO(a_bytes))

    imported = import_bundle(tar_path)
    assert imported.name == "no-sha-pack"
    assert imported.apps[0].content == b"app_bin"
