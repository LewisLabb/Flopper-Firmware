# momentum-ultra

Outil qui prépare un Flipper Zero fraîchement flashé en Momentum : installation d'un pack d'apps curé, d'un asset pack, d'un profil de réglages, et d'un premier démarrage guidé.

## Ce que ce projet ne fait pas

**Ce projet ne flashe pas de firmware.** Momentum fournit déjà son Web Updater pour cette étape.

## Installation et utilisation

```bash
# Créer et activer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate

# Installer le projet et ses outils de développement
pip install -e ".[dev]"

# Lancer les tests
pytest

# Linter et formater le code
ruff check . && ruff format .
```
