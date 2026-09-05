# Fiche de tâche — squelette du projet

## Titre

Poser le squelette Python du projet momentum-ultra.

## Agent assigné

**Gemini (Antigravity).** Tâche entièrement mécanique : l'arborescence, les noms et les signatures sont fixés ci-dessous. Toute erreur est rattrapée par `pytest` et `ruff` — c'est exactement le profil de tâche qui revient à Gemini.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

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

## Correction de contrat (post-revue, 2026-09-05)

La revue a établi que le contrat de cette fiche était inécrivable tel quel : il exigeait
« Fonction unique : `main` » tout en exigeant un test sur le résultat de l'analyse
d'arguments, que `main` seul n'expose pas. L'exécutant a tranché en ajoutant
`_build_parser()` au lieu de déclencher la condition d'arrêt « le contrat paraît
incohérent ».

Cette section ne réécrit pas le contrat exécuté : le verdict ci-dessous porte sur la
fiche telle qu'elle a été donnée. Elle fixe la formulation à reprendre.

- **`src/momentum_ultra/cli.py` — au lieu de « Fonction unique »** : « Une seule fonction
  *publique* : `def main(argv: list[str] | None = None) -> int:`. Les fonctions privées
  (préfixées `_`) sont autorisées si elles servent le contrat. »
- **Test du garde-fou — au lieu de « l'analyse de `[]` produit `dry_run is True` »** :
  « `main` rend le mode simulation observable de l'extérieur (message affiché ou valeur
  retournée), et le test le vérifie *à travers `main`*, jamais à travers le parser. »
  Motif : au niveau du parser, un futur `main` qui forcerait `dry_run = False` passerait
  les trois tests sans que rien ne le signale.

Report : à porter dans la fiche 02, la première qui touchera au corps de `main`.

## Suites à donner (non bloquantes)

- `cli.py:46` — `return int(exc.code) if isinstance(exc.code, int) else 0` : le repli sûr
  d'un code de sortie inconnu est `1`, pas `0`. Aucun chemin ne produit ce cas aujourd'hui.
- `cli.py:48` — `_ = args.dry_run` est du code mort qui ne sert qu'à éviter `F841`.
- `README.md:14` — `.venv\Scripts\activate` (cmd Windows) dans un bloc balisé ` ```bash `.
- Racine du dépôt — `tache-01-squelette-projet.md` et `FICHE-DE-TACHE.md` sont des
  doublons divergents de `taches/tache-01-squelette-projet.md` et `taches/_GABARIT.md`,
  résidus d'un paquet antérieur. À supprimer hors tâche.

## Journal de revue

Revue rendue par le sous-agent `reviseur` (contexte séparé, sans droit d'écriture), le
2026-09-05, sur la branche `tache/squelette-projet`. Les huit critères d'acceptation ont
été exécutés, non déduits.

```
Verdict : accepté
Motif : les 8 critères d'acceptation exécutés et passants ; périmètre conforme aux
        7 fichiers autorisés ; garde-fou --dry-run par défaut intact (cli.py:26).
        Réserves non bloquantes : contrat « fonction unique » non tenu (cli.py:11),
        mais contrat inécrivable tel quel ; repli d'erreur en 0 au lieu de 1
        (cli.py:46) ; code mort (cli.py:48) ; garde-fou testé au niveau du parser
        et non de main (test_cli.py:8). Revue faite sans git : diff réel,
        suppressions et historique non vérifiés.
Leçon d'aiguillage : bon agent. Tâche mécanique, contrat spécifié, erreurs
        rattrapables par pytest/ruff. La friction vient de la fiche, pas du
        partage : vérifier avant délégation que les critères d'acceptation sont
        satisfaisables sous le contrat écrit. Corriger la fiche 01 (autoriser
        les fonctions privées, ou exiger dry_run observable depuis main).
```

### Sorties vérifiées

| Critère | Sortie |
| --- | --- |
| `pip install -e ".[dev]"` | `Successfully installed ... momentum-ultra-0.1.0`, code 0 |
| `pytest` | `3 passed`, code 0 |
| `ruff check .` | `All checks passed!`, code 0 |
| `ruff format --check .` | `already formatted`, code 0 |
| `momentum-ultra --version` | `0.1.0`, code 0 |
| `momentum-ultra` (sans argument) | aide affichée, code 0 |
| Aucun `import serial` | aucune occurrence |
| Périmètre | 7 fichiers, tous autorisés |

### Réserve de méthode

La revue a tourné depuis une session distante, sans shell sur la machine de l'utilisateur.
`git diff --name-only main...HEAD` n'a donc pas pu être lancé : le périmètre est établi
sur l'inventaire des fichiers et leurs horodatages, pas sur un diff. Les fichiers
supprimés et l'historique des commits n'ont pas été vérifiés.
