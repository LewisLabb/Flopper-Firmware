# flopper

Firmware Flipper Zero, fork de [Momentum](https://github.com/Next-Flip/Momentum-Firmware). Objectif : le daily-driver définitif — non pas une centième fonction, mais l'évidence, le confort et la confiance sur tout ce que l'appareil sait déjà faire.

La vision produit et l'ordre des chantiers vivent dans `FEUILLE-DE-ROUTE.md`. Ce fichier-ci ne décrit que les règles de travail.

## Ce que ce projet n'est pas

**Ce projet ne réimplémente pas de flasheur.** Il *produit* du firmware ; l'installer sur un appareil reste le travail d'outils qui existent déjà et qui sont éprouvés : le Web Updater de Momentum, qFlipper, ou `./fbt flash_usb_full` en développement. Toute proposition d'écrire notre propre chaîne de flashage doit être refusée : c'est l'opération la plus risquée pour le matériel, et elle est déjà résolue ailleurs.

**Ce projet ne réinvente pas la radio.** Momentum possède déjà presque toutes les fonctions. On ne gagne pas sur la quantité.

## Stack

C11 · `fbt` (arbre firmware) · `ufbt` (applications autonomes, FAP) · Python 3.11+ pour l'outillage de build · cible STM32WB55, figée

Aucune dépendance supplémentaire sans justification écrite dans la fiche de tâche.

## Commandes

```
./fbt                          # construire le firmware
./fbt flash_usb_full           # flasher l'appareil connecte (action humaine, jamais automatisee)
./fbt lint          format     # verifier / appliquer le style C
ufbt                           # construire une application autonome
ufbt launch                    # la construire et la lancer sur l'appareil connecte
```

## Contrainte matérielle

Le STM32WB55 est figé : ni plus de flash, ni plus de RAM, ni plus de CPU n'arriveront. **La seule marge de progrès est l'efficacité du firmware.** On gagne en raffinant, pas en empilant.

Conséquence opérationnelle : toute fiche de tâche qui ajoute une fonction annonce son coût attendu en flash et en RAM, et la revue le vérifie. Une fonction qui ne tient pas dans le budget n'est pas une fonction, c'est une régression.

## Conventions

- Le code, les noms de symboles et les commentaires sont en anglais. Les chaînes affichées à l'utilisateur sont en français.
- Toute fonction publique est documentée en une ligne.
- Un fichier dépasse 300 lignes → le découper.
- Pas d'allocation dynamique dans une boucle de rendu ni dans un gestionnaire d'interruption.
- Rien de bloquant dans le fil d'exécution de l'interface : la GUI doit rester réactive.
- Les tests ne touchent jamais à un vrai Flipper : la couche matérielle est simulée.

## Garde-fous matériels

Le Flipper est un appareil physique : une écriture ratée coûte cher à l'utilisateur. Ces règles ont survécu au changement de nature du projet, et elles se durcissent plutôt qu'elles ne s'assouplissent.

- **Flasher est une action humaine.** Aucun agent ne lance `flash_usb_full` ni n'écrit sur un appareil connecté de sa propre initiative. Un agent prépare, il ne pose pas le doigt sur le bouton.
- **Un seul outil à la fois peut communiquer avec le Flipper.** Vérifier que qFlipper, Flipper Lab et le Web Updater sont fermés avant toute connexion série, et le signaler clairement sinon.
- **Ne jamais supprimer de fichier sur la carte SD.** Déplacer vers un dossier de sauvegarde, jamais effacer.
- Toute opération d'écriture propose un mode simulation (`--dry-run` ou son équivalent) et l'utilise par défaut dans les tests.
- Ne jamais désactiver un garde-fou pour faire passer un test.

## Garde-fous réglementaires

Le pilier « responsable par défaut » de la feuille de route n'est pas de la morale, c'est du produit.

- Les fonctions sensibles sont étiquetées clairement dans l'interface.
- Les profils régionaux sont conservateurs par défaut ; déverrouiller reste un réglage explicite de l'utilisateur, jamais une valeur d'usine.
- L'utilisateur demeure responsable de la loi locale, et l'interface le dit avant l'acte, pas dans un fichier de licence.
- Aucun agent n'inverse un défaut régional pour faire passer un test ou simplifier un écran.

## Git

- Une branche par tâche : `tache/description-courte`.
- Commits à l'impératif, une idée par commit.
- Ne jamais fusionner sans la revue décrite ci-dessous.
- Ne jamais forcer un push sur `main`.

## Répartition du travail

Deux agents, un seul dépôt. Le critère d'aiguillage reste : **si le résultat est subtilement faux, un test le rattraperait-il ?**

- **Oui → Gemini (Antigravity).** Volume mécanique et vérifiable : tables de chaînes et de traductions, pipelines d'assets et de thèmes, documentation, refactorisations répétitives, scripts de build, échafaudage de tests.
- **Non → Opus (Claude Code).** Jugement : architecture, contrats d'interface, toute écriture sur l'appareil, gestion d'erreurs matérielles, budget flash/RAM, ergonomie, garde-fous réglementaires.

**Attention : le passage au firmware déplace l'équilibre.** Sur un outil Python, `pytest` rattrapait presque tout et la majorité du travail revenait à Gemini. Sur du C embarqué, sans matériel dans l'intégration continue, la réponse « oui » devient rare : une régression d'interface, un dépassement de RAM ou un défaut régional inversé ne se voient pas dans une suite de tests. Attendre que la part d'Opus augmente nettement. Une fiche qui prétend qu'un test rattrapera une erreur d'ergonomie ou de budget mémoire se trompe.

**La revue est toujours faite par Opus, jamais par l'agent qui a exécuté.** Elle passe par le sous-agent `reviseur` (`.claude/agents/reviseur.md`), qui tourne dans son propre contexte, sans droit d'écriture : il constate, il ne corrige pas. Aucune fusion sans son verdict — y compris pour le code produit par Gemini.

Chaque agent lit ce fichier, mais ne lit pas les fichiers de configuration de l'autre. Ne pas recopier de règles dans un `GEMINI.md` : tout ce qui est commun vit ici.

## Arrête-toi et demande si

- La tâche exige de flasher un appareil, ou d'écrire dessus sans confirmation humaine.
- La tâche exige de modifier un garde-fou matériel ou réglementaire.
- La tâche sort du périmètre décrit dans la fiche.
- Il faut ajouter une dépendance non listée.
- Le budget flash ou RAM annoncé dans la fiche serait dépassé.
- Quelque chose dans la fiche est ambigu. Une question coûte moins cher qu'une reprise.

## Historique

Ce dépôt a d'abord été un outil PC de préparation post-flash, en Python. La tâche 01 (squelette Python) a été exécutée et acceptée en revue sous cette gouvernance-là ; sa fiche et son journal de revue sont conservés dans `taches/` comme archive de méthode. Le code Python correspondant est retiré de `main` et conservé sous l'étiquette `archive/outil-python`.
