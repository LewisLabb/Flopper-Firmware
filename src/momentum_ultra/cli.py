"""Command-line interface for momentum-ultra."""

from __future__ import annotations

import argparse
import sys

from momentum_ultra import __version__
from momentum_ultra.device import (
    FlipperDeviceError,
    find_flipper,
    is_port_available,
)
from momentum_ultra.flipper_client import FlipperClient, FlipperClientError
from momentum_ultra.installer import execute_install_plan, get_default_pack
from momentum_ultra.manifest import generate_install_plan


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
    parser.add_argument(
        "--detect",
        action="store_true",
        help="Détecte le Flipper Zero connecté et vérifie la disponibilité du port série.",
    )
    parser.add_argument(
        "--install",
        "--prepare",
        dest="install",
        action="store_true",
        help="Installe le pack Momentum Ultra et configure le Flipper Zero.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Confirme automatiquement l'écriture sans invite interactive.",
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
        return int(exc.code) if isinstance(exc.code, int) else 1

    if args.detect:
        return _handle_detect()

    if args.install:
        return _handle_install(dry_run=args.dry_run, auto_confirm=args.yes)

    return 0


def _handle_detect() -> int:
    """Handle the --detect command flow."""
    try:
        device = find_flipper()
    except FlipperDeviceError as err:
        print(f"Erreur : {err}", file=sys.stderr)
        return 1

    if not is_port_available(device.port):
        print(
            f"Flipper Zero détecté sur {device.port}, mais le port est occupé "
            "(qFlipper ou un autre outil est-il ouvert ?).",
            file=sys.stderr,
        )
        return 1

    print(f"Flipper Zero détecté sur {device.port}.")
    return 0


def _handle_install(dry_run: bool, auto_confirm: bool) -> int:
    """Handle the --install / --prepare workflow."""
    try:
        device = find_flipper()
    except FlipperDeviceError as err:
        print(f"Erreur : {err}", file=sys.stderr)
        return 1

    if not is_port_available(device.port):
        print(
            f"Flipper Zero détecté sur {device.port}, mais le port est inaccessible.",
            file=sys.stderr,
        )
        return 1

    if not dry_run and not auto_confirm:
        confirm = input(
            f"Attention : vous allez écrire sur le Flipper Zero ({device.port}). Continuer ? [o/N] "
        )
        if confirm.strip().lower() not in ("o", "oui", "y", "yes"):
            print("Installation annulée par l'utilisateur.")
            return 0

    mode_label = "SIMULATION (--dry-run)" if dry_run else "ÉCRITURE RÉELLE"
    print(f"\n--- Préparation de Momentum Ultra sur {device.port} [{mode_label}] ---")

    pack = get_default_pack()
    plan = generate_install_plan(pack, backup_existing=True)

    try:
        with FlipperClient(port=device.port, dry_run=dry_run) as client:
            execute_install_plan(
                client=client,
                plan=plan,
                on_progress=lambda action, curr, tot: print(
                    f"[{curr}/{tot}] {action.description}"
                ),
            )
    except FlipperClientError as err:
        print(f"Erreur lors de la communication : {err}", file=sys.stderr)
        return 1

    print("\n" + "=" * 60)
    print("Préparation terminée avec succès !")
    print("Conseils pour le premier démarrage :")
    print(" 1. Redémarrez votre Flipper Zero (touches Retour + Gauche).")
    print(" 2. Retrouvez vos applications dans le menu Applications.")
    print(" 3. Vos anciens fichiers ont été sauvegardés dans /ext/backup.")
    print("=" * 60)
    return 0
