# Fiche de tâche — Pipeline d'installation et intégration CLI

## Titre

Implémenter le moteur d'exécution du plan d'installation et l'assistant de préparation guidée dans la CLI.

## Agent assigné

**Gemini (Antigravity).** Assemblage des composants précédents (`device`, `flipper_client`, `manifest`), orchestration séquentielle et affichage utilisateur. Entièrement vérifiable par tests unitaires et d'intégration simulés.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/pipeline-installation`

## Objectif

Connecter ensemble la détection du Flipper, le chargement du pack par défaut, la confirmation explicite de l'utilisateur et l'exécution sécurisée du plan d'installation avec suivi de progression et conseils de premier démarrage en français.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```
src/momentum_ultra/installer.py
src/momentum_ultra/cli.py
tests/test_installer.py
tests/test_cli.py
taches/tache-05-pipeline-installation.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01-squelette-projet.md`, `taches/tache-02-detection-port.md`, `taches/tache-03-client-serie-flipper.md`, `taches/tache-04-gestion-manifestes.md`.
- Tout flashage de firmware.
- Toute communication avec un port série physique pendant les tests.

## Contrat

### `src/momentum_ultra/installer.py`

```python
from collections.abc import Callable
from momentum_ultra.flipper_client import FlipperClient
from momentum_ultra.manifest import PlanAction, PackManifest


def get_default_pack() -> PackManifest:
    """Return the built-in curated Momentum Ultra pack."""


def execute_install_plan(
    client: FlipperClient,
    plan: list[PlanAction],
    on_progress: Callable[[PlanAction, int, int], None] | None = None,
) -> list[str]:
    """Execute each action in the installation plan on the Flipper Zero."""
```

### `src/momentum_ultra/cli.py`

- Commande `momentum-ultra` :
  - Support de `--install` (ou `--prepare`)
  - Support de `--yes` pour confirmation non-interactive
  - Si `--install` est activé :
    1. Détecte le Flipper Zero (`find_flipper`).
    2. Vérifie la disponibilité du port (`is_port_available`).
    3. Si `dry_run=False` et non `--yes`, demande confirmation explicite : `"Voulez-vous lancer l'installation sur le Flipper Zero connecté ? (o/N)"`.
    4. Exécute le plan avec affichage de la progression.
    5. Affiche le récapitulatif et les instructions de premier démarrage en français.

## Critères d'acceptation

- [ ] `pytest` passe à 100% avec tests unitaires et intégration
- [ ] `ruff check .` ne signale rien
- [ ] `ruff format --check .` ne signale rien
- [ ] `main(["--install"])` exécute la préparation en mode simulation (`dry-run`) par défaut
- [ ] `main(["--install", "--no-dry-run"])` demande une confirmation explicite avant d'écrire
- [ ] L'exécution du plan affiche la progression en français
- [ ] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Pipeline d'installation complet implémenté avec exécution séquentielle, pack par défaut curé, confirmation interactive obligatoire en cas d'écriture réelle (`--no-dry-run`), mode simulation (`--dry-run`) par défaut, et guide de premier démarrage affiché en français. 39/39 tests automatisés passants, Ruff 100% propre.
- **Leçon d'aiguillage** : L'assemblage des couches modulaires a permis de tester de bout en bout l'application sans jamais nécessiter de matériel réel.
