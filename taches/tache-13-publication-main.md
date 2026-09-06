# Fiche de tâche — Publication complète sur main

## Titre

Publier l'intégralité du projet sur `main` sans force push.

## Agent assigné

**Opus (Claude Code).** Opération de gouvernance Git et de publication ; une erreur subtile de stratégie de merge n'est pas toujours rattrapée par des tests.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion/push.

## Branche

`tache/publish-main`

## Objectif

Rendre tous les dossiers/fichiers du projet visibles sur la branche `main` du dépôt GitHub, tout en conservant un historique propre et sans forcer l'écriture sur `main`.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```text
taches/tache-13-publication-main.md
README.md
```

## Hors périmètre

- Tout fichier de code sous `src/` et `tests/`.
- Toute modification des garde-fous matériels.
- Toute commande `push --force` sur `main`.

## Contrat

- Point de départ : branche locale créée depuis `origin/main`.
- Intégration : merge `--allow-unrelated-histories` depuis `tache/reprise-defauts-materiels`.
- Résolution de conflit : conserver le `README.md` complet du projet.
- Validation minimale : `python -m pytest` doit passer.
- Publication : push non destructif vers `origin main`.

## Critères d'acceptation

- [x] Une branche de publication basée sur `origin/main` existe (`tache/publish-main`).
- [x] Le merge de `tache/reprise-defauts-materiels` est réalisé sans force push.
- [x] Le conflit `README.md` est résolu et le fichier final est cohérent.
- [x] `python -m pytest` passe (119 tests).
- [ ] Le push vers `origin main` est réussi sans `--force`.

## Conditions d'arrêt

- Le push vers `main` est refusé par une protection de branche.
- Une modification hors périmètre devient nécessaire.
- Un garde-fou matériel devrait être modifié.

## Journal de revue

- **Verdict** : rejeté
- **Motif** : le sous-agent `reviseur` n'a pas pu exécuter `git diff`/`git status`/`pytest` dans son contexte, donc il n'a pas pu valider le périmètre et les critères par exécution réelle ; push direct vers `main` non autorisé.
- **Leçon d'aiguillage** : la tâche est bien du ressort d'Opus (gouvernance Git), mais la publication doit passer par une revue validée.
