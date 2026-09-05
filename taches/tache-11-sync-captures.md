# Fiche de tâche — Synchronisation et sauvegarde des captures locales

## Titre

Implémenter la synchronisation et la sauvegarde locale des captures Flipper Zero (Sub-GHz, NFC, RFID, Infrarouge, iButton, BadUSB) vers l'ordinateur hôte avec génération d'inventaire.

## Agent assigné

**Gemini (Antigravity).** Parcours d'arborescence, transfert de fichiers simulé, sérialisation d'inventaire JSON et intégration CLI. 100% vérifiable par tests unitaires.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/sync-captures`

## Objectif

Conformément au Pilier 2 du brief Momentum Ultra (« Workflow Capture & Organisation des Fichiers »), permettre à l'utilisateur de sauvegarder et d'organiser automatiquement sur son ordinateur toutes les captures réalisées sur le terrain avec le Flipper Zero (`.sub`, `.nfc`, `.rfid`, `.ir`, `.ibtn`, `.badusb`), avec conservation des métadonnées et sans jamais altérer ni supprimer les fichiers sur la carte SD de l'appareil.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```text
src/momentum_ultra/sync.py
src/momentum_ultra/cli.py
tests/test_sync.py
tests/test_cli.py
taches/tache-11-sync-captures.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01` à `10`.
- Toute commande de suppression sur la carte SD.

## Contrat

### `src/momentum_ultra/sync.py`

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from momentum_ultra.flipper_client import FlipperClient


CAPTURE_DIRECTORIES = {
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


def sync_captures_to_local(
    client: FlipperClient,
    destination_dir: str | Path,
) -> SyncReport:
    """Download and catalog all remote capture files to the host destination folder."""


def export_captures_catalog(report: SyncReport, destination_dir: str | Path) -> Path:
    """Generate captures_catalog.json in the local destination directory."""
```

### `src/momentum_ultra/cli.py`

- Ajout de l'option `--backup-captures <dossier>` : sauvegarde et organise les captures du Flipper vers le répertoire local spécifié.

## Critères d'acceptation

- [x] `pytest` passe à 100% avec tests unitaires simulés
- [x] `ruff check .` et `ruff format --check .` ne signalent rien
- [x] `list_remote_captures` inspecte les répertoires standards de captures
- [x] `sync_captures_to_local` télécharge et organise les fichiers par sous-dossiers
- [x] `export_captures_catalog` produit un inventaire JSON valide
- [x] L'option `--backup-captures` fonctionne de bout en bout via `main()`
- [x] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Module `sync.py` de synchronisation locale et d'inventaire JSON des captures (`.sub`, `.nfc`, `.rfid`, `.ir`, `.ibtn`, `.badusb`) implémenté sans altération des données SD. Option CLI `--backup-captures` intégrée avec refactorisation propre de `cli.py` (275 lignes). 73/73 tests passants, Ruff 100% propre.
- **Leçon d'aiguillage** : Alignement complet avec le Pilier 2 du brief (« Workflow Capture & Organisation des Fichiers »).
