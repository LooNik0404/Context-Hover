# Context Pad UI Stage 1 — Maya Test Notes

## Script Editor / Shelf snippets

### Open script launcher
```python
from context_pad.bootstrap import show_script_launcher
show_script_launcher()
```

### Open set launcher
```python
from context_pad.bootstrap import show_set_launcher
show_set_launcher()
```

## Manual validation checklist

1. Run `show_script_launcher()` and confirm it opens near your mouse cursor.
2. Run `show_script_launcher()` multiple times and confirm no duplicate script launcher windows appear.
3. Press `ESC` while launcher has focus and confirm it closes.
4. Click different categories and confirm right-side buttons change by category.
5. Confirm button labels are readable and button colors are visible.
6. Confirm top pin zone is visible and pin button text toggles between pinned/unpinned.
7. Reopen and close repeatedly (script and set launchers) and confirm no Script Editor errors.

## Expected result

You should see a compact translucent square launcher with rounded corners, a top pin strip, category list on the left, and a colored button grid on the right. Script launcher should show 3 categories and 6 total placeholders. Set launcher should show 3 placeholder set buttons.

## Known limitations of this stage

- Button clicks are placeholders only; no script execution is implemented.
- Scene set buttons are demo data only; no scene reading/writing is implemented.
- Pin state is runtime-only and is not persisted.
- Manager window integration is not expanded beyond scaffold behavior.
