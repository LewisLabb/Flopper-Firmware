# Fiche de tâche — Détection du Flipper Zero et vérification du port série

## Titre

Implémenter la détection automatique du Flipper Zero et le contrôle de disponibilité du port série.

## Agent assigné

**Gemini (Antigravity).** Tâche vérifiable par tests unitaires avec simulation de `serial.tools.list_ports.comports` et `serial.Serial`. Les signatures et critères sont entièrement spécifiés.

Revue obligatoire par le sous-agent `reviseur` de Claude Code avant fusion.

## Branche

`tache/detection-port`

## Objectif

Pour préparer le Flipper, l'outil doit être capable de détecter automatiquement le port série USB (VID `0x0483`, PID `0x5740`) sans configuration manuelle de l'utilisateur, et vérifier qu'aucune autre application (comme qFlipper) ne verrouille le port. Aucun octet n'est envoyé à ce stade : il s'agit d'une détection et d'un test de disponibilité passive.

## Périmètre

Fichiers à créer ou modifier, et eux seuls :

```
src/momentum_ultra/device.py
src/momentum_ultra/cli.py
tests/test_device.py
tests/test_cli.py
taches/tache-02-detection-port.md
```

## Hors périmètre

- `AGENTS.md`, `CLAUDE.md`, `taches/_GABARIT.md`, `taches/tache-01-squelette-projet.md`.
- Tout protocole de commande Flipper (shell CLI, protobuf, écriture de fichier) — réservé aux tâches suivantes.
- Tout appel réel au matériel physique lors des tests.

## Contrat

### `src/momentum_ultra/device.py`

```python
from dataclasses import dataclass

FLIPPER_VID = 0x0483
FLIPPER_PID = 0x5740


class FlipperDeviceError(Exception):
    """Base exception for Flipper device detection and connection issues."""


class FlipperNotFoundError(FlipperDeviceError):
    """Raised when no Flipper Zero is detected on available serial ports."""


class MultipleFlipperFoundError(FlipperDeviceError):
    """Raised when more than one Flipper Zero is connected."""


class FlipperPortBusyError(FlipperDeviceError):
    """Raised when the Flipper Zero serial port is already in use by another application."""


@dataclass(frozen=True)
class FlipperDevice:
    """Represents a detected Flipper Zero device."""

    port: str
    description: str
    serial_number: str | None = None


def find_flipper() -> FlipperDevice:
    """Find a connected Flipper Zero using USB VID and PID."""


def is_port_available(port: str) -> bool:
    """Check if a serial port can be opened without conflict."""
```

Comportement attendu :
- `find_flipper()` parcourt les ports via `serial.tools.list_ports.comports()`.
- Filtre sur `vid == FLIPPER_VID` (1155) et `pid == FLIPPER_PID` (22336).
- Si aucun trouvé → lève `FlipperNotFoundError` avec message en français : `"Aucun Flipper Zero détecté. Vérifiez la connexion USB."`
- Si plusieurs trouvés → lève `MultipleFlipperFoundError` avec message en français indiquant le nombre de périphériques détectés.
- Si exactement un trouvé → retourne une instance de `FlipperDevice`.
- `is_port_available(port)` tente d'ouvrir le port avec `serial.Serial(port)` puis le referme immédiatement. Retourne `True` si succès, `False` si `serial.SerialException` (ex: port occupé par qFlipper).

### `src/momentum_ultra/cli.py`

- Mise à jour de `main` et de l'analyseur d'arguments :
  - Ajout du flag `--detect` : lance la détection du Flipper.
  - Si `--detect` est passé :
    - Tente `find_flipper()`.
    - Si trouvé et disponible : affiche `"Flipper Zero détecté sur <port>."` et retourne `0`.
    - Si le port est occupé : affiche `"Flipper Zero détecté sur <port>, mais le port est occupé (qFlipper ou un autre outil est-il ouvert ?)."` et retourne `1`.
    - Si non trouvé ou erreur : affiche le message d'erreur en français sur la sortie d'erreur et retourne `1`.
  - Si aucun argument n'est passé : affiche toujours l'aide et retourne `0`.
  - Ne lève jamais d'exception non interceptée vers l'appelant.

### `tests/test_device.py` & `tests/test_cli.py`

- `test_device.py` teste tous les cas nominaux et d'erreur avec des mocks de `serial.tools.list_ports.comports` et `serial.Serial`.
- `test_cli.py` teste l'intégration du flag `--detect` via l'interface publique `main()`.

## Critères d'acceptation

- [ ] `pytest` passe à 100% avec couverture complète des cas (0 trouvé, 1 trouvé, >1 trouvés, port occupé, port libre)
- [ ] `ruff check .` ne signale rien
- [ ] `ruff format --check .` ne signale rien
- [ ] `main(["--detect"])` retourne `0` et affiche le port quand un Flipper simulé est présent
- [ ] `main(["--detect"])` retourne `1` et affiche un message clair en français si aucun Flipper n'est présent ou si le port est occupé
- [ ] Tous les tests utilisent des mocks et ne touchent jamais à un port physique
- [ ] Aucun fichier hors périmètre créé ou modifié

## Conditions d'arrêt

- Une modification hors périmètre semble nécessaire
- Une dépendance non listée serait requise
- Le contrat ci-dessus paraît incohérent

## Journal de revue

Rempli par Opus après exécution.

- **Verdict** :
- **Motif** :
- **Leçon d'aiguillage** :
