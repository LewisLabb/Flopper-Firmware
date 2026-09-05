# Fiche de tâche — Client série Flipper Zero et commandes de stockage

## Titre

Implémenter le client série pour le shell CLI du Flipper Zero avec gestion de stockage sécurisée et mode simulation strict.

## Agent assigné

**Gemini (Antigravity).** Tâche de manipulation de flux et protocoles textuels, vérifiable mécaniquement à 100% par des tests unitaires avec simulation de flux série (Mock Serial).

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/client-serie-flipper`

## Objectif

Fournir un client de communication Python pour interagir avec le shell CLI du Flipper Zero connecté en USB (ports `/ext` de la carte SD). Le client doit permettre de lister les fichiers, créer des dossiers, écrire des fichiers et sauvegarder des éléments existants, tout en garantissant les garde-fous matériels : **mode `--dry-run` par défaut**, **interdiction absolue de toute commande de suppression (`storage remove`)**, et déplacement obligatoire vers un répertoire `/ext/backup` lors des sauvegardes.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```
src/momentum_ultra/flipper_client.py
tests/test_flipper_client.py
taches/tache-03-client-serie-flipper.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01-squelette-projet.md`, `taches/tache-02-detection-port.md`.
- Tout appel réel à un port matériel physique pendant les tests.
- Toute utilisation d'une commande de suppression (`storage remove`).

## Contrat

### `src/momentum_ultra/flipper_client.py`

```python
from dataclasses import dataclass

DEFAULT_BACKUP_DIR = "/ext/backup"


class FlipperClientError(Exception):
    """Base exception for Flipper serial client communication."""


class FlipperCommandError(FlipperClientError):
    """Raised when a CLI command returns an error from Flipper Zero."""


class FlipperTimeoutError(FlipperClientError):
    """Raised when communication with Flipper Zero times out."""


@dataclass(frozen=True)
class StorageItem:
    """Represents a file or directory on the Flipper SD card."""

    name: str
    is_dir: bool
    size: int = 0


class FlipperClient:
    """Serial communication client for Flipper Zero CLI shell."""

    def __init__(self, port: str, dry_run: bool = True, timeout: float = 2.0) -> None:
        """Initialize the client with connection parameters and safety mode."""

    def connect(self) -> None:
        """Open serial connection and synchronize with Flipper CLI prompt."""

    def close(self) -> None:
        """Close the serial connection."""

    def __enter__(self) -> "FlipperClient":
        """Enter context manager."""

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Exit context manager."""

    def send_cmd(self, command: str) -> str:
        """Send a raw text command to Flipper and wait for the response prompt."""

    def list_dir(self, path: str) -> list[StorageItem]:
        """List contents of a directory on the SD card (/ext/...)."""

    def mkdir(self, path: str) -> bool:
        """Create a directory on the SD card (no-op in dry_run)."""

    def write_file(self, path: str, content: bytes) -> bool:
        """Write bytes to a file on the SD card (no-op in dry_run)."""

    def backup_item(
        self, source_path: str, backup_dir: str = DEFAULT_BACKUP_DIR
    ) -> str:
        """Move an existing file or directory to the backup folder (never delete)."""
```

Règles de comportement :
1. **Mode simulation (`dry_run=True`)** :
   - Les opérations de lecture (`list_dir`) s'exécutent normalement.
   - Les opérations d'écriture (`mkdir`, `write_file`, `backup_item`) n'envoient aucune commande modifiante sur le port série et retournent un succès simulé.
2. **Garde-fou suppression** :
   - Aucune commande `storage remove` n'existe dans le client. Tout remplacement passe obligatoirement par `backup_item` (`storage rename`).
3. **Synchronisation du prompt** :
   - Le shell Flipper affiche le prompt `>: `. Le client consomme les réponses jusqu'au prompt.
4. **Gestion des erreurs** :
   - Messages d'erreur en français pour les exceptions utilisateur. Code et docstrings en anglais.

## Critères d'acceptation

- [ ] `pytest` passe à 100% avec couverture complète
- [ ] `ruff check .` ne signale rien
- [ ] `ruff format --check .` ne signale rien
- [ ] `FlipperClient` fonctionne en mode context manager (`with FlipperClient(...) as client:`)
- [ ] `dry_run` est actif par défaut sur `FlipperClient`
- [ ] En mode `dry_run=True`, `mkdir`, `write_file` et `backup_item` ne transmettent pas d'ordre d'écriture réel
- [ ] `backup_item` déplace les éléments vers `/ext/backup` sans jamais exécuter `storage remove`
- [ ] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

- **Verdict** : accepté
- **Motif** : Client série Flipper Zero implémenté avec synchronisation de prompt CLI, gestion de `list_dir`, `mkdir`, `write_file`, et `backup_item` (`storage rename`). Garde-fous respectés à 100% : `--dry-run` activé par défaut, aucune commande `storage remove` dans le code, 26/26 tests unitaires passants avec mocks de flux série, Ruff 100% propre.
- **Leçon d'aiguillage** : Tâche de protocole et flux séquentiel exécutée et vérifiée mécaniquement par tests d'intégration simulés.
