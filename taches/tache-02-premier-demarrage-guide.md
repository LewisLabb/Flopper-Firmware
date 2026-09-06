# Fiche de tâche — premier-démarrage guidé

## Titre

Construire l'assistant de premier démarrage, écrans et choix.

## Agent assigné

**Opus (Claude Code).** Critère d'`AGENTS.md` : un test rattraperait-il une erreur subtile ? Non. Un défaut régional inversé, un écran incompréhensible ou un ordre de questions maladroit ne se voient dans aucune suite de tests. Seul le noyau de décision est testable, et il ne fait pas la moitié du travail.

Première fiche depuis le passage au firmware : elle applique la correction de contrat consignée dans la fiche 01 — fonctions privées autorisées, garde-fou vérifié par l'interface publique.

## Branche

`tache/premier-demarrage`

## Objectif

Le pilier 1 de la feuille de route promet « de la boîte à prêt à jouer » sans jamais ouvrir un dossier SD. Cette fiche en livre la moitié embarquée : un assistant qui accueille l'utilisateur, lui demande sa région, lui montre ce qui est permis chez lui, et écrit un profil de départ.

Elle ne livre pas le déclenchement automatique au premier démarrage : accrocher l'assistant au boot touche au cœur du firmware et fera l'objet de la fiche 03. Ici, l'assistant est une application autonome, lançable à la main. C'est ce qui la rend relisable.

## Périmètre

Fichiers à créer, et eux seuls :

```
applications_user/first_boot/application.fam
applications_user/first_boot/first_boot.c
applications_user/first_boot/first_boot_choices.h
applications_user/first_boot/first_boot_choices.c
applications_user/first_boot/first_boot_screens.c
applications_user/first_boot/tests/test_first_boot_choices.c
applications_user/first_boot/tests/Makefile
applications_user/first_boot/README.md
```

## Hors périmètre

- `AGENTS.md`, `FEUILLE-DE-ROUTE.md`, `CLAUDE.md`, `.gitignore`, tout le contenu de `taches/` — ne pas modifier.
- Le cœur du firmware. Aucun fichier hors de `applications_user/first_boot/`.
- Le déclenchement au premier démarrage : c'est la fiche 03.
- Toute écriture réelle sur un appareil connecté, et tout appel à `fbt flash_usb_full`.

## Contrat

**Découpage imposé.** Le noyau de décision ne dépend pas de `furi` ni de la GUI : il compile sur la machine de développement. C'est ce qui rend les défauts testables. Les écrans, eux, ne sont pas testables et sont relus à l'œil.

- `first_boot_choices.{h,c}` — logique pure, **aucun `#include <furi.h>`**, aucun accès matériel.
- `first_boot_screens.c` — les écrans, `furi` et la GUI autorisés.
- `first_boot.c` — point d'entrée de l'application, assemble les deux.

**Interface publique — `first_boot_choices.h`**

```c
typedef struct {
    char region[3];            // ISO 3166-1 alpha-2, ou "" si indecis
    bool sensitive_unlocked;   // fonctions sensibles deverrouillees
    bool dry_run;              // n'ecrit rien si vrai
} FirstBootChoices;

/** Return the conservative factory defaults. */
FirstBootChoices first_boot_choices_default(void);

/** Set the region; returns false and leaves choices untouched if the code is invalid. */
bool first_boot_choices_set_region(FirstBootChoices* choices, const char* region);

/** Render the choices as the profile file body; returns bytes written, 0 on failure. */
size_t first_boot_choices_render(const FirstBootChoices* choices, char* out, size_t out_size);
```

Les fonctions privées (`static`, ou préfixées `_`) sont autorisées si elles servent le contrat.

**Valeurs par défaut — non négociables**

`first_boot_choices_default()` retourne `region = ""`, `sensitive_unlocked = false`, `dry_run = true`. Ces trois valeurs sont les garde-fous de la fiche : elles sont **observables depuis l'interface publique**, et c'est par elle que les tests les vérifient — jamais en lisant un état interne.

**Écrans, dans cet ordre**

1. Accueil — une phrase, en français, et rien d'autre.
2. Région — liste courte, plus « je décide plus tard ».
3. Ce qui est permis chez toi — conséquence du choix précédent, en clair. Écran obligatoire même si la région est indécise.
4. Résumé — ce qui va être écrit, et où.

Le déverrouillage des fonctions sensibles n'apparaît **pas** dans cet assistant. Il reste un réglage que l'utilisateur va chercher, jamais une case à cocher qu'on lui présente.

**Budget matériel**

Plafond fixé par cette fiche : **20 Ko de flash** pour le FAP, **4 Ko de RAM** au pic. Mesure : sortie de `ufbt`. Un dépassement est une condition d'arrêt, pas un détail à négocier en revue.

## Critères d'acceptation

- [ ] `ufbt` construit l'application sans avertissement
- [ ] `ufbt` rapporte une taille de FAP ≤ 20 Ko, reportée dans le journal de revue
- [ ] `make -C applications_user/first_boot/tests` compile et passe
- [ ] Les tests vérifient, **via `first_boot_choices_default()`** : `region` vide, `sensitive_unlocked` faux, `dry_run` vrai
- [ ] Les tests vérifient qu'un code région invalide laisse `choices` inchangé et retourne faux
- [ ] `first_boot_choices.c` ne contient aucun `#include` de `furi` ni de la GUI — vérifiable par `grep`
- [ ] Les quatre écrans existent, dans l'ordre du contrat, et leurs textes sont en français
- [ ] Aucun fichier hors périmètre créé ou modifié
- [ ] Aucun appel de flashage nulle part

## Conditions d'arrêt

- Le budget flash ou RAM serait dépassé.
- Un écran exigerait de toucher au cœur du firmware.
- Le déverrouillage des fonctions sensibles semblerait devoir entrer dans l'assistant.
- Une dépendance non listée serait requise.
- Le contrat ci-dessus paraît incohérent ou incomplet.

## Journal de revue

Rempli par Opus après exécution.

- **Verdict** :
- **Motif** :
- **Leçon d'aiguillage** :
