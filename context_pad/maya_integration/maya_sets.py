"""Maya cmds wrappers for scene objectSet operations."""

from __future__ import annotations

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


def list_scene_sets() -> List[str]:
    """List scene object sets excluding default Maya sets."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; list_scene_sets returning empty list")
        return []

    all_sets = cmds.ls(type="objectSet") or []
    return sorted([item for item in all_sets if item not in _DEFAULT_SET_NAMES and not item.startswith("default")])


def get_current_selection() -> List[str]:
    """Return current scene selection filtered for practical set operations."""

    return _current_scene_selection()


def select_set(name: str) -> bool:
    """Replace selection with members of the specified set."""

    return replace_with_set(name)


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


def remove_set_from_selection(name: str) -> bool:
    """Remove set members from current selection."""

    members = _set_members(name)
    if members is None:
        return False
    cmds.select(members, deselect=True)
    _log_info(f"Removed {len(members)} members from current selection using set '{name}'")
    return True


def create_set_from_selection(name: str) -> bool:
    """Create a set from current selection with a unique new name."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot create set")
        return False

    selection = _current_scene_selection()
    if not selection:
        _log_warning("Cannot create set: selection is empty")
        return False
    if cmds.objExists(name):
        _log_warning(f"Cannot create set: '{name}' already exists")
        return False

    cmds.sets(selection, name=name)
    _log_info(f"Created set '{name}' with {len(selection)} members")
    return True


def update_set_from_selection(name: str) -> bool:
    """Replace all members of an existing set with current selection."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot update set")
        return False
    if not cmds.objExists(name):
        _log_warning(f"Cannot update set: '{name}' does not exist")
        return False

    selection = _current_scene_selection()
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
    if not cmds.objExists(old_name):
        _log_warning(f"Cannot rename set: '{old_name}' does not exist")
        return False
    if cmds.objExists(new_name):
        _log_warning(f"Cannot rename set: '{new_name}' already exists")
        return False

    cmds.rename(old_name, new_name)
    _log_info(f"Renamed set '{old_name}' to '{new_name}'")
    return True


def delete_set(name: str) -> bool:
    """Delete an existing set safely."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot delete set")
        return False
    if not cmds.objExists(name):
        _log_warning(f"Cannot delete set: '{name}' does not exist")
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


def get_related_sets_for_selection(selection: Optional[List[str]] = None, require_all: bool = True) -> List[str]:
    """Return sets related to current/explicit selection, sorted by specificity."""

    if cmds is None:
        return []

    chosen = selection if selection is not None else _current_scene_selection()
    if not chosen:
        _log_info("No selection provided for related sets query")
        return []

    selected_long = set(chosen)
    selected_short = {_short_name(item) for item in chosen}
    related: List[str] = []
    for set_name in list_scene_sets():
        members = cmds.sets(set_name, query=True) or []
        members_long = set(members)
        members_short = {_short_name(item) for item in members}

        if require_all:
            if selected_long.issubset(members_long) or selected_short.issubset(members_short):
                related.append(set_name)
        elif selected_long.intersection(members_long) or selected_short.intersection(members_short):
            related.append(set_name)

    try:
        from .maya_scene_meta import load_scene_set_ui_state

        ui_state = load_scene_set_ui_state()
    except Exception:
        ui_state = {}

    related.sort(
        key=lambda item: (
            get_set_size(item),
            int(ui_state.get(item, {}).get("display_order", 1000)),
            item.lower(),
        )
    )
    return related



def _current_scene_selection() -> List[str]:
    """Return selection excluding service/meta nodes and objectSet nodes."""

    if cmds is None:
        return []

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
