"""Unit tests for pack manifest parsing, validation, and installation plan generation."""

from __future__ import annotations

import pytest

from momentum_ultra.manifest import (
    ActionType,
    AppEntry,
    AssetEntry,
    PackManifest,
    generate_install_plan,
    load_manifest_from_dict,
)


def test_load_manifest_valid() -> None:
    """Test loading a complete valid pack manifest."""
    data = {
        "name": "momentum-pack-curated",
        "version": "1.0.0",
        "description": "Curated pack of tools and games",
        "apps": [
            {
                "name": "Tetris",
                "category": "Games",
                "filename": "tetris.fap",
                "content": "fap_binary_data",
            }
        ],
        "assets": [
            {
                "destination_path": "/ext/dolphin/intro.bm",
                "content": "animation_bytes",
            }
        ],
        "settings": {"bluetooth_name": "MomentumFlipper"},
    }

    manifest = load_manifest_from_dict(data)
    assert isinstance(manifest, PackManifest)
    assert manifest.name == "momentum-pack-curated"
    assert manifest.version == "1.0.0"
    assert len(manifest.apps) == 1
    assert manifest.apps[0] == AppEntry(
        name="Tetris",
        category="Games",
        filename="tetris.fap",
        content=b"fap_binary_data",
    )
    assert len(manifest.assets) == 1
    assert manifest.assets[0] == AssetEntry(
        destination_path="/ext/dolphin/intro.bm", content=b"animation_bytes"
    )
    assert manifest.settings == {"bluetooth_name": "MomentumFlipper"}


def test_load_manifest_missing_required_fields() -> None:
    """Test validation errors on missing name or version."""
    with pytest.raises(ValueError, match="Le champ 'name' est obligatoire"):
        load_manifest_from_dict({"version": "1.0.0"})

    with pytest.raises(ValueError, match="Le champ 'version' est obligatoire"):
        load_manifest_from_dict({"name": "pack"})


def test_load_manifest_type_errors() -> None:
    """Test TypeError on invalid non-dict or non-list data."""
    with pytest.raises(TypeError):
        load_manifest_from_dict("not a dict")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        load_manifest_from_dict({"name": "p", "version": "1", "apps": "not list"})

    with pytest.raises(TypeError):
        load_manifest_from_dict({"name": "p", "version": "1", "assets": "not list"})


def test_load_manifest_invalid_app_entry() -> None:
    """Test validation error on incomplete app entries."""
    data = {
        "name": "pack",
        "version": "1.0.0",
        "apps": [{"name": "Incomplete"}],
    }
    with pytest.raises(ValueError, match="Chaque application doit spécifier"):
        load_manifest_from_dict(data)


def test_load_manifest_invalid_asset_entry() -> None:
    """Test validation error on incomplete asset entries."""
    data = {
        "name": "pack",
        "version": "1.0.0",
        "assets": [{"invalid_key": "val"}],
    }
    with pytest.raises(ValueError, match="Chaque asset doit spécifier"):
        load_manifest_from_dict(data)


def test_generate_install_plan_with_backup() -> None:
    """Test install plan generation includes backup step when requested."""
    manifest = PackManifest(
        name="pack",
        version="1.0.0",
        description="test",
        apps=[
            AppEntry(
                name="App1",
                category="Tools",
                filename="app1.fap",
                content=b"data1",
            ),
            AppEntry(
                name="App2",
                category="Tools",
                filename="app2.fap",
                content=b"data2",
            ),
        ],
        assets=[AssetEntry(destination_path="/ext/dolphin/icon.bm", content=b"icon")],
        settings={"dark_mode": True},
    )

    plan = generate_install_plan(manifest, backup_existing=True)

    # Verify backup is the first step
    assert plan[0].action_type == ActionType.BACKUP
    assert plan[0].target_path == "/ext/apps"

    # Verify directory creations
    dir_actions = [p for p in plan if p.action_type == ActionType.CREATE_DIR]
    dir_targets = [d.target_path for d in dir_actions]
    assert "/ext/apps" in dir_targets
    assert "/ext/apps/Tools" in dir_targets
    assert "/ext/dolphin" in dir_targets
    assert "/ext/settings" in dir_targets

    # Verify write actions
    write_actions = [p for p in plan if p.action_type == ActionType.WRITE_FILE]
    write_targets = [w.target_path for w in write_actions]
    assert "/ext/apps/Tools/app1.fap" in write_targets
    assert "/ext/apps/Tools/app2.fap" in write_targets
    assert "/ext/dolphin/icon.bm" in write_targets
    assert "/ext/settings/momentum_profile.json" in write_targets


def test_generate_install_plan_without_backup() -> None:
    """Test install plan generation without backup step."""
    manifest = PackManifest(
        name="pack",
        version="1.0.0",
        apps=[
            AppEntry(
                name="App1",
                category="Tools",
                filename="app1.fap",
                content=b"data",
            )
        ],
    )
    plan = generate_install_plan(manifest, backup_existing=False)
    backup_actions = [p for p in plan if p.action_type == ActionType.BACKUP]
    assert len(backup_actions) == 0


def test_load_manifest_asset_path_relative_traversal() -> None:
    """Test ValueError when asset destination_path is relative with traversal."""
    data = {
        "name": "pack",
        "version": "1.0.0",
        "assets": [{"destination_path": "../../../../etc/passwd"}],
    }
    with pytest.raises(
        ValueError, match="doit être un chemin absolu commençant par /ext/"
    ):
        load_manifest_from_dict(data)


def test_load_manifest_asset_path_traversal_after_ext() -> None:
    """Test ValueError when asset destination_path escapes /ext/ via traversal."""
    data = {
        "name": "pack",
        "version": "1.0.0",
        "assets": [{"destination_path": "/ext/apps/../../../int/x.fap"}],
    }
    with pytest.raises(ValueError, match="doit rester sous /ext/ une fois normalisé"):
        load_manifest_from_dict(data)


def test_load_manifest_asset_path_outside_ext() -> None:
    """Test ValueError when asset destination_path is outside /ext/."""
    data = {
        "name": "pack",
        "version": "1.0.0",
        "assets": [{"destination_path": "/int/firmware_critical/override.bin"}],
    }
    with pytest.raises(ValueError, match="doit rester sous /ext/ une fois normalisé"):
        load_manifest_from_dict(data)


@pytest.mark.parametrize(
    "bad_category",
    ["../../../int", "Tools/Games", "Tools\\Games", ".", ".."],
)
def test_load_manifest_app_category_separator_or_dot(bad_category: str) -> None:
    """Test ValueError when app category contains separators or dot segments."""
    data = {
        "name": "pack",
        "version": "1.0.0",
        "apps": [
            {
                "name": "Malicious",
                "category": bad_category,
                "filename": "test.fap",
            }
        ],
    }
    with pytest.raises(ValueError, match="ne doit pas contenir de séparateur"):
        load_manifest_from_dict(data)


@pytest.mark.parametrize(
    "bad_filename",
    ["../../evil.fap", "sub/evil.fap", "sub\\evil.fap", ".", ".."],
)
def test_load_manifest_app_filename_separator_or_dot(bad_filename: str) -> None:
    """Test ValueError when app filename contains separators or dot segments."""
    data = {
        "name": "pack",
        "version": "1.0.0",
        "apps": [
            {
                "name": "Malicious",
                "category": "Tools",
                "filename": bad_filename,
            }
        ],
    }
    with pytest.raises(ValueError, match="ne doit pas contenir de séparateur"):
        load_manifest_from_dict(data)


def test_load_manifest_app_category_invalid_type() -> None:
    """Test ValueError when app category is not a string."""
    data = {
        "name": "pack",
        "version": "1.0.0",
        "apps": [
            {
                "name": "App",
                "category": {"a": 1},
                "filename": "app.fap",
            }
        ],
    }
    with pytest.raises(ValueError, match="doit être une chaîne non vide"):
        load_manifest_from_dict(data)


def test_load_manifest_invalid_content_type() -> None:
    """Test TypeError when app or asset content is not str or bytes."""
    app_data = {
        "name": "pack",
        "version": "1.0.0",
        "apps": [
            {
                "name": "App",
                "category": "Tools",
                "filename": "app.fap",
                "content": 12345,
            }
        ],
    }
    with pytest.raises(TypeError, match="doit être une chaîne ou des octets"):
        load_manifest_from_dict(app_data)

    asset_data = {
        "name": "pack",
        "version": "1.0.0",
        "assets": [
            {
                "destination_path": "/ext/dolphin/icon.bm",
                "content": 12345,
            }
        ],
    }
    with pytest.raises(TypeError, match="doit être une chaîne ou des octets"):
        load_manifest_from_dict(asset_data)
