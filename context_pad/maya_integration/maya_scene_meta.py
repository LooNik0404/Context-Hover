"""Maya scene metadata node wrappers."""

from __future__ import annotations

from ..core.scene_meta import SceneMeta


def read_scene_meta() -> SceneMeta:
    """Read scene metadata from Maya nodes."""

    return SceneMeta()


def write_scene_meta(scene_meta: SceneMeta) -> None:
    """Write scene metadata into Maya nodes."""

    _ = scene_meta
