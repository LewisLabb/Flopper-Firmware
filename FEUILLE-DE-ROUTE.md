# Feuille de route — flopper

Source : *Flopper — brief de conception & feuille de route*, septembre 2026. Ce fichier est la version exécutable du brief : c'est lui qui décide de l'ordre des fiches de tâche. Le brief reste le document de vision ; en cas de désaccord entre les deux, c'est ce fichier qui tranche, et le brief qu'on corrige.

## Promesse

Pas « la dernière mise à jour dont ton Flipper aura besoin » — aucun firmware n'est jamais fini. La promesse tenable : **le daily-driver définitif, la version qui se sent enfin terminée.** Pas « plus rien après », mais « plus rien d'essentiel qui manque ».

On construit sur Momentum. On ne gagne pas sur la quantité de fonctions — elles y sont déjà presque toutes — mais sur l'évidence, le confort et la confiance.

## Les six piliers

| # | Pilier | Ce qu'il change |
| --- | --- | --- |
| 1 | Onboarding et autoinstall | De « boîte » à « prêt à jouer » sans jamais ouvrir un dossier SD |
| 2 | UI cohérente et amicale | Le débutant comprend l'écran d'accueil en trois secondes |
| 3 | Refonte de la saisie | Le point noir n°1 de la plateforme, et le candidat le plus viral |
| 4 | Store d'apps embarqué + OTA Wi-Fi | Installer et mettre à jour sans PC, compatibilité vérifiée avant install |
| 5 | Gestionnaire de modules unifié | La carte externe se présente toute seule au lieu du rituel de configuration |
| 6 | Responsable par défaut | Le vrai facteur de différenciation — voir les garde-fous réglementaires d'`AGENTS.md` |

Transversal : **discipline de perf et de stabilité.** Matériel figé, donc chaque milliseconde et chaque Ko comptent. C'est ce qui distingue d'une surenchère de fonctions bancales.

## Ordre des chantiers

P0 = gains rapides à fort impact et faible coût, livrés en premier. P1 = les piliers phares. P2–P3 = valeur additionnelle et exploration.

| Chantier | Pilier | Impact | Effort | Priorité | Fiche |
| --- | --- | --- | --- | --- | --- |
| Thème par défaut soigné + control center | 2 | Élevé | Faible | P0 | — |
| Premier-démarrage guidé | 1 | Élevé | Faible-moyen | P0 | **02** |
| Profils région-safe + étiquetage clair | 6 | Élevé | Faible-moyen | P0 | — |
| Revoir médias / captures sur l'appareil | 2 | Moyen | Faible | P1 | — |
| Clavier prédictif + pré-saisies | 3 | Très élevé | Moyen | P1 · phare | — |
| Passerelle clavier BLE + saisie QR | 3 | Élevé | Moyen | P1 | — |
| Store d'apps OTA (Wi-Fi, sans PC) | 4 | Très élevé | Moyen-élevé | P1 · phare | — |
| Gestionnaire de modules auto-détecté | 5 | Élevé | Moyen | P1 | — |
| Bundle autoinstall partageable | 1 | Élevé | Moyen | P1 | — |
| Discipline de perf et de stabilité | — | Élevé | Continu | Continu | — |
| Sync réglages / captures (compagnon) | 4 | Moyen | Moyen | P2 | — |
| Automations no-code (« recettes ») | — | Moyen | Élevé | P2 | — |
| Exploration Thread / Matter | — | Moyen | Élevé | P3 | — |

## Objectifs chiffrés retenus

- **Saisie** : diviser par ~3 le nombre de clics pour saisir un SSID (pilier 3).
- **Onboarding** : de la boîte à l'appareil utilisable en deux minutes (pilier 1).
- **Écran d'accueil** : compris en trois secondes par un débutant (pilier 2).

Un objectif chiffré sans moyen de mesure n'est qu'un slogan : chaque fiche qui prétend servir l'un d'eux dit comment il sera mesuré.

## Deux réserves à lever

Consignées ici pour ne pas être redécouvertes plus tard.

1. **Lignée de Momentum.** Le brief décrit Momentum comme étant « base Unleashed » ; le site officiel du projet le présente comme un fork du firmware officiel. La différence est sans conséquence sur la feuille de route, mais elle compte pour le crédit et pour la compatibilité amont. À vérifier avant toute communication publique.
2. **Le pilier 1 déborde du dépôt.** Le brief décrit « un flux unique qui flashe le firmware ». Ce dépôt produit du firmware et n'écrit pas de flasheur (voir `AGENTS.md`). La part réalisable ici est le premier-démarrage guidé, le profil de départ et le bundle partageable ; le flashage lui-même reste délégué au Web Updater et à qFlipper. Si le flux « un seul lien, un seul clic » reste un objectif produit, il demandera un outil compagnon séparé — décision non prise.
