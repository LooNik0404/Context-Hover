"""Temporary harness for scene set operations before full UI hookup."""

from __future__ import annotations

from typing import Dict, List

from .set_registry import SetRegistry


def run_set_registry_demo(set_name: str = "ContextPad_TestSet") -> Dict[str, object]:
    """Run a small set operation flow and return results."""

    registry = SetRegistry()
    scene_sets_before = registry.list_scene_sets()

    created = registry.create_set_from_selection(set_name)
    related = registry.get_related_sets_for_selection()
    sizes: Dict[str, int] = {item: registry.get_set_size(item) for item in related}

    return {
        "scene_sets_before": scene_sets_before,
        "created": created,
        "related_sets": related,
        "related_sizes": sizes,
    }


def list_related_for_current_selection(require_all: bool = True) -> List[str]:
    """Convenience function for quickly testing related set queries."""

    return SetRegistry().get_related_sets_for_selection(require_all=require_all)
