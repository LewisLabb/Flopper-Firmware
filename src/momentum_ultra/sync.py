"""Synchronize and catalog remote Flipper Zero captures to the host machine."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from momentum_ultra.flipper_client import (
    FlipperClient,
    FlipperCommandError,
)

CAPTURE_DIRECTORIES: dict[str, str] = {
    "subghz": "/ext/subghz",
    "nfc": "/ext/nfc",
    "lfrfid": "/ext/lfrfid",
    "infrared": "/ext/infrared",
    "ibutton": "/ext/ibutton",
    "badusb": "/ext/badusb",
}


@dataclass(frozen=True)
class CaptureItem:
    """Metadata representation of a captured signal or payload on Flipper."""

    category: str
    remote_path: str
    filename: str
    size: int


@dataclass(frozen=True)
class SyncReport:
    """Summary report of a capture synchronization operation."""

    synced_items: list[CaptureItem]
    destination_dir: Path
    total_bytes: int


def list_remote_captures(client: FlipperClient) -> list[CaptureItem]:
    """Scan standard Flipper capture directories and return all found capture files."""
    captured: list[CaptureItem] = []

    for category, remote_dir in CAPTURE_DIRECTORIES.items():
        try:
            items = client.list_dir(remote_dir)
        except FlipperCommandError:
            # Directory may not exist yet on fresh Flipper SD card
            continue

        for item in items:
            if not item.is_dir:
                captured.append(
                    CaptureItem(
                        category=category,
                        remote_path=f"{remote_dir}/{item.name}",
                        filename=item.name,
                        size=item.size,
                    )
                )

    return captured


def sync_captures_to_local(
    client: FlipperClient,
    destination_dir: str | Path,
) -> SyncReport:
    """Download and catalog all remote capture files to the host destination folder."""
    dest_path = Path(destination_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    items = list_remote_captures(client)
    total_bytes = 0

    for item in items:
        cat_dir = dest_path / item.category
        cat_dir.mkdir(parents=True, exist_ok=True)
        local_file = cat_dir / item.filename

        # Download or simulate download
        if not client.dry_run:
            output = client.send_cmd(f"storage read {item.remote_path}")
            local_file.write_bytes(output.encode("utf-8", errors="replace"))
        else:
            # In simulation, write a placeholder header
            local_file.write_text(
                f"# [SIMULATION] Captured file from Flipper: {item.remote_path}\n",
                encoding="utf-8",
            )

        total_bytes += item.size

    report = SyncReport(
        synced_items=items,
        destination_dir=dest_path,
        total_bytes=total_bytes,
    )

    export_captures_catalog(report, dest_path)
    return report


def export_captures_catalog(report: SyncReport, destination_dir: str | Path) -> Path:
    """Generate captures_catalog.json in the local destination directory."""
    dest_path = Path(destination_dir)
    catalog_path = dest_path / "captures_catalog.json"

    data: dict[str, Any] = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "total_files": len(report.synced_items),
        "total_bytes": report.total_bytes,
        "items": [asdict(item) for item in report.synced_items],
    }

    catalog_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return catalog_path
