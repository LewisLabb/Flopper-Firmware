"""Serial communication client for Flipper Zero CLI storage operations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Self

import serial

DEFAULT_BACKUP_DIR = "/ext/backup"
PROMPT = b">: "


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

    def __init__(
        self,
        port: str,
        dry_run: bool = True,
        timeout: float = 2.0,
    ) -> None:
        """Initialize the client with connection parameters and safety mode."""
        self.port = port
        self.dry_run = dry_run
        self.timeout = timeout
        self._serial: serial.Serial | None = None

    def connect(self) -> None:
        """Open serial connection and synchronize with Flipper CLI prompt."""
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=115200,
                timeout=self.timeout,
            )
        except (serial.SerialException, OSError) as exc:
            raise FlipperClientError(
                f"Impossible d'ouvrir le port série {self.port} : {exc}"
            ) from exc

        # Synchronize CLI shell
        self._sync_prompt()

    def close(self) -> None:
        """Close the serial connection."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def __enter__(self) -> Self:
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager."""
        self.close()

    def _sync_prompt(self) -> None:
        """Send newline and wait for the CLI prompt to verify ready state."""
        if self._serial is None:
            raise FlipperClientError("Le client série n'est pas connecté.")

        self._serial.reset_input_buffer()
        self._serial.write(b"\r\n")
        self._read_until_prompt()

    def _read_until_prompt(self) -> str:
        """Read incoming serial bytes until the prompt marker is reached."""
        if self._serial is None:
            raise FlipperClientError("Le client série n'est pas connecté.")

        buffer = bytearray()
        start_time = time.time()

        while True:
            if buffer.endswith(PROMPT):
                # Strip prompt marker from response
                return buffer[: -len(PROMPT)].decode("utf-8", errors="replace")

            chunk = self._serial.read(1)
            if chunk:
                buffer.extend(chunk)
            else:
                if (time.time() - start_time) > self.timeout:
                    raise FlipperTimeoutError(
                        "Délai d'attente dépassé lors de la réponse du Flipper Zero."
                    )
                time.sleep(0.005)

    def send_cmd(self, command: str) -> str:
        """Send a raw text command to Flipper and wait for the response prompt."""
        if self._serial is None:
            raise FlipperClientError("Le client série n'est pas connecté.")

        cmd_bytes = f"{command.strip()}\r\n".encode()
        self._serial.write(cmd_bytes)
        output = self._read_until_prompt()

        # Strip echo of the command if present at the start
        lines = output.replace("\r\n", "\n").split("\n")
        if lines and command.strip() in lines[0]:
            lines = lines[1:]

        return "\n".join(lines).strip()

    def list_dir(self, path: str) -> list[StorageItem]:
        """List contents of a directory on the SD card (/ext/...)."""
        output = self.send_cmd(f"storage list {path}")
        if "Storage error" in output or "error:" in output.lower():
            raise FlipperCommandError(
                f"Erreur lors de la lecture du dossier {path} : {output}"
            )

        items: list[StorageItem] = []
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("[DIR]"):
                dir_name = line[5:].strip()
                items.append(StorageItem(name=dir_name, is_dir=True, size=0))
            elif line.startswith("[FILE]"):
                parts = line[6:].strip().split()
                if len(parts) >= 2:
                    name = " ".join(parts[:-1])
                    size_str = parts[-1].rstrip("B")
                    size = int(size_str) if size_str.isdigit() else 0
                    items.append(StorageItem(name=name, is_dir=False, size=size))
                elif len(parts) == 1:
                    items.append(StorageItem(name=parts[0], is_dir=False, size=0))

        return items

    def mkdir(self, path: str) -> bool:
        """Create a directory on the SD card (no-op in dry_run)."""
        if self.dry_run:
            return True

        output = self.send_cmd(f"storage mkdir {path}")
        if "Storage error" in output or "error:" in output.lower():
            raise FlipperCommandError(
                f"Impossible de créer le dossier {path} : {output}"
            )
        return True

    def write_file(self, path: str, content: bytes) -> bool:
        """Write bytes to a file on the SD card (no-op in dry_run)."""
        if self.dry_run:
            return True

        output = self.send_cmd(f"storage write {path}")
        if "Storage error" in output or "error:" in output.lower():
            raise FlipperCommandError(
                f"Impossible d'écrire dans le fichier {path} : {output}"
            )
        if self._serial is not None:
            self._serial.write(content)
            self._read_until_prompt()
        return True

    def backup_item(
        self,
        source_path: str,
        backup_dir: str = DEFAULT_BACKUP_DIR,
    ) -> str:
        """Move an existing file or directory to the backup folder (never delete)."""
        clean_source = source_path.rstrip("/")
        item_name = clean_source.split("/")[-1]
        target_path = f"{backup_dir.rstrip('/')}/{item_name}"

        if self.dry_run:
            return target_path

        self.mkdir(backup_dir)
        output = self.send_cmd(f"storage rename {clean_source} {target_path}")
        if "Storage error" in output or "error:" in output.lower():
            raise FlipperCommandError(
                f"Impossible de sauvegarder {clean_source} vers {target_path} : {output}"
            )

        return target_path
