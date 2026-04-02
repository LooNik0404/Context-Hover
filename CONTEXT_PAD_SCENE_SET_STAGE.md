# Context Pad Scene Set Support Stage

## Public API (data/service layer)

```python
from context_pad.core.set_registry import SetRegistry

sets = SetRegistry()
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
```

## Temporary harness

```python
from context_pad.core.set_registry_harness import run_set_registry_demo
print(run_set_registry_demo("ContextPad_TestSet"))
```

## Copy-paste Maya snippets

### Create set from current selection
```python
from context_pad.core.set_registry import SetRegistry
SetRegistry().create_set_from_selection("TailSet")
```

### Select a set
```python
from context_pad.core.set_registry import SetRegistry
SetRegistry().select_set("TailSet")
```

### Update a set from current selection
```python
from context_pad.core.set_registry import SetRegistry
SetRegistry().update_set_from_selection("TailSet")
```

### Rename a set
```python
from context_pad.core.set_registry import SetRegistry
SetRegistry().rename_set("TailSet", "TailSet_New")
```

### Delete a set
```python
from context_pad.core.set_registry import SetRegistry
SetRegistry().delete_set("TailSet_New")
```

### Query related sets for current selection
```python
from context_pad.core.set_registry import SetRegistry
print(SetRegistry().get_related_sets_for_selection())
```

## Manual validation scenario (step-by-step)

1. Select several tail controls.
2. Run `create_set_from_selection("TailSet")`.
3. Select all controls in rig and run `create_set_from_selection("AllCtrls_Set")`.
4. Clear selection.
5. Select one tail control.
6. Run related query: `get_related_sets_for_selection()`.
7. Confirm both `TailSet` and `AllCtrls_Set` are returned.
8. Select several tail controls.
9. Run related query again and confirm only sets containing **all selected controls** are returned when `require_all=True`.
10. Save scene.
11. Reopen scene.
12. Run `list_scene_sets()` and confirm created sets still exist.

## Expected result

- Set operations complete safely and return booleans.
- Missing sets / empty selection are handled with readable warnings.
- Related set query returns smaller/more specific sets first.
- API remains UI-independent and ready for future set launcher hookup.

## Known limitations of this stage

- No dedicated set launcher UI binding yet.
- No set metadata/category tagging yet.
- No manager editing workflow for sets yet.
- Sorting uses set size + name only (no custom priority weights yet).
