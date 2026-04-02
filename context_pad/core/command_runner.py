"""Command execution abstractions for Python and MEL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommandLanguage(str, Enum):
    """Supported script language identifiers."""

    PYTHON = "python"
    MEL = "mel"


@dataclass(frozen=True)
class CommandPayload:
    """Structured payload representing a command invocation target."""

    language: CommandLanguage
    source_path: str


class CommandRunner:
    """Placeholder command execution service."""

    def run(self, payload: CommandPayload) -> None:
        """Execute a command payload.

        This is intentionally a placeholder in scaffolding stage.
        """

        _ = payload
