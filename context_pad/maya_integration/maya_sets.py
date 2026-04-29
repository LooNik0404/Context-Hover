"""Maya cmds wrappers for scene objectSet operations."""

from __future__ import annotations

import re
from typing import List, Optional

try:
    import maya.cmds as cmds  # type: ignore
except Exception:  # pragma: no cover - outside Maya
    cmds = None

_DEFAULT_SET_NAMES = {
    "defaultLightSet",
    "defaultObjectSet",
    "initialParticleSE",
    "initialShadingGroup",
}
_CONTEXT_PAD_SET_ATTR = "cp_user_selection_set"
_CONTEXT_PAD_ANNOTATION = "ContextPadSelectionSet"


def list_scene_sets() -> List[str]:
    """List scene object sets excluding default Maya sets."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; list_scene_sets returning empty list")
        return []

    candidate_sets = _candidate_scene_sets()
    visible_sets = [item for item in candidate_sets if _is_user_facing_selection_set(item)]
    return sorted(visible_sets)


def list_reference_sets(prepared_only: bool = True) -> List[str]:
    """List referenced scene sets for Set Library import workflows."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; list_reference_sets returning empty list")
        return []

    candidates = _candidate_scene_sets()
    found: List[str] = []
    for set_name in candidates:
        if not is_referenced_set(set_name):
            continue
        if _is_material_or_technical_set(set_name):
            continue
        members = cmds.sets(set_name, query=True) or []
        if not members:
            continue
        if prepared_only and not (_has_context_pad_marker(set_name) or _has_user_annotation(set_name)):
            continue
        found.append(set_name)
    return sorted(found)


def _candidate_scene_sets() -> List[str]:
    """Return raw non-default objectSet candidates before launcher-facing filtering."""

    if cmds is None:
        return []
    all_sets = cmds.ls(type="objectSet") or []
    return [item for item in all_sets if item not in _DEFAULT_SET_NAMES and not item.startswith("default")]


def get_current_selection() -> List[str]:
    """Return current scene selection filtered for practical set operations."""

    return _current_scene_selection()


def get_ordered_selection() -> List[str]:
    """Return ordered selection when Maya tracking is enabled, else fallback selection."""

    return _current_scene_selection(prefer_ordered=True)


def select_set(name: str) -> bool:
    """Replace selection with members of the specified set."""

    return replace_with_set(name)


def select_set_with_saved_order(name: str, ordered_members: Optional[List[str]] = None) -> bool:
    """Replace selection using saved member order while filtering against current set members."""

    members = _set_members(name)
    if members is None:
        return False
    ordered = [item for item in (ordered_members or []) if item in members]
    remainder = [item for item in members if item not in ordered]
    final_members = ordered + remainder
    if not final_members:
        _log_warning(f"Set '{name}' has no selectable members")
        return False
    cmds.select(final_members, replace=True)
    _log_info(f"Selected {len(final_members)} members from set '{name}' using saved order")
    return True


def replace_with_set(name: str) -> bool:
    """Replace current selection with all members from a set."""

    members = _set_members(name)
    if members is None:
        return False
    cmds.select(members, replace=True)
    _log_info(f"Selected {len(members)} members from set '{name}'")
    return True


def add_set_to_selection(name: str) -> bool:
    """Add set members to current selection."""

    members = _set_members(name)
    if members is None:
        return False
    cmds.select(members, add=True)
    _log_info(f"Added {len(members)} members from set '{name}'")
    return True


def add_set_with_saved_order(name: str, ordered_members: Optional[List[str]] = None) -> bool:
    """Add set members to current selection honoring saved order first."""

    members = _set_members(name)
    if members is None:
        return False
    ordered = [item for item in (ordered_members or []) if item in members]
    remainder = [item for item in members if item not in ordered]
    final_members = ordered + remainder
    if not final_members:
        return False
    cmds.select(final_members, add=True)
    _log_info(f"Added {len(final_members)} members from set '{name}' using saved order")
    return True


def remove_set_from_selection(name: str) -> bool:
    """Remove set members from current selection."""

    members = _set_members(name)
    if members is None:
        return False
    cmds.select(members, deselect=True)
    _log_info(f"Removed {len(members)} members from current selection using set '{name}'")
    return True


def create_set_from_selection(name: str, selection: Optional[List[str]] = None) -> str | None:
    """Create a set from selection and return final created set name."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot create set")
        return None

    sanitized_name = sanitize_set_name(name)
    if sanitized_name != name:
        _log_info(f"Adjusted set name '{name}' -> '{sanitized_name}'")

    selected_items = list(selection) if selection is not None else _current_scene_selection(prefer_ordered=True)
    if not selected_items:
        _log_warning("Cannot create set: selection is empty")
        return None

    unique_name = ensure_unique_set_name(sanitized_name)
    if unique_name != sanitized_name:
        _log_info(f"Adjusted duplicate set name '{sanitized_name}' -> '{unique_name}'")

    cmds.sets(selected_items, name=unique_name)
    _mark_context_pad_set(unique_name)
    _log_info(f"Created set '{unique_name}' with {len(selected_items)} members")
    return unique_name


def ensure_unique_set_name(name: str) -> str:
    """Return Maya-safe unique set name using _NN suffix when needed."""

    sanitized_name = sanitize_set_name(name)
    if cmds is None:
        return sanitized_name
    if not cmds.objExists(sanitized_name):
        return sanitized_name

    base_name = re.sub(r"_(\d{2})$", "", sanitized_name)
    index = 1
    while True:
        candidate = f"{base_name}_{index:02d}"
        if not cmds.objExists(candidate):
            return candidate
        index += 1


def update_set_from_selection(name: str) -> bool:
    """Replace all members of an existing set with current selection."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot update set")
        return False
    if not cmds.objExists(name):
        _log_warning(f"Cannot update set: '{name}' does not exist")
        return False

    selection = _current_scene_selection(prefer_ordered=True)
    if not selection:
        _log_warning("Cannot update set: selection is empty")
        return False

    cmds.sets(clear=name)
    cmds.sets(selection, addElement=name)
    _log_info(f"Updated set '{name}' with {len(selection)} members")
    return True


def rename_set(old_name: str, new_name: str) -> bool:
    """Rename an existing set to a new unique name."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot rename set")
        return False
    sanitized_name = sanitize_set_name(new_name)
    if sanitized_name != new_name:
        _log_info(f"Adjusted set name '{new_name}' -> '{sanitized_name}'")

    if not cmds.objExists(old_name):
        _log_warning(f"Cannot rename set: '{old_name}' does not exist")
        return False
    if old_name == sanitized_name:
        _log_info(f"Rename skipped: '{old_name}' already matches normalized name")
        return True
    final_name = ensure_unique_set_name(sanitized_name)
    if final_name != sanitized_name:
        _log_info(f"Adjusted duplicate rename target '{sanitized_name}' -> '{final_name}'")

    renamed_node = cmds.rename(old_name, final_name)
    if not renamed_node:
        _log_warning(f"Rename failed for '{old_name}' -> '{final_name}'")
        return False
    _log_info(f"Renamed set '{old_name}' to '{renamed_node}'")
    return True


def delete_set(name: str) -> bool:
    """Delete an existing set safely."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot delete set")
        return False
    if not cmds.objExists(name):
        _log_warning(f"Cannot delete set: '{name}' does not exist")
        return False
    if is_referenced_set(name):
        _log_warning(f"Cannot delete referenced set: '{name}'")
        return False
    if not _is_user_facing_selection_set(name):
        _log_warning(f"Refusing to delete non-user-facing set: '{name}'")
        return False

    cmds.delete(name)
    _log_info(f"Deleted set '{name}'")
    return True


def get_sets_for_object(node_name: str) -> List[str]:
    """Return all sets that contain the specified node."""

    if cmds is None:
        return []
    if not cmds.objExists(node_name):
        _log_warning(f"Node does not exist: {node_name}")
        return []

    found: List[str] = []
    for set_name in list_scene_sets():
        members = cmds.sets(set_name, query=True) or []
        if node_name in members:
            found.append(set_name)
    return sorted(found)


def get_set_size(name: str) -> int:
    """Return number of members in a set."""

    members = _set_members(name)
    return len(members) if members is not None else 0


def set_exists(name: str) -> bool:
    """Return True when a set node exists in scene."""

    if cmds is None:
        return False
    try:
        return bool(cmds.objExists(name))
    except Exception:
        return False


def is_referenced_set(name: str) -> bool:
    """Return True if the set node is referenced from an external file."""

    if cmds is None or not cmds.objExists(name):
        return False
    try:
        return bool(cmds.referenceQuery(name, isNodeReferenced=True))
    except Exception:
        return False


def get_related_sets_for_selection(selection: Optional[List[str]] = None, require_all: bool = True) -> List[str]:
    """Return sets related to selection using strict matching with ranked fallback."""

    if cmds is None:
        return []

    chosen = selection if selection is not None else _current_scene_selection()
    if not chosen:
        _log_info("No selection provided for related sets query")
        return []

    try:
        from .maya_scene_meta import load_scene_set_ui_state

        ui_state = load_scene_set_ui_state()
    except Exception:
        ui_state = {}

    selected_long = set(chosen)
    selected_short = {_short_name(item) for item in chosen}
    selected_count = max(1, len(selected_short))

    strict_related: List[str] = []
    partial_related: List[tuple[str, int, float, int]] = []
    for set_name in list_scene_sets():
        members = cmds.sets(set_name, query=True) or []
        members_long = set(members)
        members_short = {_short_name(item) for item in members}

        overlap_count = max(
            len(selected_long.intersection(members_long)),
            len(selected_short.intersection(members_short)),
        )
        if overlap_count <= 0:
            continue

        strict_match = selected_long.issubset(members_long) or selected_short.issubset(members_short)
        if strict_match:
            strict_related.append(set_name)
            continue

        overlap_ratio = float(overlap_count) / float(selected_count)
        partial_related.append((set_name, overlap_count, overlap_ratio, len(members_short)))

    if len(chosen) == 1:
        related = strict_related + [item[0] for item in partial_related]
        related = sorted(
            set(related),
            key=lambda item: (
                get_set_size(item),
                int(ui_state.get(item, {}).get("display_order", 1000)),
                item.lower(),
            ),
        )
        return related

    if require_all and strict_related:
        strict_related.sort(
            key=lambda item: (
                get_set_size(item),
                int(ui_state.get(item, {}).get("display_order", 1000)),
                item.lower(),
            )
        )
        return strict_related

    partial_related.sort(
        key=lambda item: (
            -item[1],  # overlap count desc
            -item[2],  # overlap ratio desc
            item[3],  # set size asc (specific first)
            int(ui_state.get(item[0], {}).get("display_order", 1000)),
            item[0].lower(),
        )
    )
    return [item[0] for item in partial_related]



def _current_scene_selection(prefer_ordered: bool = False) -> List[str]:
    """Return selection excluding service/meta nodes and objectSet nodes."""

    if cmds is None:
        return []

    selected: List[str] = []
    if prefer_ordered:
        try:
            selected = cmds.ls(orderedSelection=True, long=True) or []
        except Exception:
            selected = []
    if not selected:
        selected = cmds.ls(selection=True, long=True) or []
    filtered: List[str] = []
    for node in selected:
        short_name = _short_name(node)
        if short_name == "ContextPadSceneMeta":
            continue
        if cmds.nodeType(node) == "objectSet":
            continue
        filtered.append(node)
    return filtered


def _short_name(node_name: str) -> str:
    """Return short node name without DAG path segments."""

    return str(node_name).split("|")[-1]


def sanitize_set_name(name: str, prefix: str = "set_") -> str:
    """Normalize user-entered set names into Maya-safe readable identifiers."""

    raw = str(name or "").strip()
    cleaned = re.sub(r"\s+", "_", raw)
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "set"
    if cleaned[0].isdigit():
        cleaned = f"{prefix}{cleaned}"
    return cleaned


def _is_user_facing_selection_set(name: str) -> bool:
    """Return True for animator-facing selection sets only."""

    if not name or name in _DEFAULT_SET_NAMES or name.startswith("default"):
        return False
    if cmds is None or not cmds.objExists(name):
        return False
    if _is_material_or_technical_set(name):
        return False

    members = cmds.sets(name, query=True) or []
    if not members:
        return False

    if is_referenced_set(name):
        return _has_context_pad_marker(name) or _has_user_annotation(name)

    return True


def _is_material_or_technical_set(name: str) -> bool:
    """Return True when set should be hidden from animator-facing UI."""

    node_type = str(cmds.nodeType(name) or "")
    if node_type == "shadingEngine":
        return True

    technical_flags = ["renderableOnlySet", "verticesOnlySet", "edgesOnlySet", "facetsOnlySet", "editPointsOnlySet"]
    for attr in technical_flags:
        if cmds.attributeQuery(attr, node=name, exists=True):
            try:
                if bool(cmds.getAttr(f"{name}.{attr}")):
                    return True
            except Exception:
                pass

    partitions = cmds.listConnections(name, type="partition") or []
    if any(part == "renderPartition" for part in partitions):
        return True

    return False


def _mark_context_pad_set(name: str) -> None:
    """Mark newly created sets so they are clearly user-facing in future sessions."""

    if cmds is None or not cmds.objExists(name):
        return
    if not cmds.attributeQuery(_CONTEXT_PAD_SET_ATTR, node=name, exists=True):
        cmds.addAttr(name, longName=_CONTEXT_PAD_SET_ATTR, attributeType="bool")
    cmds.setAttr(f"{name}.{_CONTEXT_PAD_SET_ATTR}", True)
    if cmds.attributeQuery("annotation", node=name, exists=True):
        try:
            cmds.setAttr(f"{name}.annotation", _CONTEXT_PAD_ANNOTATION, type="string")
        except Exception:
            pass


def _has_context_pad_marker(name: str) -> bool:
    """Return True when set has explicit Context Pad marker attribute enabled."""

    if cmds is None or not cmds.objExists(name):
        return False
    if not cmds.attributeQuery(_CONTEXT_PAD_SET_ATTR, node=name, exists=True):
        return False
    try:
        return bool(cmds.getAttr(f"{name}.{_CONTEXT_PAD_SET_ATTR}"))
    except Exception:
        return False


def _has_user_annotation(name: str) -> bool:
    """Return True when set has non-empty annotation text indicating user intent."""

    if cmds is None or not cmds.objExists(name):
        return False
    if not cmds.attributeQuery("annotation", node=name, exists=True):
        return False
    try:
        annotation = str(cmds.getAttr(f"{name}.annotation") or "").strip()
    except Exception:
        return False
    return bool(annotation)

def _set_members(name: str) -> Optional[List[str]]:
    """Return set members or None when set is unavailable."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot query set members")
        return None
    if not cmds.objExists(name):
        _log_warning(f"Set does not exist: {name}")
        return None

    members = cmds.sets(name, query=True) or []
    return list(members)


def _log_info(message: str) -> None:
    """Log info to Script Editor."""

    print(f"[ContextPad:Sets] {message}")


def _log_warning(message: str) -> None:
    """Log warning to Script Editor."""

    if cmds is not None:
        cmds.warning(f"[ContextPad:Sets] {message}")
    else:
        print(f"[ContextPad:Sets][WARN] {message}")
