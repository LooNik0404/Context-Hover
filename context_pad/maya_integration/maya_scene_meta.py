"""Scene-local Context Pad UI metadata storage for set launcher behavior."""

from __future__ import annotations

import json
from typing import Any, Dict

try:
    import maya.cmds as cmds  # type: ignore
except Exception:  # pragma: no cover - outside Maya
    cmds = None

from .maya_sets import list_scene_sets

_META_NODE_NAME = "ContextPadSceneMeta"
_META_ATTR_NAME = "cp_set_ui_state"

_DEFAULT_SET_STATE: Dict[str, Any] = {
    "display_order": 1000,
    "button_color": "#6B7280",
    "group": "Default",
    "hidden_state": False,
}


def ensure_scene_meta_node() -> str:
    """Ensure scene metadata network node and JSON attribute exist."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; metadata node cannot be created")
        return _META_NODE_NAME

    if not cmds.objExists(_META_NODE_NAME):
        cmds.createNode("network", name=_META_NODE_NAME)

    if not cmds.attributeQuery(_META_ATTR_NAME, node=_META_NODE_NAME, exists=True):
        cmds.addAttr(_META_NODE_NAME, longName=_META_ATTR_NAME, dataType="string")
        cmds.setAttr(f"{_META_NODE_NAME}.{_META_ATTR_NAME}", "{}", type="string")

    return _META_NODE_NAME


def load_scene_set_ui_state() -> Dict[str, Dict[str, Any]]:
    """Load scene-local set UI metadata from metadata node JSON."""

    if cmds is None:
        return {}

    node = ensure_scene_meta_node()
    raw_value = cmds.getAttr(f"{node}.{_META_ATTR_NAME}") or "{}"

    try:
        parsed = json.loads(raw_value)
    except Exception:
        _log_warning("Invalid JSON in scene metadata; resetting to empty state")
        parsed = {}

    if not isinstance(parsed, dict):
        _log_warning("Scene metadata root must be an object; resetting to empty state")
        return {}

    normalized: Dict[str, Dict[str, Any]] = {}
    for set_name, state in parsed.items():
        if not isinstance(state, dict):
            continue
        normalized[str(set_name)] = _merge_defaults(state)

    return normalized


def save_scene_set_ui_state(data: Dict[str, Dict[str, Any]]) -> bool:
    """Save scene-local set UI metadata JSON to metadata node."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot save metadata")
        return False

    node = ensure_scene_meta_node()
    safe_data: Dict[str, Dict[str, Any]] = {}
    for set_name, state in (data or {}).items():
        if not isinstance(state, dict):
            continue
        safe_data[str(set_name)] = _merge_defaults(state)

    payload = json.dumps(safe_data, sort_keys=True, indent=2)
    cmds.setAttr(f"{node}.{_META_ATTR_NAME}", payload, type="string")
    _log_info(f"Saved UI metadata for {len(safe_data)} sets")
    return True


def cleanup_missing_set_metadata() -> Dict[str, Dict[str, Any]]:
    """Remove metadata entries for sets that no longer exist in scene."""

    state = load_scene_set_ui_state()
    if cmds is None:
        return state

    existing_sets = set(list_scene_sets())
    cleaned = {name: value for name, value in state.items() if name in existing_sets}
    if len(cleaned) != len(state):
        save_scene_set_ui_state(cleaned)
        _log_info(f"Cleaned stale metadata entries: {len(state) - len(cleaned)}")
    return cleaned


def refresh_scene_set_ui_state() -> Dict[str, Dict[str, Any]]:
    """Ensure metadata has defaults for current sets and remove stale entries."""

    state = cleanup_missing_set_metadata()
    if cmds is None:
        return state

    changed = False
    for set_name in list_scene_sets():
        if set_name not in state:
            state[set_name] = dict(_DEFAULT_SET_STATE)
            changed = True
        else:
            merged = _merge_defaults(state[set_name])
            if merged != state[set_name]:
                state[set_name] = merged
                changed = True

    if changed:
        save_scene_set_ui_state(state)

    return state


def _merge_defaults(state: Dict[str, Any]) -> Dict[str, Any]:
    """Merge metadata state with defaults and normalize value types."""

    merged = dict(_DEFAULT_SET_STATE)
    merged.update(state)

    merged["display_order"] = int(merged.get("display_order", _DEFAULT_SET_STATE["display_order"]))
    merged["button_color"] = str(merged.get("button_color", _DEFAULT_SET_STATE["button_color"]))
    merged["group"] = str(merged.get("group", _DEFAULT_SET_STATE["group"]))
    merged["hidden_state"] = bool(merged.get("hidden_state", _DEFAULT_SET_STATE["hidden_state"]))
    return merged


def _log_info(message: str) -> None:
    """Log info to Script Editor."""

    print(f"[ContextPad:SceneMeta] {message}")


def _log_warning(message: str) -> None:
    """Log warning to Script Editor."""

    if cmds is not None:
        cmds.warning(f"[ContextPad:SceneMeta] {message}")
    else:
        print(f"[ContextPad:SceneMeta][WARN] {message}")
