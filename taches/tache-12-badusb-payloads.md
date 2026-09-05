# Fiche de tâche — Bibliothèque BadUSB et gestionnaire de payloads

## Titre

Implémenter le gestionnaire de payloads BadUSB, la validation DuckyScript et le déploiement d'une collection sécurisée de scripts d'administration et de test.

## Agent assigné

**Gemini (Antigravity).** Structuration de templates de scripts DuckyScript, validation de syntaxe et intégration dans le plan d'installation. 100% vérifiable par tests unitaires.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/badusb-payloads`

## Objectif

Permettre à l'utilisateur de déployer une bibliothèque organisée de scripts BadUSB / DuckyScript (outils d'administration, tests de saisie, diagnostics réseau) sous `/ext/badusb/` avec classification par système d'exploitation cible (Windows, macOS, Linux) et contrôle de conformité sans scripts destructeurs.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```text
src/momentum_ultra/badusb.py
src/momentum_ultra/installer.py
src/momentum_ultra/cli.py
tests/test_badusb.py
tests/test_cli.py
taches/tache-12-badusb-payloads.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01` à `11`.
- Tout script offensif ou destructeur.

## Contrat

### `src/momentum_ultra/badusb.py`

```python
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


def get_default_payloads() -> list[BadUSBPayload]:
    """Return the curated library of harmless administration and diagnostic BadUSB payloads."""


def validate_duckyscript(script: str) -> bool:
    """Validate that script uses standard DuckyScript syntax without forbidden/destructive patterns."""


def export_payload_assets(payloads: list[BadUSBPayload]) -> list[AssetEntry]:
    """Convert BadUSB payloads into AssetEntry files deployed under /ext/badusb/."""
```

### `src/momentum_ultra/installer.py` & `src/momentum_ultra/cli.py`

- Intégration des `AssetEntry` BadUSB dans `get_default_pack()`.
- Option CLI `--list-payloads` pour consulter l'inventaire des scripts disponibles.

## Critères d'acceptation

- [x] `pytest` passe à 100% avec tests unitaires complets
- [x] `ruff check .` et `ruff format --check .` ne signalent rien
- [x] `get_default_payloads` fournit des payloads pour Windows, macOS et Linux
- [x] `validate_duckyscript` valide la syntaxe DuckyScript (DELAY, STRING, GUI, ENTER, etc.)
- [x] `export_payload_assets` génère les scripts sous `/ext/badusb/{category}/{filename}`
- [x] L'option `--list-payloads` affiche la liste des payloads en français
- [x] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Module `badusb.py` implémenté avec validation syntaxique DuckyScript et bibliothèque d'administration système/réseau sans commandes destructrices. Option CLI `--list-payloads` et injection d'assets dans le pack d'installation. 80/80 tests automatisés passants, Ruff 100% propre.
- **Leçon d'aiguillage** : Alignement complet avec la boîte à outils BadUSB Flipper Zero.
