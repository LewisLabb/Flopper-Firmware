# Fiche de tâche — Personnalisation UI et thèmes visuels Momentum

## Titre

Implémenter la gestion des profils de thèmes visuels (Cyber Orange, Dark Stealth, Retro Gamer, Cyberpunk), la configuration de la barre d'état et le déploiement des assets graphiques Momentum.

## Agent assigné

**Gemini (Antigravity).** Modélisation de structures de configuration de thèmes, génération de fichiers JSON de paramètres d'affichage et intégration CLI. 100% vérifiable par tests unitaires.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/themes-ui-momentum`

## Objectif

Conformément au Pilier 1 du brief Momentum Ultra (« Architecture UI & Ergonomie Immédiate »), offrir à l'utilisateur le choix d'un thème visuel dès l'onboarding pour personnaliser instantanément l'affichage du Flipper Zero : style de la barre d'état (pourcentage de batterie, horloge, indicateurs radio), disposition du menu et animations de bureau.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```text
src/momentum_ultra/theme.py
src/momentum_ultra/cli.py
src/momentum_ultra/installer.py
tests/test_theme.py
tests/test_cli.py
taches/tache-10-themes-ui-momentum.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01` à `09`.
- Tout flashage de firmware ou accès physique sans mock.

## Contrat

### `src/momentum_ultra/theme.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import Any
from momentum_ultra.manifest import AssetEntry


class ThemeName(str, Enum):
    """Available curated UI themes."""

    DEFAULT = "default"  # Momentum classic
    DARK_STEALTH = "dark_stealth"  # Minimalist dark & tactical
    RETRO_GAMER = "retro_gamer"  # 8-bit handheld aesthetic
    CYBERPUNK = "cyberpunk"  # High-contrast tech vibe


class StatusBarStyle(str, Enum):
    """Battery and indicator layout for the top status bar."""

    FULL = "full"  # Battery %, Clock, Radio status
    MINIMAL = "minimal"  # Battery icon only
    BAR_PERCENT = "bar_percent"  # Battery % and icon


@dataclass(frozen=True)
class ThemeProfile:
    """Configuration profile for Momentum UI styling."""

    name: ThemeName
    title: str
    description: str
    status_bar: StatusBarStyle
    show_clock: bool
    animations_pack: str
    accent_color_hint: str


def get_theme_profile(name: ThemeName | str) -> ThemeProfile:
    """Retrieve theme configuration profile by name."""


def get_available_themes() -> list[ThemeName]:
    """List all available theme names."""


def export_theme_settings(profile: ThemeProfile) -> dict[str, Any]:
    """Generate settings dictionary for /ext/settings/momentum_ui.json."""


def get_theme_assets(profile: ThemeProfile) -> list[AssetEntry]:
    """Return theme-specific asset entries for dolphin/animations."""
```

### `src/momentum_ultra/cli.py` & `src/momentum_ultra/installer.py`

- Ajout de l'option `--theme {default,dark_stealth,retro_gamer,cyberpunk}` (valeur par défaut : `default`).
- Intégration du profil de thème dans le pack d'installation (`/ext/settings/momentum_ui.json` et assets de personnalisation sous `/ext/dolphin/`).

## Critères d'acceptation

- [x] `pytest` passe à 100% avec tests unitaires complets
- [x] `ruff check .` et `ruff format --check .` ne signalent rien
- [x] Les 4 thèmes (`DEFAULT`, `DARK_STEALTH`, `RETRO_GAMER`, `CYBERPUNK`) sont définis et exportables
- [x] `export_theme_settings` génère une configuration JSON valide
- [x] `get_theme_assets` fournit les assets graphiques associés
- [x] L'option `--theme` est reconnue par le CLI et intégrée à l'onboarding
- [x] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Module `theme.py` complet avec 4 profils de thèmes et réglages de status bar implémentés. Option CLI `--theme` ajoutée avec injection dans `/ext/settings/momentum_ui.json` et les assets `/ext/dolphin/`. 68/68 tests automatisés passants, Ruff 100% propre.
- **Leçon d'aiguillage** : Conforme au Pilier 1 du brief (« Architecture UI & Ergonomie Immédiate »).
