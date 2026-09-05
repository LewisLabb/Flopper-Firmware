# Fiche de tâche — squelette du projet

## Titre

Poser le squelette Python du projet momentum-ultra.

## Agent assigné

**Claude Code**, en attendant Antigravity. Tâche entièrement mécanique : l'arborescence, les noms et les signatures sont fixés ci-dessous. Toute erreur est rattrapée par `pytest` et `ruff`.

Revue obligatoire par le sous-agent `reviseur` avant fusion.

## Branche

`tache/squelette-projet`

## Objectif

Le dépôt est vide. Il faut la structure de base d'un projet Python installable et testable, pour que toutes les tâches suivantes aient un socle. Aucune fonctionnalité métier dans cette tâche : ni communication série, ni lecture de carte SD, ni installation de quoi que ce soit.

## Périmètre

Fichiers à créer, et eux seuls :

```
.gitignore
README.md
pyproject.toml
src/momentum_ultra/__init__.py
src/momentum_ultra/cli.py
tests/test_cli.py
taches/.gitkeep
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `FICHE-DE-TACHE.md` — déjà en place, ne pas modifier.
- Tout fichier non listé dans le périmètre.
- Toute utilisation de `pyserial`. La dépendance est déclarée, mais aucun code ne l'importe dans cette tâche.

## Contrat

**`pyproject.toml`**
- Nom du paquet : `momentum-ultra` · version `0.1.0` · Python `>=3.11`
- Build backend : `setuptools`, disposition `src/`
- Dépendance : `pyserial`
- Groupe optionnel `dev` : `pytest`, `ruff`
- Script console : `momentum-ultra = "momentum_ultra.cli:main"`

**`src/momentum_ultra/__init__.py`**
- Expose `__version__: str = "0.1.0"`

**`src/momentum_ultra/cli.py`**
- Fonction unique : `def main(argv: list[str] | None = None) -> int:`
- Utilise `argparse`. Deux options seulement :
  - `--version` — affiche la version, retourne `0`
  - `--dry-run / --no-dry-run` — **`--dry-run` est actif par défaut**, conformément aux garde-fous matériels d'`AGENTS.md`
- Sans argument : affiche l'aide et retourne `0`
- Ne lève jamais d'exception vers l'appelant : retourne un code de sortie
- Les messages affichés sont en français

**`tests/test_cli.py`** — au minimum ces trois tests :
- `main(["--version"])` retourne `0`
- `main([])` retourne `0`
- l'analyse de `[]` produit `dry_run is True`, et `["--no-dry-run"]` produit `dry_run is False`

**`.gitignore`** — au minimum : `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `dist/`, `build/`

**`README.md`** — court : ce que fait le projet (préparer un Flipper déjà flashé), ce qu'il ne fait pas (flasher le firmware), et les commandes d'installation et de test.

## Critères d'acceptation

- [ ] `pip install -e ".[dev]"` réussit
- [ ] `pytest` passe, avec au moins les trois tests listés
- [ ] `ruff check .` ne signale rien
- [ ] `ruff format --check .` ne signale rien
- [ ] `momentum-ultra --version` affiche `0.1.0`
- [ ] `momentum-ultra` sans argument affiche l'aide et sort en code `0`
- [ ] Aucun fichier hors périmètre créé ou modifié
- [ ] Aucun `import serial` nulle part

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent ou incomplet

## Journal de revue

Rempli par Opus après exécution.

- **Verdict** :
- **Motif** :
- **Leçon d'aiguillage** :
