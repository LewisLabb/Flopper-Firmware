# Fiche de tâche — Gestion des manifestes et plans d'installation

## Titre

Implémenter la modélisation, le chargement et la validation des manifestes de packs (applications, assets, réglages) et la génération du plan d'installation.

## Agent assigné

**Gemini (Antigravity).** Modélisation de données typées, validation de dictionnaires/fichiers et génération de structures déterministes. Entièrement vérifiable par tests unitaires.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/gestion-manifestes`

## Objectif

Permettre à l'outil de charger et valider des manifestes de configuration définissant les applications à installer (`.fap`), les assets (animations, icônes) et le profil de réglages Momentum. Le module génère une liste ordonnée d'actions à entreprendre (`InstallPlan`) sans toucher directement à l'appareil.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```
src/momentum_ultra/manifest.py
tests/test_manifest.py
taches/tache-04-gestion-manifestes.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01-squelette-projet.md`, `taches/tache-02-detection-port.md`, `taches/tache-03-client-serie-flipper.md`.
- Toute communication série directe (réservée à `flipper_client`).
- Fichiers binaires réels (les tests utilisent des mocks et structures en mémoire).

## Contrat

### `src/momentum_ultra/manifest.py`

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ActionType(str, Enum):
    """Type of installation action."""

    CREATE_DIR = "create_dir"
    WRITE_FILE = "write_file"
    BACKUP = "backup"


@dataclass(frozen=True)
class PlanAction:
    """Single installation plan action."""

    action_type: ActionType
    target_path: str
    source_content: bytes | None = None
    description: str = ""


@dataclass(frozen=True)
class AppEntry:
    """Application to be installed on Flipper."""

    name: str
    category: str
    filename: str
    content: bytes = field(repr=False, default=b"")


@dataclass(frozen=True)
class AssetEntry:
    """Asset file to deploy."""

    destination_path: str
    content: bytes = field(repr=False, default=b"")


@dataclass(frozen=True)
class PackManifest:
    """Manifest describing a curated curation pack."""

    name: str
    version: str
    description: str
    apps: list[AppEntry] = field(default_factory=list)
    assets: list[AssetEntry] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)


def load_manifest_from_dict(data: dict[str, Any]) -> PackManifest:
    """Load and validate a PackManifest from a dictionary."""


def generate_install_plan(
    manifest: PackManifest, backup_existing: bool = True
) -> list[PlanAction]:
    """Generate the ordered list of PlanAction items needed to install the pack."""
```

Règles de comportement :
1. `load_manifest_from_dict(data)` :
   - Vérifie la présence des champs obligatoires (`name`, `version`).
   - Lève `ValueError` si des champs requis manquent ou si les formats sont invalides.
2. `generate_install_plan(manifest, backup_existing=True)` :
   - Génère les actions de création de répertoires de base (`/ext/apps`, `/ext/apps/<Category>`, `/ext/dolphin`, `/ext/badusb`, etc.).
   - Pour chaque application, cible `/ext/apps/{category}/{filename}`.
   - Pour chaque asset, cible le chemin de destination spécifié sous `/ext/...`.
   - Si `backup_existing=True`, ajoute les étapes de sauvegarde préalable pour les dossiers cibles.
   - Retourne une liste ordonnée et déterministe de `PlanAction`.

## Critères d'acceptation

- [ ] `pytest` passe à 100% avec tests unitaires complets
- [ ] `ruff check .` ne signale rien
- [ ] `ruff format --check .` ne signale rien
- [ ] `load_manifest_from_dict` valide les types et champs obligatoires
- [ ] `generate_install_plan` produit un plan d'installation ordonné et complet
- [ ] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Modèles de données `PackManifest`, `AppEntry`, `AssetEntry`, `PlanAction` implémentés avec validation robuste (`load_manifest_from_dict`) et génération de plan ordonné (`generate_install_plan`) incluant la sauvegarde préventive. 33 tests automatisés passants au total, Ruff 100% conforme.
- **Leçon d'aiguillage** : Modélisation et validation de structures de données pures parfaitement adaptées à une exécution mécanique par Gemini.
