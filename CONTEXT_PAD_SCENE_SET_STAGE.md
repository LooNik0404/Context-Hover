# Context Pad Scene Set + Scene Metadata Stage

## Public API

```python
from context_pad.core.set_registry import SetRegistry

sets = SetRegistry()

# Scene set operations
sets.list_scene_sets()
sets.select_set("TailSet")
sets.replace_with_set("TailSet")
sets.add_set_to_selection("TailSet")
sets.remove_set_from_selection("TailSet")
sets.create_set_from_selection("TailSet")
sets.update_set_from_selection("TailSet")
sets.rename_set("TailSet", "TailSet_New")
sets.delete_set("TailSet_New")
sets.get_sets_for_object("tail_ctrl_01")
sets.get_set_size("TailSet")
sets.get_related_sets_for_selection(require_all=True)

# Scene-local UI metadata operations
sets.ensure_scene_meta_node()
sets.load_scene_set_ui_state()
sets.save_scene_set_ui_state({})
sets.cleanup_missing_set_metadata()
sets.refresh_scene_set_ui_state()
```

## Scene-local metadata sample structure

```python
{
    "TailSet": {
        "display_order": 10,
        "button_color": "#5D82A8",
        "group": "Tail",
        "hidden_state": False,
    },
    "AllCtrls_Set": {
        "display_order": 999,
        "button_color": "#6B7280",
        "group": "Global",
        "hidden_state": False,
    },
}
```

Stored on a dedicated Maya `network` node (`ContextPadSceneMeta`) as JSON string attr `cp_set_ui_state`.

## Temporary harness

```python
from context_pad.core.set_registry_harness import run_set_registry_demo
print(run_set_registry_demo("ContextPad_TestSet"))
```

## Copy-paste Maya snippets

### Create metadata node
```python
from context_pad.core.set_registry import SetRegistry
print(SetRegistry().ensure_scene_meta_node())
```

### Change display order
```python
from context_pad.core.set_registry import SetRegistry
reg = SetRegistry()
state = reg.load_scene_set_ui_state()
state.setdefault("TailSet", {})["display_order"] = 10
reg.save_scene_set_ui_state(state)
```

### Change color
```python
from context_pad.core.set_registry import SetRegistry
reg = SetRegistry()
state = reg.load_scene_set_ui_state()
state.setdefault("TailSet", {})["button_color"] = "#4A90E2"
reg.save_scene_set_ui_state(state)
```

### Change group
```python
from context_pad.core.set_registry import SetRegistry
reg = SetRegistry()
state = reg.load_scene_set_ui_state()
state.setdefault("TailSet", {})["group"] = "Tail"
reg.save_scene_set_ui_state(state)
```

### Hide/unhide set
```python
from context_pad.core.set_registry import SetRegistry
reg = SetRegistry()
state = reg.load_scene_set_ui_state()
state.setdefault("TailSet", {})["hidden_state"] = True   # False to unhide
reg.save_scene_set_ui_state(state)
```

### Related sets query for current selection
```python
from context_pad.core.set_registry import SetRegistry
print(SetRegistry().get_related_sets_for_selection())
```

## Manual validation scenario (step-by-step)

1. Select objects in Maya.
2. Create `TailSet`: `create_set_from_selection("TailSet")`.
3. Select all controls and create `AllCtrls_Set`.
4. Edit metadata for both sets (`display_order`, `button_color`, `group`, `hidden_state`).
5. Save scene.
6. Reopen scene.
7. Run `load_scene_set_ui_state()` and confirm order/color/group/hidden state values are preserved.
8. Delete one set (for example `TailSet`).
9. Run `refresh_scene_set_ui_state()`.
10. Confirm stale metadata for deleted set is cleaned.
11. Select one tail control and run `get_related_sets_for_selection()`.
12. Confirm returned sets are ordered for future launcher usage by:
    - smaller set size first,
    - then metadata `display_order`,
    - then set name.

## Expected result

- Scene set operations work through a UI-independent API.
- Scene-local UI metadata is saved in Maya scene and survives save/reopen.
- Missing metadata falls back to defaults automatically.
- Deleted sets do not leave stale metadata forever after refresh.
- Related set results are ready for future UI sorting behavior.

## Known limitations of this stage

- No full set launcher UI hookup yet.
- No drag-and-drop ordering UI yet.
- Metadata schema migration/versioning is basic.
- Related sorting currently uses size + display_order + name only.
