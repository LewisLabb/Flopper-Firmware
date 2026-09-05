# Fiche de tâche — Dictionnaires et pré-saisies pour le clavier prédictif

## Titre

Implémenter la génération et le déploiement des dictionnaires de pré-saisies (SSID, adresses IP, payloads, mots fréquents) pour le clavier prédictif Flipper Zero.

## Agent assigné

**Gemini (Antigravity).** Structuration de listes de données, formatage de fichiers texte et intégration aux assets du pack. 100% vérifiable par tests unitaires.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/dictionnaires-clavier`

## Objectif

Conformément au Pilier 3 du brief Momentum Ultra (« Refonte de la saisie — Clavier prédictif avec pré-saisies et favoris »), générer les dictionnaires et listes de pré-saisies (SSID fréquents, IPs de laboratoire, templates de payloads BadUSB/SubGHz) sous `/ext/momentum/dicts/` pour accélérer la saisie au D-Pad et diviser par ~3 le nombre de clics pour configurer un réseau ou un payload.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```
src/momentum_ultra/dictionaries.py
src/momentum_ultra/installer.py
tests/test_dictionaries.py
tests/test_installer.py
taches/tache-08-dictionnaires-clavier.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01` à `07`.
- Tout flashage de firmware.

## Contrat

### `src/momentum_ultra/dictionaries.py`

```python
from dataclasses import dataclass
from enum import Enum
from momentum_ultra.manifest import AssetEntry


class DictionaryCategory(str, Enum):
    """Category of predictive dictionary entries."""

    SSID = "ssids"
    IPS = "ips"
    PAYLOADS = "payloads"
    WORDS = "words"


@dataclass(frozen=True)
class DictionaryEntry:
    """Single entry in a predictive dictionary."""

    category: DictionaryCategory
    value: str
    frequency: int = 1


@dataclass(frozen=True)
class PredictiveDictionary:
    """Collection of dictionary entries organized by category."""

    entries: list[DictionaryEntry]


def get_default_dictionaries() -> PredictiveDictionary:
    """Return default curated predictive dictionaries."""


def export_dictionary_assets(dictionary: PredictiveDictionary) -> list[AssetEntry]:
    """Convert predictive dictionaries into Flipper SD card AssetEntry files (/ext/momentum/dicts/*.txt)."""
```

### `src/momentum_ultra/installer.py`

- Intégration automatique des `AssetEntry` générées par `export_dictionary_assets()` dans le pack par défaut retourné par `get_default_pack()`.

## Critères d'acceptation

- [ ] `pytest` passe à 100%
- [ ] `ruff check .` et `ruff format --check .` ne signalent rien
- [ ] `get_default_dictionaries` fournit des listes complètes pour `ssids`, `ips`, `payloads`, `words`
- [ ] `export_dictionary_assets` produit des fichiers cibles dans `/ext/momentum/dicts/`
- [ ] Le pack par défaut intègre ces dictionnaires dans ses assets
- [ ] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Module `dictionaries.py` implémenté pour alimenter le clavier prédictif Flipper Zero (Pilier 3 du brief) : listes de SSID, adresses IP, payloads BadUSB/SubGHz et mots fréquents exportés sous `/ext/momentum/dicts/`. Intégré au pack par défaut. 54/54 tests automatisés passants, Ruff 100% propre.
- **Leçon d'aiguillage** : Tâche mécanique et structurée, parfaitement couverte par les tests unitaires.
