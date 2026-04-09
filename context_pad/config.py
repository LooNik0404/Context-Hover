"""Configuration constants and defaults for Context Pad."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ContextPadConfig:
    """Container for top-level configuration values used by the tool."""

    tool_name: str = "Context Pad"
    schema_version: int = 1
    manifest_filename: str = "manifest.json"
    manifest_root: Path = PACKAGE_ROOT / "manifest"


DEFAULT_CONFIG = ContextPadConfig()
