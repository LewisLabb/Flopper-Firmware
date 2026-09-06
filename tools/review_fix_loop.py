"""Review-and-fix loop that keeps the Flopper codebase free of Flopper branding."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
REPLACEMENTS = (
    ("flopper", "flopper"),
    ("flopper", "flopper"),
    ("Flopper", "Flopper"),
    ("Flopper", "Flopper"),
    ("FLOPPER", "FLOPPER"),
    ("flopper", "flopper"),
)


def iter_files() -> list[Path]:
    """Return project files to scan and normalize."""
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def scan_forbidden() -> list[tuple[Path, str]]:
    """Return references to legacy project naming that still need fixing."""
    hits: list[tuple[Path, str]] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for old, _ in REPLACEMENTS:
            if old.lower() in text.lower():
                hits.append((path, old))
                break
    return hits


def normalize_file(path: Path) -> bool:
    """Replace legacy naming with the Flopper brand in a single file."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False

    updated = text
    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new)

    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> int:
    """Run the review-and-fix cycle and report any remaining forbidden references."""
    changed = 0
    for path in iter_files():
        if normalize_file(path):
            changed += 1

    remaining = scan_forbidden()
    print(f"Updated files: {changed}")
    if remaining:
        print(f"Remaining forbidden references: {len(remaining)}")
        for path, token in remaining[:10]:
            print(f" - {path.relative_to(ROOT)} :: {token}")
        return 1

    print("No forbidden Flopper references remain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
