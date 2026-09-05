"""Command-line interface for momentum-ultra."""

from __future__ import annotations

import argparse
import sys

from momentum_ultra import __version__


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="momentum-ultra",
        description="Outil de préparation post-flash pour Flipper Zero sous Momentum.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Affiche la version du programme et quitte.",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exécute en mode simulation sans écrire sur l'appareil (activé par défaut).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the momentum-ultra command-line interface."""
    parser = _build_parser()

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 0

    _ = args.dry_run
    return 0
