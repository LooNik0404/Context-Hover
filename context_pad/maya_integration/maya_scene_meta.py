"""Scene-local Context Pad UI metadata storage for set launcher behavior."""

from __future__ import annotations

import json
from typing import Any, Dict

try:
    import maya.cmds as cmds  # type: ignore
except Exception:  # pragma: no cover - outside Maya
    cmds = None

_META_NODE_NAME = "ContextPadSceneMeta"
_META_ATTR_NAME = "cp_set_ui_state"

_DEFAULT_SET_STATE: Dict[str, Any] = {
    "display_order": 1000,
    "button_color": "#6B7280",
    "group": "Default",
    "hidden_in_launcher": False,
}
_DEFAULT_LIBRARY_ENTRY: Dict[str, Any] = {
    "id": "",
    "source_kind": "local_maya_set",
    "source_ref": "",
    "display_label": "",
    "button_color": "#6B7280",
    "display_order": 1000,
    "hidden_in_launcher": False,
    "is_referenced": False,
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

    library = _normalize_library_payload(parsed)
    state_by_set: Dict[str, Dict[str, Any]] = {}
    for entry in library.values():
        source_ref = str(entry.get("source_ref", "")).strip()
        if not source_ref:
            continue
        state_by_set[source_ref] = {
            "display_order": int(entry.get("display_order", 1000)),
            "button_color": str(entry.get("button_color", "#6B7280")),
            "group": "Main",
            "hidden_in_launcher": bool(entry.get("hidden_in_launcher", False)),
        }
    return state_by_set


def save_scene_set_ui_state(data: Dict[str, Dict[str, Any]]) -> bool:
    """Save scene-local set UI metadata JSON to metadata node."""

    if cmds is None:
        _log_warning("Maya cmds unavailable; cannot save metadata")
        return False

    node = ensure_scene_meta_node()
    library = load_scene_set_library()
    for set_name, state in (data or {}).items():
        if not isinstance(state, dict):
            continue
        entry_id = _find_entry_id_by_source_ref(library, str(set_name))
        if not entry_id:
            entry_id = _next_entry_id(library)
        merged = dict(_DEFAULT_LIBRARY_ENTRY)
        merged.update(
            {
                "id": entry_id,
                "source_kind": "local_maya_set",
                "source_ref": str(set_name),
                "display_label": _display_label(str(set_name)),
                "button_color": str(state.get("button_color", "#6B7280")),
                "display_order": int(state.get("display_order", 1000)),
                "hidden_in_launcher": bool(state.get("hidden_in_launcher", state.get("hidden_state", False))),
            }
        )
        library[entry_id] = merged

    payload = json.dumps({"entries": library}, sort_keys=True, indent=2)
    cmds.setAttr(f"{node}.{_META_ATTR_NAME}", payload, type="string")
    _log_info(f"Saved UI metadata for {len(library)} set-library entries")
    return True


def cleanup_missing_set_metadata() -> Dict[str, Dict[str, Any]]:
    """Remove metadata entries for sets that no longer exist in scene."""

    state = load_scene_set_ui_state()
    if cmds is None:
        return state

    return state


def refresh_scene_set_ui_state() -> Dict[str, Dict[str, Any]]:
    """Ensure metadata has defaults for current sets and remove stale entries."""

    state = cleanup_missing_set_metadata()
    if cmds is None:
        return state

    return state


def load_scene_set_library() -> Dict[str, Dict[str, Any]]:
    """Load explicit Context Pad set-library entries persisted in scene metadata."""

    if cmds is None:
        return {}
    node = ensure_scene_meta_node()
    raw_value = cmds.getAttr(f"{node}.{_META_ATTR_NAME}") or "{}"
    try:
        parsed = json.loads(raw_value)
    except Exception:
        parsed = {}
    return _normalize_library_payload(parsed)


def save_scene_set_library(entries: Dict[str, Dict[str, Any]]) -> bool:
    """Save explicit Context Pad set-library entries to scene metadata."""

    if cmds is None:
        return False
    node = ensure_scene_meta_node()
    normalized: Dict[str, Dict[str, Any]] = {}
    for entry_id, entry in (entries or {}).items():
        if not isinstance(entry, dict):
            continue
        merged = dict(_DEFAULT_LIBRARY_ENTRY)
        merged.update(entry)
        merged["id"] = str(entry_id)
        merged["source_ref"] = str(merged.get("source_ref", ""))
        merged["display_label"] = str(merged.get("display_label", _display_label(merged["source_ref"])))
        merged["button_color"] = str(merged.get("button_color", "#6B7280"))
        merged["display_order"] = int(merged.get("display_order", 1000))
        merged["hidden_in_launcher"] = bool(merged.get("hidden_in_launcher", False))
        merged["is_referenced"] = bool(merged.get("is_referenced", False))
        normalized[str(entry_id)] = merged
    payload = json.dumps({"entries": normalized}, sort_keys=True, indent=2)
    cmds.setAttr(f"{node}.{_META_ATTR_NAME}", payload, type="string")
    return True


def register_set_library_entry(
    source_ref: str,
    source_kind: str,
    display_label: str | None = None,
    color: str = "#6B7280",
    hidden_in_launcher: bool = False,
    is_referenced: bool = False,
) -> str:
    """Create or update a set-library entry for a source set reference."""

    entries = load_scene_set_library()
    source_ref = str(source_ref).strip()
    entry_id = _find_entry_id_by_source_ref(entries, source_ref) or _next_entry_id(entries)
    sort_order = int(entries.get(entry_id, {}).get("display_order", _next_display_order(entries)))
    entries[entry_id] = {
        "id": entry_id,
        "source_kind": source_kind,
        "source_ref": source_ref,
        "display_label": str(display_label or _display_label(source_ref)),
        "button_color": color,
        "display_order": sort_order,
        "hidden_in_launcher": bool(hidden_in_launcher),
        "is_referenced": bool(is_referenced),
    }
    save_scene_set_library(entries)
    return entry_id


def update_set_library_entry(entry_id: str, updates: Dict[str, Any]) -> bool:
    """Patch an existing set-library entry by id."""

    entries = load_scene_set_library()
    if entry_id not in entries:
        return False
    merged = dict(entries[entry_id])
    merged.update(updates or {})
    entries[entry_id] = merged
    return save_scene_set_library(entries)


def delete_set_library_entry(entry_id: str) -> bool:
    """Delete a set-library entry by id."""

    entries = load_scene_set_library()
    if entry_id not in entries:
        return False
    entries.pop(entry_id, None)
    return save_scene_set_library(entries)


def _merge_defaults(state: Dict[str, Any]) -> Dict[str, Any]:
    """Merge metadata state with defaults and normalize value types."""

    merged = dict(_DEFAULT_SET_STATE)
    merged.update(state)
    if "hidden_in_launcher" not in merged and "hidden_state" in merged:
        merged["hidden_in_launcher"] = merged.get("hidden_state", False)
    merged.pop("hidden_state", None)

    merged["display_order"] = int(merged.get("display_order", _DEFAULT_SET_STATE["display_order"]))
    merged["button_color"] = str(merged.get("button_color", _DEFAULT_SET_STATE["button_color"]))
    merged["group"] = str(merged.get("group", _DEFAULT_SET_STATE["group"]))
    merged["hidden_in_launcher"] = bool(merged.get("hidden_in_launcher", _DEFAULT_SET_STATE["hidden_in_launcher"]))
    return merged


def _normalize_library_payload(raw_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Normalize legacy/new payload shapes into explicit entries mapping."""

    entries_root = raw_payload.get("entries") if isinstance(raw_payload, dict) else None
    source = entries_root if isinstance(entries_root, dict) else raw_payload if isinstance(raw_payload, dict) else {}

    normalized: Dict[str, Dict[str, Any]] = {}
    for key, value in source.items():
        if not isinstance(value, dict):
            continue
        if "source_ref" in value:
            entry_id = str(value.get("id") or key)
            merged = dict(_DEFAULT_LIBRARY_ENTRY)
            merged.update(value)
            merged["id"] = entry_id
            merged["source_ref"] = str(merged.get("source_ref", ""))
            if not merged["display_label"]:
                merged["display_label"] = _display_label(merged["source_ref"])
            normalized[entry_id] = merged
            continue

        # Legacy shape: top-level key is full set name -> ui state dict
        source_ref = str(key)
        entry_id = _next_entry_id(normalized)
        normalized[entry_id] = {
            "id": entry_id,
            "source_kind": "local_maya_set",
            "source_ref": source_ref,
            "display_label": _display_label(source_ref),
            "button_color": str(value.get("button_color", "#6B7280")),
            "display_order": int(value.get("display_order", 1000)),
            "hidden_in_launcher": bool(value.get("hidden_in_launcher", value.get("hidden_state", False))),
            "is_referenced": False,
        }
    return normalized


def _find_entry_id_by_source_ref(entries: Dict[str, Dict[str, Any]], source_ref: str) -> str | None:
    for entry_id, entry in entries.items():
        if str(entry.get("source_ref", "")) == source_ref:
            return entry_id
    return None


def _next_entry_id(entries: Dict[str, Dict[str, Any]]) -> str:
    index = 1
    while True:
        candidate = f"entry_{index:03d}"
        if candidate not in entries:
            return candidate
        index += 1


def _next_display_order(entries: Dict[str, Dict[str, Any]]) -> int:
    if not entries:
        return 10
    return max(int(item.get("display_order", 0)) for item in entries.values()) + 10


def _display_label(source_ref: str) -> str:
    short_name = str(source_ref).split("|")[-1]
    return short_name.split(":")[-1]


def _log_info(message: str) -> None:
    """Log info to Script Editor."""

    print(f"[ContextPad:SceneMeta] {message}")


def _log_warning(message: str) -> None:
    """Log warning to Script Editor."""

    if cmds is not None:
        cmds.warning(f"[ContextPad:SceneMeta] {message}")
    else:
        print(f"[ContextPad:SceneMeta][WARN] {message}")
