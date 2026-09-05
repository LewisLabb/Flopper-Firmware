# Fiche de tâche — Profils région-safe et configuration responsable

## Titre

Implémenter la gestion des profils région-safe (EU, US, JP, WORLD), l'étiquetage clair des bandes de fréquences autorisées et la génération de la configuration radio.

## Agent assigné

**Gemini (Antigravity).** Modélisation de tables de fréquences et génération de configuration déterministe. 100% vérifiable par tests unitaires.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/profils-region-safe`

## Objectif

Conformément au Pilier 6 du brief Momentum Ultra (« Responsable par défaut »), l'outil doit permettre à l'utilisateur de spécifier son profil régional (`EU`, `US`, `JP`, `WORLD`) dès l'onboarding. Chaque profil active les plages de fréquences adaptées aux réglementations locales (CE, FCC, MIC) avec un étiquetage transparent des bandes d'émission/réception. Le profil généré est injecté dans le plan d'installation sous `/ext/settings/region.json`.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```text
src/momentum_ultra/regions.py
src/momentum_ultra/cli.py
src/momentum_ultra/installer.py
tests/test_regions.py
tests/test_cli.py
taches/tache-06-profils-region-safe.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01` à `05`.
- Tout flashage de firmware ou accès physique sans mock.

## Contrat

### `src/momentum_ultra/regions.py`

```python
from dataclasses import dataclass
from enum import Enum


class RegionCode(str, Enum):
    """Supported geographical regulatory regions."""

    EU = "EU"  # CE (433.05-434.79 MHz, 868.15-868.55 MHz)
    US = "US"  # FCC (304.10-321.95 MHz, 433.05-434.79 MHz, 915.00-928.00 MHz)
    JP = "JP"  # MIC (312.00-315.25 MHz, 920.50-923.50 MHz)
    WORLD = "WORLD"  # Déverrouillé (avertissement légal obligatoire)


@dataclass(frozen=True)
class FrequencyBand:
    """Frequency band specification in Hz."""

    start_hz: int
    end_hz: int
    duty_cycle: float | None = None
    max_power_dbm: int | None = None


@dataclass(frozen=True)
class RegionProfile:
    """Regional regulatory profile with legal frequency bands."""

    code: RegionCode
    name: str
    regulatory_body: str
    subghz_tx_bands: list[FrequencyBand]
    description: str


def get_region_profile(code: RegionCode | str) -> RegionProfile:
    """Get regulatory profile by code."""


def get_available_regions() -> list[RegionCode]:
    """List all available region codes."""


def export_region_config(profile: RegionProfile) -> dict[str, object]:
    """Export region profile to Flipper settings dictionary."""
```

### `src/momentum_ultra/cli.py` & `src/momentum_ultra/installer.py`

- Option `--region {EU,US,JP,WORLD}` (valeur par défaut : `EU`).
- Si `WORLD` est sélectionné en écriture réelle (`--no-dry-run`), afficher un avertissement légal clair : `"Attention : Le profil WORLD déverrouille les restrictions fréquentielles. L'utilisateur demeure légalement responsable des émissions radio selon sa législation locale."`
- Intégrer le fichier `/ext/settings/region.json` dans le plan d'installation.

## Critères d'acceptation

- [ ] `pytest` passe à 100%
- [ ] `ruff check .` et `ruff format --check .` ne signalent rien
- [ ] Profils `EU`, `US`, `JP`, `WORLD` définis avec bandes précises
- [ ] `main(["--install", "--region", "US"])` injecte la configuration US
- [ ] `main(["--region", "INVALID"])` affiche une erreur claire en français et sort en code `1` ou `2`
- [ ] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Profils région-safe (EU/CE, US/FCC, JP/MIC, WORLD/déverrouillé) implémentés avec modélisation exacte des fréquences TX autorisées et exportation de configuration. CLI enrichie de `--region` avec avertissement légal explicite pour WORLD. 46/46 tests unitaires et d'intégration passants, Ruff 100% conforme.
- **Leçon d'aiguillage** : Conforme aux règles d'aiguillage d'AGENTS.md et au Pilier 6 du brief (« Responsable par défaut »).
