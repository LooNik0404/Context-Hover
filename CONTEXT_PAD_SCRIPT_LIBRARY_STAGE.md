# Context Pad Script Library Registry Stage

## Public API

```python
from context_pad.core.script_registry import ScriptRegistry

registry = ScriptRegistry()
registry.load_manifest("context_pad/manifest/manifest.json")
categories = registry.get_categories()
buttons = registry.get_buttons_for_category("anim")
```

Methods:
- `load_manifest(path=None)`
- `validate_manifest(data)`
- `get_categories()`
- `get_buttons_for_category(category_id)`

## Required vs optional fields

### Category fields
Required:
- `id` (stable unique id)
- `label`
- `sort_order`

Optional:
- `color` (defaults to `#6B7280` in parsed output)

### Button fields
Required:
- `id` (stable unique id)
- `label`
- `category_id` (must reference existing category id)
- `color`
- `action_type` (`python_inline`, `python_file`, `mel_inline`, `mel_file`)
- `source`
- `tooltip`
- `sort_order`

Optional:
- `submenu_id` (validation-only for now; must exist in `submenus` when provided)

### Submenu fields (validation/data only)
Required:
- `id`
- `label`

## Sample manifests

- Valid sample: `context_pad/manifest/manifest.json`
- Intentionally broken sample: `context_pad/manifest/manifest_broken.json`

## Harness / usage example

```python
from context_pad.core.script_registry_harness import run_registry_demo

result = run_registry_demo()
print("valid_ok:", result["valid_ok"])
print("categories:", [c["label"] for c in result["categories"]])
print("anim buttons:", [b["label"] for b in result["buttons_by_category"]["anim"]])
print("broken_error:", result["broken_error"])
```

## Copy-paste snippets

### Plain Python (recommended for this stage)

```python
from context_pad.core.script_registry import ScriptRegistry, ManifestValidationError

registry = ScriptRegistry()
registry.load_manifest("context_pad/manifest/manifest.json")
print(registry.get_categories())
print(registry.get_buttons_for_category("anim"))

try:
    registry.load_manifest("context_pad/manifest/manifest_broken.json")
except ManifestValidationError as exc:
    print("Validation error:", exc)
```

### Maya Script Editor (Python tab)

```python
from context_pad.core.script_registry import ScriptRegistry

registry = ScriptRegistry()
registry.load_manifest()  # default: context_pad/manifest/manifest.json
for category in registry.get_categories():
    print(category["label"], "->", [b["label"] for b in registry.get_buttons_for_category(category["id"])])
```

## Manual validation checklist

1. Valid manifest loads without error.
2. Invalid manifest raises readable `ManifestValidationError`.
3. Categories return in expected `sort_order`.
4. Buttons return by category and preserve `sort_order`.
5. Optional submenu references validate only at data level.

## Expected result

- Launcher-facing data is now disk-driven and UI-independent.
- Registry returns stable category/button structures ready for UI consumption.
- Broken manifests fail early with clear messages.

## Known limitations of this stage

- No UI submenu rendering yet.
- No manager editing workflow yet.
- No manifest auto-reload/watch yet.
- No schema version migration logic yet.
