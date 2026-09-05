# Fiche de tâche — Bundles autoinstall partageables

## Titre

Implémenter l'exportation, l'importation et l'installation de bundles autonomes et partageables (.tar.gz / json).

## Agent assigné

**Gemini (Antigravity).** Sérialisation/désérialisation d'archives, calcul de sommes de contrôle (checksums SHA256) et intégration CLI. 100% vérifiable par tests unitaires.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/bundles-partageables`

## Objectif

Conformément au Pilier 4 du brief (« Bundle partageable »), permettre à un utilisateur ou à la communauté de packager un ensemble complet (manifeste + applications `.fap` + assets + profil de réglages) dans une archive unique `.tar.gz`, et de l'installer directement sur n'importe quel Flipper Zero avec `momentum-ultra --install --bundle <fichier>`.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```text
src/momentum_ultra/bundle.py
src/momentum_ultra/cli.py
tests/test_bundle.py
tests/test_cli.py
taches/tache-07-bundles-partageables.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01` à `06`.
- Tout flashage de firmware.

## Contrat

### `src/momentum_ultra/bundle.py`

```python
from pathlib import Path
from momentum_ultra.manifest import PackManifest


class BundleError(Exception):
    """Base exception for bundle packaging and extraction errors."""


def export_bundle(manifest: PackManifest, destination: str | Path) -> Path:
    """Package a PackManifest and its embedded contents into a shareable .tar.gz archive."""


def import_bundle(bundle_path: str | Path) -> PackManifest:
    """Load, validate and unpack a PackManifest from a bundle archive."""
```

### `src/momentum_ultra/cli.py`

- Ajout de l'option `--export-bundle <chemin>` : exporte le pack par défaut vers une archive partageable.
- Ajout de l'option `--bundle <chemin>` : utilise le bundle spécifié au lieu du pack par défaut lors de `--install`.

## Critères d'acceptation

- [ ] `pytest` passe à 100% avec tests unitaires d'aller-retour (export -> import)
- [ ] `ruff check .` et `ruff format --check .` ne signalent rien
- [ ] `export_bundle` produit une archive valide avec manifeste `manifest.json` et données associées
- [ ] `import_bundle` reconstitue fidèlement le `PackManifest`
- [ ] `main(["--export-bundle", "test_bundle.tar.gz"])` génère le bundle et sort en code `0`
- [ ] `main(["--install", "--bundle", "test_bundle.tar.gz"])` installe le pack issu du bundle
- [ ] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Module `bundle.py` d'exportation et d'importation d'archives compressées `.tar.gz` et manifestes `.json` avec validation d'intégrité implémenté. Options CLI `--export-bundle` et `--bundle` opérationnelles et testées. 52/52 tests automatisés passants, Ruff 100% propre.
- **Leçon d'aiguillage** : Alignement complet avec le Pilier 4 du brief (« Bundle partageable »).
