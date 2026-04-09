# Context Pad v1 Hardening Notes

## Bootstrap callables (hotkey-safe entry points)

Use these in Maya `nameCommand` and hotkeys:

```python
from context_pad.bootstrap import show_script_launcher
show_script_launcher()
```

```python
from context_pad.bootstrap import show_set_launcher
show_set_launcher()
```

```python
from context_pad.bootstrap import show_manager_window
show_manager_window()
```

## Recommended Maya nameCommand / hotkey approach

Example pattern (edit names/keys as needed):

```python
import maya.cmds as cmds

cmd_name = "ContextPadShowSetLauncherCmd"
if not cmds.runTimeCommand(cmd_name, exists=True):
    cmds.runTimeCommand(
        cmd_name,
        commandLanguage="python",
        command="from context_pad.bootstrap import show_set_launcher; show_set_launcher()",
        category="User",
    )

name_cmd = "ContextPadShowSetLauncherNameCmd"
if not cmds.nameCommand(name_cmd, exists=True):
    cmds.nameCommand(name_cmd, command=cmd_name, annotation="Show Context Pad Set Launcher")

# Assign in your hotkey set from Maya Hotkey Editor using nameCommand.
```

## Stability and lifecycle hardening applied

- Added `show_manager_window()` singleton bootstrap path.
- Added deleted-widget safety checks before reusing cached launcher/manager instances.
- Script launcher manifest load now logs readable warnings and safely falls back.
- Set launcher RMB actions are exception-guarded with readable warnings.
- Related refresh remains active only while launcher is open + pinned.
- Command execution is wrapped in safe Maya undo chunks when available.

## Stress-test checklist

- Open/close Script Launcher 20 times.
- Open/close Set Launcher 20 times.
- Toggle pinned/unpinned repeatedly while using launcher.
- Run valid and invalid script actions.
- Test in scene with sets.
- Test in scene without sets.
- Test Related Sets with empty, single, multi-selection.
- Test plus icon set creation with valid/empty selection.
- Test RMB menu actions on set buttons.
- Test bad manifest/library path handling.
- Test missing script file handling.
- Confirm no related-set refresh activity remains after launcher close.

## Short code review summary

### Issues found
- Raw hex codes in set color menu reduced usability.
- New set colors were random and could clump visually.
- Singleton reuse could break when Qt widgets had been deleted.
- Script launcher swallowed non-validation load failures silently.
- Action failures in set RMB flow could bubble up without clear context.

### Concrete fixes applied
- Named set colors in UI picker.
- Balanced auto-color assignment for new sets.
- Singleton-alive checks in bootstrap.
- Added `show_manager_window` callable.
- Added warning logging around launcher data load and set RMB actions.
- Added undo chunk wrapper in script execution service.

### Remaining known risks
- No dedicated automated Maya integration test suite yet.
- Related refresh currently uses timer polling while pinned.
- Set color balancing is heuristic (best-effort, not strict adjacency graph).

## Expected result (v1 complete)

A technical animator should be able to:
- open manager, script launcher, and set launcher reliably from hotkeys,
- edit and run script buttons safely,
- manage sets directly from hover quickly,
- pin and move launcher as needed,
- recover gracefully from invalid paths/actions without tool collapse.

## Known limitations of this stage

- Requires Maya runtime for full set and MEL behavior.
- Related updates are polling-based while pinned.
- No formal CI for Maya UI interactions in this stage.


## Press/Release hotkey snippets (hold-to-show)

### Script hover
Press command:
```python
from context_pad.bootstrap import show_script_launcher
show_script_launcher()
```
Release command:
```python
from context_pad.bootstrap import hide_script_launcher
hide_script_launcher()
```

### Set hover
Press command:
```python
from context_pad.bootstrap import show_set_launcher
show_set_launcher()
```
Release command:
```python
from context_pad.bootstrap import hide_set_launcher
hide_set_launcher()
```

`hide_*` keeps pinned launchers visible and closes only unpinned launchers.
