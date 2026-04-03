# Context Pad Set Launcher — Final Hover Workflow

## Open Set Launcher (Maya Script Editor, Python tab)

```python
from context_pad.bootstrap import show_set_launcher
show_set_launcher()
```

## Final Set Launcher workflow

The Set Launcher is now the primary place for fast set work:

- **Top utility row (compact icons)**
  - Pin / Unpin
  - `+` create set from current selection
  - manager utility icon (secondary)
  - pinned hover can be dragged by top bar
- **Left rail: Related Sets** (contextual shortcuts)
- **Right side: All Sets** (full, stable list)

### Related Sets behavior

- Empty selection: related rail stays hidden/minimized.
- Single selection: shows sets containing that object.
- Multi-selection: shows sets containing **all** selected objects.
- Sorting:
  1. smaller sets first (more specific)
  2. then `display_order`
  3. then name
- Related list is limited to top 7 for speed and readability.

### All Sets behavior

- Always shows full list (except hidden sets).
- Uses scene metadata for:
  - color (`button_color`)
  - hidden state (`hidden_state`)
  - order (`display_order`)
  - grouping (`group`) for stable sorting
- List is scrollable while utility row stays fixed.

### Set button interactions

- **LMB**: select that set
- **RMB context menu** (launcher stays open while using menu):
  - Rename
  - Delete
  - Change Color (limited palette)
  - Update from Selection

### Fast create behavior

- `+` creates a set from current selection.
- Empty selection shows readable feedback.
- Uses a quick naming flow with suggested names.
- New sets get a random color from a fixed approved color palette.

### Pinned refresh behavior

- Related set auto-refresh runs only when launcher is:
  - visible, and
  - pinned.
- Closing launcher stops this logic fully.
- No permanent background watcher is created.

## Why set management now lives in hover

Set work is a rapid scene interaction task. Keeping create/rename/update/delete directly in the hover avoids context switching to manager forms and matches animator workflow speed.

## Manual validation checklist

- Open set launcher with nothing selected → only All Sets is visible or Related Sets is minimized.
- Select one object from TailSet → Related Sets appears.
- TailSet appears above AllCtrls_Set.
- Select multiple objects → only sets containing all objects remain.
- Click plus icon with selection → a new set is created.
- Click plus icon with empty selection → readable warning.
- RMB on a set button → context menu appears.
- Rename works.
- Delete works.
- Change Color works.
- Update from Selection works.
- Pin launcher → change selection → Related Sets updates while pinned.
- Close launcher → no background update logic remains active.

## Expected result

A compact translucent hover launcher supports complete day-to-day set operations directly in scene context, with fast contextual related-set shortcuts and stable all-set access.

## Known limitations of this stage

- Related updates use lightweight timer polling while pinned (not Maya callback events).
- Color choice uses a fixed quick-pick palette (no free color wheel in this stage).
- Grouping is reflected through sort order, not dedicated visual group headers.
- Outside Maya, set actions safely no-op.
