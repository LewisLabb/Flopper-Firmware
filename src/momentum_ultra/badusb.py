"""BadUSB DuckyScript payload library and validator for Flipper Zero."""

import json
from dataclasses import dataclass
from enum import Enum

from momentum_ultra.manifest import AssetEntry


class TargetOS(str, Enum):
    """Target operating system for BadUSB payloads."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    CROSS_PLATFORM = "multi"


class PayloadCategory(str, Enum):
    """Category of utility payload."""

    ADMIN = "admin"
    NETWORK = "network"
    DEMO = "demo"


@dataclass(frozen=True)
class BadUSBPayload:
    """Single BadUSB payload script definition."""

    name: str
    filename: str
    target_os: TargetOS
    category: PayloadCategory
    description: str
    script_content: str


_DEFAULT_PAYLOADS: list[BadUSBPayload] = [
    BadUSBPayload(
        name="Windows Diagnostic Système",
        filename="win_sysinfo.txt",
        target_os=TargetOS.WINDOWS,
        category=PayloadCategory.ADMIN,
        description="Ouvre l'invite de commande et affiche les informations système.",
        script_content="DELAY 1000\nGUI r\nDELAY 500\nSTRING cmd /k systeminfo\nENTER\n",
    ),
    BadUSBPayload(
        name="Windows Test Connectivité Réseau",
        filename="win_ping_test.txt",
        target_os=TargetOS.WINDOWS,
        category=PayloadCategory.NETWORK,
        description="Teste la connectivité DNS et passerelle via un ping ICMP.",
        script_content="DELAY 1000\nGUI r\nDELAY 500\nSTRING cmd /k ping -n 4 1.1.1.1\nENTER\n",
    ),
    BadUSBPayload(
        name="macOS Diagnostic Réseau",
        filename="mac_netinfo.txt",
        target_os=TargetOS.MACOS,
        category=PayloadCategory.NETWORK,
        description="Ouvre le Terminal macOS et affiche la configuration réseau ifconfig.",
        script_content="DELAY 1000\nGUI SPACE\nDELAY 500\nSTRING Terminal\nENTER\nDELAY 1000\nSTRING ifconfig\nENTER\n",
    ),
    BadUSBPayload(
        name="Linux Diagnostic Matériel",
        filename="linux_hwinfo.txt",
        target_os=TargetOS.LINUX,
        category=PayloadCategory.ADMIN,
        description="Ouvre un terminal Linux et affiche les informations CPU et noyau.",
        script_content="DELAY 1000\nCTRL ALT t\nDELAY 600\nSTRING uname -a && lscpu\nENTER\n",
    ),
    BadUSBPayload(
        name="Démonstration Clavier Multiplateforme",
        filename="demo_banner.txt",
        target_os=TargetOS.CROSS_PLATFORM,
        category=PayloadCategory.DEMO,
        description="Saisit une bannière de bienvenue Momentum Ultra.",
        script_content="DELAY 1000\nSTRING Momentum Ultra - Flipper Zero Onboarding Completed!\nENTER\n",
    ),
]

_VALID_DUCKY_KEYWORDS = {
    "REM",
    "DELAY",
    "STRING",
    "GUI",
    "WINDOWS",
    "ENTER",
    "CTRL",
    "ALT",
    "SHIFT",
    "TAB",
    "SPACE",
    "ESCAPE",
    "ESC",
    "DOWN",
    "UP",
    "LEFT",
    "RIGHT",
    "CAPSLOCK",
    "DELETE",
    "BACKSPACE",
    "MENU",
    "DEFAULT_DELAY",
    "DEFAULTDELAY",
}

_FORBIDDEN_PATTERNS = [
    "rm -rf /",
    "format c:",
    "del /f /s /q c:\\",
    "mkfs",
    ":(){ :|:& };:",
]


def get_default_payloads() -> list[BadUSBPayload]:
    """Return the curated library of harmless administration and diagnostic BadUSB payloads."""
    return list(_DEFAULT_PAYLOADS)


def validate_duckyscript(script: str) -> bool:
    """Validate DuckyScript *syntax* only — not the safety of what the script does.

    Returns True when the script is non-empty and every non-comment line begins
    with a known DuckyScript keyword. A short best-effort denylist also rejects a
    few blatantly destructive one-liners, but that denylist is NOT a safety
    guarantee: it is trivially bypassed (e.g. ``rm -rf ~``, piped downloads) and
    must never be relied on to sanitize third-party scripts.
    """
    if not script or not script.strip():
        return False

    script_lower = script.lower()
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern in script_lower:
            return False

    for line in script.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("REM"):
            continue

        keyword = line_clean.split()[0].upper()
        if keyword not in _VALID_DUCKY_KEYWORDS:
            return False

    return True


def export_payload_assets(payloads: list[BadUSBPayload]) -> list[AssetEntry]:
    """Convert BadUSB payloads into AssetEntry files deployed under /ext/badusb/."""
    assets: list[AssetEntry] = []
    manifest_data = []

    for payload in payloads:
        if not validate_duckyscript(payload.script_content):
            raise ValueError(f"Payload invalide ou non conforme : {payload.name}")

        dest_path = f"/ext/badusb/{payload.category.value}/{payload.filename}"
        assets.append(
            AssetEntry(
                destination_path=dest_path,
                content=payload.script_content.encode("utf-8"),
            )
        )
        manifest_data.append(
            {
                "name": payload.name,
                "filename": payload.filename,
                "target_os": payload.target_os.value,
                "category": payload.category.value,
                "path": dest_path,
                "description": payload.description,
            }
        )

    assets.append(
        AssetEntry(
            destination_path="/ext/badusb/manifest.json",
            content=json.dumps(manifest_data, indent=2).encode("utf-8"),
        )
    )

    return assets
