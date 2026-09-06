# flopper

Outil qui prépare un Flipper Zero fraîchement flashé en Momentum : installation d'un pack d'apps curé, d'un asset pack, d'un profil de réglages, et d'un premier démarrage guidé.

## Ce que ce projet n'est pas

**Ce projet ne flashe pas de firmware.** Momentum fournit déjà son Web Updater pour ça. Toute proposition de réimplémenter le flashage doit être refusée : c'est hors périmètre, et c'est l'opération la plus risquée pour le matériel.

## Stack

Python 3.11+ · pyserial (communication USB) · pytest (tests) · ruff (lint et format)

Aucune dépendance supplémentaire sans justification écrite dans la fiche de tâche.

## Commandes

```bash
python -m venv .venv          # créer l'environnement
.venv\Scripts\activate        # l'activer (Windows)
pip install -e ".[dev]"       # installer le projet et ses outils
pytest                        # lancer les tests
ruff check . && ruff format . # lint et formatage
```

## Conventions

- Toute fonction publique est typée et documentée en une ligne.
- Un fichier dépasse 300 lignes → le découper.
- Les tests ne touchent jamais à un vrai Flipper : la couche série est simulée.
- Les messages destinés à l'utilisateur final sont en français.
- Le code, les noms de variables et les commentaires sont en anglais.

## Garde-fous matériels

Le Flipper est un appareil physique : une écriture ratée coûte cher à l'utilisateur.

- **Un seul outil à la fois peut communiquer avec le Flipper.** Vérifier que qFlipper, Flipper Lab et le Web Updater sont fermés avant toute connexion série, et le signaler clairement sinon.
- **Ne jamais écrire sur un appareil connecté sans confirmation explicite de l'utilisateur.**
- **Ne jamais supprimer de fichier sur la carte SD.** Déplacer vers un dossier de sauvegarde, jamais effacer.
- Toute opération d'écriture doit proposer un mode simulation (`--dry-run`) et l'utiliser par défaut dans les tests.
- Ne jamais désactiver un garde-fou pour faire passer un test.

## Git

- Une branche par tâche : `tache/description-courte`.
- Commits à l'impératif, une idée par commit.
- Ne jamais fusionner sans la revue décrite ci-dessous.
- Ne jamais forcer un push sur `main`.

## Répartition du travail

Deux agents, un seul dépôt. Le critère d'aiguillage est unique : **si le résultat est subtilement faux, un test le rattraperait-il ?**

- **Oui → Gemini (Antigravity).** Volume mécanique et vérifiable : échafaudage de tests, documentation, refactorisations répétitives, traitement de fichiers, code répétitif. Son grand contexte est fait pour le large et peu profond.
- **Non → Opus (Claude Code).** Jugement : architecture, contrats d'interface, toute écriture sur l'appareil, gestion d'erreurs matérielles, sécurité.

**La revue est toujours faite par Opus, jamais par l'agent qui a exécuté.** Elle passe par le sous-agent `reviseur` de Claude Code (`.claude/agents/reviseur.md`), qui tourne dans son propre contexte, sans droit d'écriture : il constate, il ne corrige pas. Aucune fusion sans son verdict — y compris pour le code produit par Gemini. C'est là que la revue croisée prend tout son mordant : le relecteur n'est pas le même modèle que l'auteur.

Chaque agent lit ce fichier, mais ne lit pas les fichiers de configuration de l'autre. Ne pas recopier de règles dans un `GEMINI.md` : tout ce qui est commun vit ici, dans `AGENTS.md`.

## Arrête-toi et demande si

- La tâche exige de modifier un garde-fou matériel.
- La tâche sort du périmètre décrit dans la fiche.
- Il faut ajouter une dépendance non listée.
- Il faut toucher à plus de fichiers que la fiche n'en autorise.
- Quelque chose dans la fiche est ambigu. Une question coûte moins cher qu'une reprise.
