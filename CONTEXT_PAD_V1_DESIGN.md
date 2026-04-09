# Context Pad v1 — Production-Friendly Maya Tool Design

## 1) Proposed Folder Structure

```text
context_pad/
  __init__.py
  bootstrap.py                  # single entry-point called from Maya shelf/hotkey

  core/
    __init__.py
    constants.py                # names, version, default colors, file names
    logging.py                  # logger setup for Script Editor + optional file
    paths.py                    # user/global paths resolution (os-safe)
    compat.py                   # Maya/PySide compatibility helpers

  data/
    __init__.py
    models.py                   # dataclasses/dicts schema helpers
    json_store.py               # manifest read/write with validation
    scene_store.py              # objectSet + attrs read/write wrappers

  services/
    __init__.py
    script_library_service.py   # create/edit/delete categories+scripts on disk
    selection_set_service.py    # create/edit/delete scene selection sets
    execution_service.py        # run Python or MEL safely
    color_service.py            # normalize/convert/store colors

  ui/
    __init__.py
    style.py                    # shared Qt stylesheets + translucency constants
    widgets/
      __init__.py
      overlay_pad.py            # base square translucent launcher widget
      radial_or_grid_menu.py    # hover menu widget (grid recommended for v1)
      script_button.py          # color-coded script item button
      set_button.py             # color-coded selection set item button

    windows/
      __init__.py
      manager_window.py         # tabbed editor: Scripts + Selection Sets
      script_editor_panel.py    # edit categories/scripts metadata
      set_editor_panel.py       # edit scene sets metadata + capture selection

  resources/
    icons/
      context_pad.svg
      launcher_script.svg
      launcher_sets.svg

  tests/
    test_manifest_schema.py
    test_color_service.py
    test_execution_service.py

manifest/
  manifest.json                 # global script library index
  scripts/
    anim/
      bake_keys.py
      isolate_controls.mel

README.md
```

Notes:
- Keep the package importable even outside Maya for static checks and partial unit tests.
- `manifest/` can be relocated to studio path later via environment variable in `paths.py`.

---

## 2) Module Responsibilities

### `bootstrap.py`
- Initializes compatibility layer and Maya main-window parenting.
- Creates/reuses singleton overlays:
  - Script Launcher overlay
  - Selection Set Launcher overlay
- Creates/reuses manager window.
- Registers *minimal* lifecycle hooks (e.g., on scene open, refresh set cache once).

### `core/compat.py`
- Import strategy:
  1. Try `PySide2` + `shiboken2` (Maya 2022/2023 primary).
  2. Fallback scaffold for `PySide6` + `shiboken6`.
- Exposes unified names (`QtCore`, `QtGui`, `QtWidgets`, `wrapInstance`).
- Avoids PyMEL requirement by using `maya.cmds` + `maya.OpenMayaUI`.

### `data/json_store.py`
- Loads/saves `manifest.json` atomically (temp file + replace).
- Validates required fields, ids, and script file references.
- Handles schema version migration hooks.

### `data/scene_store.py`
- Reads/writes scene-local metadata to Maya object sets.
- Uses custom attrs on each managed set (e.g., `cp_label`, `cp_color`, `cp_category`).
- Provides safe creation/updating/deletion wrappers around `cmds.sets`, `cmds.addAttr`, `cmds.setAttr`.

### `services/script_library_service.py`
- CRUD for script categories and entries in manifest.
- Creates/removes script files in `manifest/scripts/...`.
- Ensures unique ids and stable ordering.

### `services/selection_set_service.py`
- Create set from current selection.
- Replace set membership from current selection.
- Recall/select set contents.
- Scene-scope only; no disk persistence for membership.

### `services/execution_service.py`
- Executes script button payload by type:
  - Python: `exec(compile(...))` in controlled namespace.
  - MEL: `maya.mel.eval(...)`.
- Captures errors and routes to Script Editor + optional UI toast.

### `ui/widgets/overlay_pad.py`
- Frameless, square, translucent, always-on-top tool window.
- Drag-move support and optional edge snapping.
- Click/hover behavior to open associated menu.
- Pin mode state + visual indicator.

### `ui/windows/manager_window.py`
- Non-overlay editor UI for content management.
- Tabs:
  - Global Script Library (disk)
  - Scene Selection Sets (scene)
- Includes color picker, category management, reorder controls.

---

## 3) Data Model for `manifest.json` (Global Script Library)

```json
{
  "schema_version": 1,
  "library_name": "Context Pad Global Library",
  "updated_utc": "2026-04-01T00:00:00Z",
  "categories": [
    {
      "id": "cat_anim",
      "name": "Animation",
      "color": "#4DA3FF",
      "order": 10,
      "enabled": true
    }
  ],
  "scripts": [
    {
      "id": "scr_bake_keys",
      "name": "Bake Keys",
      "category_id": "cat_anim",
      "language": "python",
      "source": {
        "mode": "file",
        "path": "scripts/anim/bake_keys.py"
      },
      "tooltip": "Bake selected controls to timeline range.",
      "button_color": "#2E7D32",
      "text_color": "#FFFFFF",
      "order": 100,
      "enabled": true,
      "tags": ["bake", "keys", "anim"]
    },
    {
      "id": "scr_isolate",
      "name": "Isolate Controls",
      "category_id": "cat_anim",
      "language": "mel",
      "source": {
        "mode": "file",
        "path": "scripts/anim/isolate_controls.mel"
      },
      "tooltip": "Toggle isolate select for control rigs.",
      "button_color": "#6A1B9A",
      "text_color": "#FFFFFF",
      "order": 110,
      "enabled": true,
      "tags": ["viewport", "isolate"]
    }
  ]
}
```

Rules:
- `id` fields must be stable and unique.
- `language` in `{ "python", "mel" }`.
- `source.mode` initially only `file` (non-goal: inline code editor in v1).
- Paths are relative to manifest root for portability.

---

## 4) Data Model for Scene-Local Set Metadata

Use native Maya `objectSet` nodes for membership (scene persistence), plus custom attrs for metadata.

### Node naming
- Suggested managed prefix: `CP_SET_<slug>`.
- Example: `CP_SET_face_controls`.

### Required custom attributes on each managed set
- `cp_id` (string) — stable UUID-like id.
- `cp_label` (string) — button display name.
- `cp_category` (string) — category key (e.g., `face`, `body`, `props`).
- `cp_color` (string) — hex color `#RRGGBB`.
- `cp_text_color` (string) — hex color.
- `cp_order` (long) — ordering index.
- `cp_enabled` (bool) — visible/active toggle.
- `cp_created_by` (string) — optional artist/tool signature.
- `cp_updated_utc` (string) — ISO timestamp.

### Optional scene-level aggregator node
- Network node: `CP_SCENE_META` with attrs:
  - `cp_schema_version` (long)
  - `cp_last_migrated_utc` (string)
- Used only for migration/versioning, not for set membership itself.

Why this model:
- Membership stays robust and native via `objectSet`.
- Metadata remains queryable via `cmds.ls(type='objectSet')` and attr checks.
- No external files needed for scene-specific sets.

---

## 5) Event Flow (Open / Hover / Execute / Pin / Close)

### A) Tool launch
1. User clicks shelf button `Context Pad`.
2. `bootstrap.launch()` resolves paths, loads manifest, scans scene sets.
3. Builds/refreshes two overlay pads:
   - Script Launcher
   - Selection Set Launcher
4. Pads appear in last saved screen positions.

### B) Open behavior
- Click pad (or configured hotkey) opens compact grid menu near pad.
- Menu content sourced from:
  - Script pad: `manifest.json`
  - Set pad: scene `objectSet` metadata

### C) Hover behavior
- Hover item highlights with subtle scale/opacity animation.
- Tooltip shows description, language/type, and optional tags.
- No polling loop; pure Qt enter/leave events.

### D) Execute behavior
- Script item click:
  1. Resolve script path from manifest.
  2. Read file contents.
  3. Dispatch by language to execution service.
  4. Report success/failure in Script Editor and optional status label.
- Selection set item click:
  1. Validate set exists.
  2. Select members via `cmds.select(set_members, r=True)`.
  3. Optionally frame selection (config toggle).

### E) Pin behavior
- Pin icon toggles `pinned=True` state per pad.
- Pinned pad keeps menu open until explicit close or execute (configurable).
- Unpinned pad auto-closes menu on focus out.

### F) Close behavior
- ESC closes open menu (not necessarily pad).
- Close button hides pad instance; relaunch restores.
- Manager window close does not destroy pads.

---

## 6) Non-Goals for v1

- No node-graph or marking-menu integration.
- No remote/cloud shared library sync.
- No per-shot permission system.
- No inline code editor with syntax highlighting.
- No automatic context inference (camera/character/task-based suggestions).
- No background idle refreshers or polling daemons.
- No PyMEL-only APIs.
- No animation-layer-aware smart execution wrappers (defer to v2).

---

## 7) Risks and Mitigation

1. **Qt compatibility drift (PySide2 vs future PySide6)**
   - Mitigation: centralize all Qt imports/types in `core/compat.py`; keep UI code alias-based.

2. **Maya crashes from unsafe script execution**
   - Mitigation: strict file-based scripts, pre-execution existence checks, try/except around runtime execution boundary, clear logging.

3. **Corrupt manifest due to abrupt writes**
   - Mitigation: atomic writes (`.tmp` then replace), JSON schema validation before save.

4. **Set metadata inconsistency in scene**
   - Mitigation: validation pass on manager open; missing attrs auto-healed; skip invalid sets safely.

5. **UI clutter on animator screens**
   - Mitigation: compact square pads, draggable placement, opacity control, per-pad visibility toggle.

6. **Name collisions with user-created sets**
   - Mitigation: managed prefix + `cp_id` attr marker; never assume name alone identifies managed set.

7. **Hand-off complexity for other artists/TDs**
   - Mitigation: clear modular package, docstrings, service boundaries, and small test suite around data/execution layers.
