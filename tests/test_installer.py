"""Unit tests for the installer execution module."""

from __future__ import annotations

from unittest.mock import MagicMock

from momentum_ultra.flipper_client import FlipperClient
from momentum_ultra.installer import execute_install_plan, get_default_pack
from momentum_ultra.manifest import (
    ActionType,
    PackManifest,
    PlanAction,
)


def test_get_default_pack_validity() -> None:
    """Test default pack structure and contents."""
    pack = get_default_pack()
    assert isinstance(pack, PackManifest)
    assert len(pack.apps) > 0
    assert len(pack.assets) > 0
    assert len(pack.settings) > 0


def test_execute_install_plan_dry_run() -> None:
    """Test plan execution in simulation mode."""
    client = MagicMock(spec=FlipperClient)
    client.dry_run = True

    plan = [
        PlanAction(
            action_type=ActionType.CREATE_DIR,
            target_path="/ext/apps",
            description="Create dir",
        ),
        PlanAction(
            action_type=ActionType.WRITE_FILE,
            target_path="/ext/apps/test.fap",
            source_content=b"content",
            description="Write app",
        ),
        PlanAction(
            action_type=ActionType.BACKUP,
            target_path="/ext/old_apps",
            description="Backup old",
        ),
    ]

    progress_calls: list[tuple[PlanAction, int, int]] = []
    results = execute_install_plan(
        client=client,
        plan=plan,
        on_progress=lambda a, c, t: progress_calls.append((a, c, t)),
    )

    assert len(results) == 3
    assert all("[SIMULATION]" in r for r in results)
    assert len(progress_calls) == 3
    assert progress_calls[0][1] == 1
    assert progress_calls[2][1] == 3

    client.mkdir.assert_called_once_with("/ext/apps")
    client.write_file.assert_called_once_with("/ext/apps/test.fap", b"content")
    client.backup_item.assert_called_once_with("/ext/old_apps")


def test_execute_install_plan_real_mode() -> None:
    """Test plan execution in real mode logs success status."""
    client = MagicMock(spec=FlipperClient)
    client.dry_run = False

    plan = [
        PlanAction(
            action_type=ActionType.CREATE_DIR,
            target_path="/ext/apps",
            description="Create apps dir",
        ),
    ]

    results = execute_install_plan(client=client, plan=plan)
    assert len(results) == 1
    assert "[SUCCÈS]" in results[0]
    client.mkdir.assert_called_once_with("/ext/apps")
