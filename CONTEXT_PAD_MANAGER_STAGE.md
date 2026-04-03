# Context Pad Manager Window Stage

## Open manager window (Maya Script Editor, Python tab)

```python
from context_pad.bootstrap import launch_context_pad
launch_context_pad()
```

## Complete usage path

1. Open manager.
2. In **Script Categories** click **Add** and create a category (example: `Custom`).
3. Select the new category.
4. In **Script Buttons** fill fields and click **Add** for a Python button:
   - Label: `Py Test`
   - Action Type: `python_inline`
   - Source: `print("Hello from Python")`
   - Pick color swatch.
5. Add a MEL button:
   - Label: `MEL Test`
   - Action Type: `mel_inline`
   - Source: `print "Hello from MEL\\n";`
   - Pick color swatch.
6. Use ↑/↓ controls to reorder category or buttons.
7. Click **Save Manifest**.
8. Open script launcher and confirm new buttons appear.
9. In **Scene Sets** section select a set and edit:
   - display order
   - color
   - group
   - hide/unhide
10. Click **Apply Set Metadata** and confirm saved state via refresh/reopen.

## Manual validation checklist

- Categories can be added / renamed / deleted.
- Buttons can be added / edited / deleted.
- Colors are selected visually via swatches.
- Order changes persist after save.
- Script launcher shows updated manifest-driven buttons after refresh/reopen.
- Set metadata can be edited without manual scene JSON editing.

## Expected result

- Non-programmer-friendly manager window allows editing categories/buttons and set UI metadata.
- Saved manifest changes are reflected in the launcher.
- Scene set metadata (order/color/group/hidden) persists in scene and can be refreshed.

## Known limitations of this stage

- No drag-and-drop ordering (up/down only).
- No advanced validation UI (errors shown in status label/exception text).
- No manager support for submenu editing yet.
- No dedicated set creation/deletion controls in manager section (scene ops remain API-level).
