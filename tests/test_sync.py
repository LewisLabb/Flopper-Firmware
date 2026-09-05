"""Unit tests for capture synchronization and local backup."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from momentum_ultra.flipper_client import (
    FlipperClient,
    FlipperCommandError,
    StorageItem,
)
from momentum_ultra.sync import (
    CaptureItem,
    SyncReport,
    export_captures_catalog,
    list_remote_captures,
    sync_captures_to_local,
)


def test_list_remote_captures() -> None:
    """Test scanning remote capture directories."""
    client = MagicMock(spec=FlipperClient)

    def mock_list_dir(path: str) -> list[StorageItem]:
        if path == "/ext/subghz":
            return [
                StorageItem(name="garage.sub", is_dir=False, size=1024),
                StorageItem(name="saved_sub", is_dir=True),
            ]
        elif path == "/ext/nfc":
            return [
                StorageItem(name="badge.nfc", is_dir=False, size=512),
            ]
        elif path == "/ext/lfrfid":
            raise FlipperCommandError("Directory does not exist")
        return []

    client.list_dir.side_effect = mock_list_dir

    items = list_remote_captures(client)
    assert len(items) == 2

    sub_item = next(i for i in items if i.category == "subghz")
    assert sub_item.filename == "garage.sub"
    assert sub_item.remote_path == "/ext/subghz/garage.sub"
    assert sub_item.size == 1024

    nfc_item = next(i for i in items if i.category == "nfc")
    assert nfc_item.filename == "badge.nfc"
    assert nfc_item.size == 512


def test_sync_captures_to_local_dry_run(tmp_path: Path) -> None:
    """Test syncing captures in dry-run mode."""
    client = MagicMock(spec=FlipperClient)
    client.dry_run = True

    client.list_dir.side_effect = lambda path: (
        [StorageItem(name="key.ir", is_dir=False, size=256)]
        if path == "/ext/infrared"
        else []
    )

    dest_dir = tmp_path / "captures"
    report = sync_captures_to_local(client=client, destination_dir=dest_dir)

    assert isinstance(report, SyncReport)
    assert len(report.synced_items) == 1
    assert report.total_bytes == 256
    assert (dest_dir / "infrared" / "key.ir").exists()
    assert (dest_dir / "captures_catalog.json").exists()


def test_sync_captures_to_local_real_mode(tmp_path: Path) -> None:
    """Test syncing captures in real download mode."""
    client = MagicMock(spec=FlipperClient)
    client.dry_run = False

    client.list_dir.side_effect = lambda path: (
        [StorageItem(name="card.nfc", is_dir=False, size=50)]
        if path == "/ext/nfc"
        else []
    )
    client.send_cmd.return_value = "File content NFC card payload"

    dest_dir = tmp_path / "captures_real"
    report = sync_captures_to_local(client=client, destination_dir=dest_dir)

    assert len(report.synced_items) == 1
    local_file = dest_dir / "nfc" / "card.nfc"
    assert local_file.exists()
    assert "File content NFC" in local_file.read_text(encoding="utf-8")
    client.send_cmd.assert_called_once_with("storage read /ext/nfc/card.nfc")


def test_export_captures_catalog(tmp_path: Path) -> None:
    """Test generating captures catalog JSON."""
    items = [
        CaptureItem(
            category="subghz",
            remote_path="/ext/subghz/car.sub",
            filename="car.sub",
            size=2048,
        )
    ]
    report = SyncReport(
        synced_items=items,
        destination_dir=tmp_path,
        total_bytes=2048,
    )

    cat_path = export_captures_catalog(report, tmp_path)
    assert cat_path.exists()

    data = json.loads(cat_path.read_text(encoding="utf-8"))
    assert data["total_files"] == 1
    assert data["total_bytes"] == 2048
    assert data["items"][0]["filename"] == "car.sub"
