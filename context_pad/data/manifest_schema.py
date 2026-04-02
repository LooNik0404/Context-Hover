"""Manifest schema scaffolding and validation placeholders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ManifestCategory:
    """Schema model for a manifest category entry."""

    category_id: str
    name: str
    color: str


@dataclass(frozen=True)
class ManifestScript:
    """Schema model for a manifest script entry."""

    script_id: str
    name: str
    category_id: str
    language: str
    source_path: str


@dataclass(frozen=True)
class ManifestModel:
    """Top-level schema model for a manifest payload."""

    schema_version: int
    categories: List[ManifestCategory] = field(default_factory=list)
    scripts: List[ManifestScript] = field(default_factory=list)


def validate_manifest(_: ManifestModel) -> None:
    """Validate manifest payload.

    This is intentionally a placeholder for future schema checks.
    """
