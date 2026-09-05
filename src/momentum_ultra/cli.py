"""Command-line interface for momentum-ultra."""

from __future__ import annotations

import argparse
import sys

from momentum_ultra import __version__
from momentum_ultra.bundle import BundleError, export_bundle, import_bundle
from momentum_ultra.device import (
    FlipperDeviceError,
    find_flipper,
    is_port_available,
)
from momentum_ultra.flipper_client import FlipperClient, FlipperClientError
from momentum_ultra.installer import execute_install_plan, get_default_pack
from momentum_ultra.manifest import generate_install_plan
from momentum_ultra.modules import (
    detect_connected_modules,
    get_default_module_configs,
)
from momentum_ultra.regions import RegionCode, get_available_regions, get_region_profile
from momentum_ultra.theme import get_available_themes, get_theme_profile


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
        "--diagnose-modules",
        action="store_true",
        help="Diagnostique et affiche les modules d'extension externes connectés au GPIO.",
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
    valid_regions = [r.value for r in get_available_regions()]
    parser.add_argument(
        "--region",
        default="EU",
        choices=valid_regions + [r.lower() for r in valid_regions],
        help="Profil régional pour les fréquences radio (EU, US, JP, WORLD). Par défaut : EU.",
    )
    valid_themes = [t.value for t in get_available_themes()]
    parser.add_argument(
        "--theme",
        default="default",
        choices=valid_themes + [t.lower() for t in valid_themes],
        help="Thème visuel Momentum (default, dark_stealth, retro_gamer, cyberpunk). Par défaut : default.",
    )
    parser.add_argument(
        "--bundle",
        metavar="FICHIER",
        help="Chemin vers un bundle personnalisé (.tar.gz ou .json) à installer.",
    )
    parser.add_argument(
        "--export-bundle",
        metavar="FICHIER",
        help="Exporte le pack Momentum Ultra vers une archive partageable (.tar.gz).",
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

    if args.export_bundle:
        return _handle_export_bundle(
            destination=args.export_bundle,
            region_str=args.region,
            theme_str=args.theme,
        )

    if args.detect:
        return _handle_detect()

    if args.diagnose_modules:
        return _handle_diagnose_modules()

    if args.install:
        return _handle_install(
            dry_run=args.dry_run,
            auto_confirm=args.yes,
            region_str=args.region,
            theme_str=args.theme,
            bundle_path=args.bundle,
        )

    return 0


def _handle_export_bundle(
    destination: str, region_str: str, theme_str: str = "default"
) -> int:
    """Handle exporting a shareable bundle."""
    try:
        pack = get_default_pack(region=region_str, theme=theme_str)
        out_file = export_bundle(pack, destination)
        print(f"Bundle '{pack.name}' exporté avec succès vers : {out_file}")
        return 0
    except (BundleError, OSError, ValueError) as err:
        print(f"Erreur lors de l'export du bundle : {err}", file=sys.stderr)
        return 1


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


def _handle_diagnose_modules() -> int:
    """Handle the --diagnose-modules command flow."""
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

    print(f"\n--- Diagnostic des modules GPIO sur {device.port} ---")
    try:
        with FlipperClient(port=device.port, dry_run=True) as client:
            gpio_output = client.send_cmd("gpio status")
            modules = detect_connected_modules(gpio_output)
            all_configs = get_default_module_configs()

            if not modules:
                print("Aucun module externe détecté sur le connecteur GPIO.")
                print(
                    "Note : Les modules CC1101, nRF24 et ESP32 sont configurables dans les réglages."
                )
            else:
                print(f"Modules détectés ({len(modules)}) :")
                for mod in modules:
                    cfg = all_configs.get(mod)
                    if cfg:
                        print(f"  • {cfg.name} : {cfg.description}")
            return 0
    except FlipperClientError as err:
        print(f"Erreur de communication : {err}", file=sys.stderr)
        return 1


def _handle_install(
    dry_run: bool,
    auto_confirm: bool,
    region_str: str,
    theme_str: str = "default",
    bundle_path: str | None = None,
) -> int:
    """Handle the --install / --prepare workflow."""
    try:
        profile = get_region_profile(region_str)
        theme_profile = get_theme_profile(theme_str)
    except ValueError as err:
        print(f"Erreur : {err}", file=sys.stderr)
        return 1

    if bundle_path:
        try:
            pack = import_bundle(bundle_path)
            print(f"Chargement du bundle externe : {pack.name} v{pack.version}")
        except BundleError as err:
            print(f"Erreur de bundle : {err}", file=sys.stderr)
            return 1
    else:
        pack = get_default_pack(region=profile.code, theme=theme_profile.name)

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

    if profile.code == RegionCode.WORLD and not bundle_path:
        print(
            "\n[Avertissement Légal] Le profil WORLD déverrouille les restrictions fréquentielles."
            "\nVous êtes légalement responsable des émissions radio selon votre juridiction locale.\n"
        )

    if not dry_run and not auto_confirm:
        confirm = input(
            f"Attention : vous allez écrire sur le Flipper Zero ({device.port}). Continuer ? [o/N] "
        )
        if confirm.strip().lower() not in ("o", "oui", "y", "yes"):
            print("Installation annulée par l'utilisateur.")
            return 0

    mode_label = "SIMULATION (--dry-run)" if dry_run else "ÉCRITURE RÉELLE"
    print(
        f"\n--- Préparation de Momentum Ultra ({pack.name}) sur {device.port} [{mode_label}] ---"
    )

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
    print(f"Pack installé : {pack.name} v{pack.version}")
    print(f"Région configurée : {profile.name}")
    print(f"Thème configuré : {theme_profile.title}")
    print("Conseils pour le premier démarrage :")
    print(" 1. Redémarrez votre Flipper Zero (touches Retour + Gauche).")
    print(" 2. Retrouvez vos applications dans le menu Applications.")
    print(" 3. Vos anciens fichiers ont été sauvegardés dans /ext/backup.")
    print("=" * 60)
    return 0
