"""Scene metadata abstractions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SceneMeta:
    """Container for high-level scene metadata used by Context Pad."""

    schema_version: int = 1
    last_migrated_utc: str = ""
