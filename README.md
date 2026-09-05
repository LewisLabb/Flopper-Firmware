# momentum-ultra

Outil de préparation et d'onboarding complet pour Flipper Zero sous firmware Momentum Ultra : installation d'un pack d'apps curé, d'un asset pack, d'un profil de réglages région-safe, des dictionnaires de saisie rapide, et d'un premier démarrage guidé.

## Ce que ce projet ne fait pas

**Ce projet ne flashe pas de firmware.** Momentum fournit déjà son Web Updater pour cette étape.

## Fonctionnalités

- 🔍 **Détection automatique & exclusivité** : Détection instantanée du Flipper Zero en USB avec vérification des conflits (qFlipper / Web Updater).
- 🛡️ **Garde-fous matériels stricts** : Mode simulation (`--dry-run`) actif par défaut, confirmation interactive obligatoire avant toute écriture réelle, **aucune suppression** sur la carte SD (déplacement préventif vers `/ext/backup`).
- 🌍 **Profils région-safe (P0)** : Sélection de région (`EU / CE`, `US / FCC`, `JP / MIC`, `WORLD`) avec configuration responsable des bandes de fréquences d'émission.
- ⌨️ **Dictionnaires pour clavier prédictif (P1)** : Déploiement des pré-saisies (SSID, adresses IP de lab, commandes BadUSB, mots fréquents) sous `/ext/momentum/dicts/`.
- 📦 **Bundles autoinstall partageables (P1)** : Export et import de packs d'installation complets au format `.tar.gz` ou `.json`.
- 🚀 **Assistant de premier démarrage** : Conseils guidés et suivi de progression en français.

## Commandes

```bash
# Activer l'environnement
.venv\Scripts\activate

# Vérifier la détection du Flipper
momentum-ultra --detect

# Lancer la simulation d'installation (mode sans risque par défaut)
momentum-ultra --install

# Lancer l'installation réelle avec profil régional (ex: US)
momentum-ultra --install --no-dry-run --region US

# Exporter le pack complet vers un bundle partageable
momentum-ultra --export-bundle mon_pack.tar.gz

# Installer un bundle personnalisé téléchargé
momentum-ultra --install --bundle mon_pack.tar.gz --no-dry-run
```

## Développement et tests

```bash
pytest                        # 54 tests automatisés (couche série 100% simulée)
ruff check . && ruff format . # lint et formatage
```
