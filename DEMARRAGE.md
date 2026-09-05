# À faire, dans l'ordre

Ce paquet contient la base de gouvernance du projet, déjà rangée. Tu n'as rien à déplacer.

## 1. Décompresser

Décompresse ce paquet **à la racine de ton dossier `momentum-ultra`** (celui qui est lié à ton dépôt GitHub, sur ton `C:`).

Après décompression, ton dossier doit contenir :

```text
momentum-ultra/
├── AGENTS.md                 ← règles communes aux deux agents
├── CLAUDE.md                 ← renvoi vers AGENTS.md pour Claude Code
├── DEMARRAGE.md              ← ce fichier
├── .claude/
│   └── agents/
│       └── reviseur.md       ← le relecteur (Claude Code / Opus)
└── taches/
    ├── _GABARIT.md           ← modèle de fiche réutilisable
    └── tache-01-squelette-projet.md
```

> Sur Windows, les dossiers commençant par un point (`.claude`) sont parfois masqués par l'explorateur, mais ils existent bien. Ne t'inquiète pas s'il semble absent : Claude Code le trouvera.

## 2. Premier commit

Dans un terminal ouvert sur le dossier :

```bash
git add .
git commit -m "Base de gouvernance : AGENTS.md, reviseur, premiere fiche"
git push
```

## 3. Exécuter la première tâche (Gemini / Antigravity)

Ouvre Antigravity sur le dossier `momentum-ultra`. Crée la branche `tache/squelette-projet`. Puis donne à l'agent, mot pour mot :

> Lis `AGENTS.md`, puis exécute `taches/tache-01-squelette-projet.md`.

Laisse-le travailler. Il doit créer le squelette Python décrit dans la fiche, rien de plus.

## 4. Faire relire (Opus / Claude Code)

Ouvre Claude Code sur le **même dossier, la même branche**. Donne-lui, mot pour mot :

> Utilise le sous-agent `reviseur` sur la tâche 01.

Le réviseur va lancer les tests lui-même et rendre un verdict : accepté ou rejeté, avec les motifs.

## 5. Décider

- **Verdict accepté** → fusionne la branche dans `main`, et passe à la fiche suivante (dis-le-moi, je la prépare).
- **Verdict rejeté** → renvoie les motifs à Gemini pour correction, puis refais relire. On ne fusionne jamais un rejet.

Dans les deux cas, recopie le verdict dans la section « Journal de revue » au bas de la fiche 01. C'est ce qui nous servira à ajuster la répartition des tâches par la suite.

## Ce qu'il ne faut pas faire

- Ne saute pas l'étape 4, même si le résultat de Gemini a l'air parfait. La relecture indépendante est tout l'intérêt du montage.
- Ne laisse pas un agent écrire directement sur `main`.
- Ne crée pas de fichier `GEMINI.md` pour l'instant : il prendrait le dessus sur `AGENTS.md` dans Antigravity et créerait deux sources de règles divergentes.

## Un détail volontaire

La fiche 01 contient une exigence de sécurité facile à inverser par distraction (le mode simulation actif par défaut). Si le réviseur la relève, c'est bon signe : ta chaîne de contrôle fonctionne. Si personne ne la relève, c'est un signal à me rapporter.
