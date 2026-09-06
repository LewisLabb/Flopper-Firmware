"""Command-line interface for flopper."""

from __future__ import annotations

import argparse
import sys

from flopper import __version__
from flopper.bundle import BundleError, export_bundle, import_bundle
from flopper.device import (
    FlipperDevice,
    FlipperDeviceError,
    find_flipper,
    is_port_available,
)
from flopper.flipper_client import FlipperClient, FlipperClientError
from flopper.installer import (
    build_modules_settings_action,
    build_region_settings_action,
    execute_install_plan,
    get_default_pack,
)
from flopper.manifest import generate_install_plan
from flopper.modules import ModuleType, get_default_module_configs
from flopper.regions import RegionCode, get_region_profile
from flopper.sync import sync_captures_to_local
from flopper.theme import get_available_themes, get_theme_profile


def _parse_modules_arg(raw: str) -> list[ModuleType]:
    """Parse the --modules comma-separated list into ModuleType values."""
    result: list[ModuleType] = []
    for token in raw.split(","):
        if not (token := token.strip().lower()):
            continue
        try:
            result.append(ModuleType(token))
        except ValueError as exc:
            valid = ", ".join(m.value for m in ModuleType)
            raise ValueError(
                f"Module inconnu '{token}'. Modules valides : {valid}."
            ) from exc
    return result


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="flopper",
        description="Outil de préparation post-flash pour Flipper Zero sous le firmware standard.",
    )
    add = parser.add_argument
    add("--version", action="version", version=__version__, help="Affiche la version.")
    add(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Mode simulation.",
    )
    add("--detect", action="store_true", help="Vérifie la connexion du Flipper Zero.")
    add(
        "--diagnose-modules",
        action="store_true",
        help="Diagnostique les modules GPIO connectés.",
    )
    add(
        "--modules",
        metavar="LISTE",
        default="",
        help="Modules externes connectés séparés par virgules (cc1101, nrf24, esp32, combo_2in1).",
    )
    add(
        "--install",
        "--prepare",
        dest="install",
        action="store_true",
        help="Installe le pack.",
    )
    add("-y", "--yes", action="store_true", help="Confirme automatiquement l'écriture.")
    add("--region", default="EU", help="Profil régional radio (EU, US, JP, WORLD).")
    valid_themes = [t.value for t in get_available_themes()]
    add(
        "--theme",
        default="default",
        choices=valid_themes + [t.lower() for t in valid_themes],
        help=(
            "Profil de préférences visuelles Flopper (extension propre à "
            "ce projet : n'installe pas d'asset pack Momentum natif)."
        ),
    )
    add("--bundle", metavar="FICHIER", help="Chemin vers un bundle personnalisé.")
    add("--export-bundle", metavar="FICHIER", help="Exporte vers un bundle .tar.gz.")
    add("--backup-captures", metavar="DOSSIER", help="Sauvegarde les captures locales.")
    add(
        "--list-payloads",
        action="store_true",
        help="Affiche la liste des payloads BadUSB.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the flopper command-line interface."""
    parser = _build_parser()
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1

    try:
        get_region_profile(args.region)
    except ValueError as err:
        print(f"Erreur : {err}", file=sys.stderr)
        return 1

    if args.list_payloads:
        return _handle_list_payloads()
    if args.export_bundle:
        return _handle_export_bundle(args.export_bundle, args.region, args.theme)
    if args.backup_captures:
        return _handle_backup_captures(args.backup_captures, args.dry_run)
    if args.detect:
        return _handle_detect()
    if args.diagnose_modules:
        return _handle_diagnose_modules()
    if args.install:
        return _handle_install(
            args.dry_run, args.yes, args.region, args.theme, args.bundle, args.modules
        )
    return 0


def _handle_list_payloads() -> int:
    """Display available BadUSB payloads library."""
    from flopper.badusb import get_default_payloads

    payloads = get_default_payloads()
    print(f"\n--- Bibliothèque de payloads BadUSB ({len(payloads)} scripts) ---")
    for p in payloads:
        print(
            f"  • [{p.target_os.value.upper()}] {p.name} ({p.filename}) : {p.description}"
        )
    return 0


def _get_connected_device() -> FlipperDevice | None:
    """Find and validate connected Flipper Zero availability."""
    try:
        device = find_flipper()
    except FlipperDeviceError as err:
        print(f"Erreur : {err}", file=sys.stderr)
        return None

    if not is_port_available(device.port):
        print(
            f"Flipper Zero détecté sur {device.port}, mais le port est occupé "
            "(qFlipper ou un autre outil est-il ouvert ?).",
            file=sys.stderr,
        )
        return None
    return device


def _handle_backup_captures(destination: str, dry_run: bool) -> int:
    """Handle capture synchronization to local destination folder."""
    if not (device := _get_connected_device()):
        return 1
    try:
        with FlipperClient(port=device.port, dry_run=dry_run) as client:
            report = sync_captures_to_local(client, destination)
            print(
                f"Sauvegarde terminée : {len(report.synced_items)} fichiers synchronisés."
            )
            return 0
    except (FlipperClientError, OSError) as err:
        print(f"Erreur lors de la synchronisation : {err}", file=sys.stderr)
        return 1


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
    if not (device := _get_connected_device()):
        return 1
    print(f"Flipper Zero détecté sur {device.port}.")
    return 0


def _handle_diagnose_modules() -> int:
    """List supported external modules and their pinout for manual verification."""
    configs = get_default_module_configs()
    print(
        "\n--- Modules externes pris en charge (vérification manuelle du câblage) ---"
    )
    print(
        "Le CLI série du Flipper Zero ne permet pas de détecter automatiquement\n"
        "quel module est branché sur le connecteur GPIO. Comparez votre câblage\n"
        "à la liste ci-dessous, puis déclarez vos modules avec --modules lors de --install.\n"
    )
    for cfg in configs.values():
        print(f"  • {cfg.name} ({cfg.module_type.value}) : {cfg.description}")
    return 0


def _handle_install(
    dry_run: bool,
    auto_confirm: bool,
    region_str: str,
    theme_str: str = "default",
    bundle_path: str | None = None,
    modules_str: str = "",
) -> int:
    """Handle the --install / --prepare workflow."""
    try:
        profile = get_region_profile(region_str)
        theme_profile = get_theme_profile(theme_str)
        modules_list = _parse_modules_arg(modules_str)
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
        pack = get_default_pack(
            region=profile.code, modules=modules_list, theme=theme_profile.name
        )

    if not (device := _get_connected_device()):
        return 1

    if profile.code == RegionCode.WORLD:
        print(
            "\nAttention : Le profil WORLD déverrouille les restrictions fréquentielles. "
            "L'utilisateur demeure légalement responsable des émissions radio selon sa "
            "législation locale.\n"
        )

    if not dry_run and not auto_confirm:
        prompt = f"Attention : vous allez écrire sur le Flipper Zero ({device.port}). Continuer ? [o/N] "
        if input(prompt).strip().lower() not in ("o", "oui", "y", "yes"):
            print("Installation annulée par l'utilisateur.")
            return 0

    mode_label = "SIMULATION (--dry-run)" if dry_run else "ÉCRITURE RÉELLE"
    print(
        f"\n--- Préparation de Flopper ({pack.name}) sur {device.port} [{mode_label}] ---"
    )

    plan = generate_install_plan(pack, backup_existing=True)
    plan.append(build_region_settings_action(profile))
    plan.append(build_modules_settings_action(modules_list))
    try:
        with FlipperClient(port=device.port, dry_run=dry_run) as client:
            execute_install_plan(
                client, plan, lambda a, c, t: print(f"[{c}/{t}] {a.description}")
            )
    except FlipperClientError as err:
        print(f"Erreur lors de la communication : {err}", file=sys.stderr)
        return 1

    print(
        f"\n{'=' * 60}\n"
        "Préparation terminée avec succès !\n"
        f"Pack installé : {pack.name} v{pack.version}\n"
        f"Région configurée : {profile.name}\n"
        f"Thème configuré : {theme_profile.title}\n"
        "Conseils pour le premier démarrage :\n"
        " 1. Redémarrez votre Flipper Zero (touches Retour + Gauche).\n"
        " 2. Retrouvez vos applications dans le menu Applications.\n"
        " 3. Vos anciens fichiers ont été sauvegardés dans /ext/backup.\n"
        f"{'=' * 60}"
    )
    return 0
