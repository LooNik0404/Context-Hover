# Context Pad UI Refinement Notes

## 1) Intended visual hierarchy (concise)

1. **Body shell first**: compact translucent charcoal surface with rounded corners and minimal border.
2. **Utility controls second**: tiny top-right icon controls for low-noise access.
3. **Primary action content third**: left contextual rail + right action area with top-aligned click targets.
4. **Color and labels fourth**: muted button colors with automatic text contrast for readability.

## 2) Script Launcher layout

- Left: narrow **Categories** rail.
- Center: subtle thin vertical divider.
- Right: compact 2-column action grid, top-aligned.
- No large title strip; utility icons stay in compact top-right area.

## 3) Set Launcher layout

- Left: narrow **Related** button rail for contextual quick sets.
- Center: subtle divider.
- Right: stable **All Sets** button area in compact 2-column top-aligned grid.
- Left is contextual shortcuts, right is full/primary action area.
- Utility row uses only **add + pin** (no manager `⋯`) for cleaner set-focused UX.

## 4) Specific UI changes from previous implementation

- Removed large pin text button and replaced with tiny dot icon state (`○` unpinned / `●` pinned).
- Removed large title header block to recover vertical action space.
- Added icon-style utility controls with per-launcher visibility:
  - Script launcher: add (`+`), manager (`⋯`), pin.
  - Set launcher: add (`+`), pin.
- Reduced heavy nested-panel feeling with transparent left lists and light divider.
- Enforced top alignment in grids and added compact spacing rhythm.
- Added automatic button text contrast based on button color luminance.

## 5) Code/UI structure updates supporting the design

- `PinZone` now acts as a utility bar with three icon controls and signals for future hooks.
- `LauncherBase` now exposes lightweight extension points:
  - replaceable left widget (`set_left_widget`)
  - configurable button columns (`set_button_columns`)
  - placeholder callbacks (`on_add_requested`, `on_manager_requested`)
- Added `RelatedSetsList` widget so Set Launcher can use contextual left-column buttons without reworking core architecture.

## 6) Hold-to-show hotkey workflow (manual Hotkey Editor setup)

Context Pad does **not** auto-assign Maya hotkeys in code. Configure in Maya **Hotkey Editor** with press/release runtime commands.

### Script launcher

- **Press command** (Python):
  `import context_pad; context_pad.show_script_launcher()`
- **Release command** (Python):
  `import context_pad; context_pad.hide_script_launcher()`

### Set launcher

- **Press command** (Python):
  `import context_pad; context_pad.show_set_launcher()`
- **Release command** (Python):
  `import context_pad; context_pad.hide_set_launcher()`

Result: overlay appears while the key is held, then hides on key release (unless pinned).
