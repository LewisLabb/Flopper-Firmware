# Fiche de tâche — gabarit

Gabarit de passation. Opus le remplit avant toute délégation. Une fiche vague produit un travail vague : le temps passé ici est le vrai travail d'orchestration.

Copier ce fichier dans `taches/` sous le nom de la branche, puis le remplir.

---

## Titre

Une phrase à l'impératif. Exemple : « Ajouter la lecture du manifeste de pack d'apps ».

## Agent assigné

Gemini (Antigravity) ou Opus (Claude Code).

Justifier en une ligne selon le critère d'`AGENTS.md` : un test rattraperait-il une erreur subtile ?

## Branche

`tache/nom-court`

## Objectif

Deux ou trois phrases. Ce que la tâche accomplit, et pourquoi elle existe. Pas de solution ici — seulement le besoin.

## Périmètre

Liste explicite des fichiers que l'agent peut créer ou modifier.

## Hors périmètre

Liste explicite des fichiers à ne pas toucher. Toujours remplir cette section, même si elle paraît évidente. C'est la protection principale contre la dérive.

## Contrat

Les signatures, formats de données et interfaces à respecter, écrits noir sur blanc. Si la tâche consomme ou produit une structure de données, la donner en exemple.

Cette section est ce qui permet à deux agents de travailler sans se contredire.

**Avant de déléguer, relire le contrat et les critères d'acceptation ensemble : chaque
critère doit être satisfaisable sous le contrat tel qu'il est écrit.** Un contrat qui
interdit ce qu'un critère exige force l'agent à trancher seul — et il tranchera, au lieu
de s'arrêter. Vérifier en particulier qu'un critère portant sur un état interne dispose
d'un moyen public de l'observer.

## Critères d'acceptation

Conditions vérifiables, pas des intentions. Chacune doit pouvoir se répondre par oui ou non.

- [ ] `pytest` passe
- [ ] `ruff check .` ne signale rien
- [ ] …

Un critère qui vérifie un garde-fou doit le vérifier **par l'interface publique**, jamais
par un rouage interne : tester le parser plutôt que la commande laisse passer un garde-fou
désactivé plus loin dans la chaîne.

## Conditions d'arrêt

Ce qui doit interrompre l'agent et déclencher une question plutôt qu'une décision autonome.

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

Rempli par Opus après exécution. C'est cette section qui fait progresser la méthode.

- **Verdict** : accepté / rejeté
- **Motif** : si rejeté, ce qui a manqué
- **Leçon d'aiguillage** : la tâche était-elle chez le bon agent ? Si non, corriger la règle dans `AGENTS.md`.
