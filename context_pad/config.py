"""Configuration and user-data path helpers for Context Pad."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict

try:
    import maya.cmds as cmds  # type: ignore
except Exception:  # pragma: no cover - outside Maya
    cmds = None


PACKAGE_ROOT = Path(__file__).resolve().parent
PACKAGE_MANIFEST_ROOT = PACKAGE_ROOT / "manifest"

_USER_FOLDER_NAME = "ContextPadData"
_CONFIG_FILENAME = "config.json"
_MANIFEST_FILENAME = "manifest.json"


@dataclass(frozen=True)
class ContextPadConfig:
    """Container for top-level configuration values used by the tool."""

    tool_name: str = "Context Pad"
    schema_version: int = 1
    manifest_filename: str = _MANIFEST_FILENAME
    package_manifest_root: Path = PACKAGE_MANIFEST_ROOT


DEFAULT_CONFIG = ContextPadConfig()


def get_user_data_root() -> Path:
    """Return Context Pad user-data folder rooted in Maya user area."""

    return resolve_writable_user_data_root()


def get_user_data_candidates() -> list[Path]:
    """Return ordered candidate roots for user-editable Context Pad data."""

    candidates: list[Path] = []
    if cmds is not None:
        try:
            scripts_dir = str(cmds.internalVar(userScriptDir=True) or "").strip()
            if scripts_dir:
                candidates.append(Path(scripts_dir).expanduser().resolve() / _USER_FOLDER_NAME)
        except Exception:
            pass
        try:
            app_dir = str(cmds.internalVar(userAppDir=True) or "").strip()
            if app_dir:
                candidates.append(Path(app_dir).expanduser().resolve() / _USER_FOLDER_NAME)
        except Exception:
            pass
    candidates.append(Path.home() / "maya" / _USER_FOLDER_NAME)
    candidates.append(Path.home() / ".context_pad_data")

    deduped: list[Path] = []
    seen: set[str] = set()
    for item in candidates:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def resolve_writable_user_data_root() -> Path:
    """Resolve first writable user-data root using preferred + fallback candidates."""

    errors: list[str] = []
    for candidate in get_user_data_candidates():
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            _assert_path_writable(candidate)
            return candidate
        except Exception as exc:
            errors.append(f"{candidate} ({exc})")
    raise RuntimeError("Could not resolve writable Context Pad user-data root. Tried: " + "; ".join(errors))


def get_user_config_path() -> Path:
    """Return user config.json path."""

    return get_user_data_root() / _CONFIG_FILENAME


def get_default_user_manifest_path() -> Path:
    """Return default manifest location in user data."""

    return get_user_data_root() / _MANIFEST_FILENAME


def default_user_config_payload() -> Dict[str, Any]:
    """Return default user config payload."""

    manifest_path = str(get_default_user_manifest_path())
    return {
        "schema_version": DEFAULT_CONFIG.schema_version,
        "tool_name": DEFAULT_CONFIG.tool_name,
        "active_manifest_path": manifest_path,
    }


def ensure_user_data_layout() -> Dict[str, Path]:
    """Ensure user data folder/config/manifest exist; copy defaults on first run."""

    user_root = resolve_writable_user_data_root()

    config_path = get_user_config_path()
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            config_path.write_text(json.dumps(default_user_config_payload(), indent=2), encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Could not create config '{config_path}': {exc}") from exc

    manifest_path = get_default_user_manifest_path()
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        if not manifest_path.exists():
            package_manifest = DEFAULT_CONFIG.package_manifest_root / DEFAULT_CONFIG.manifest_filename
            if package_manifest.exists():
                manifest_path.write_text(package_manifest.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                manifest_path.write_text('{"version": 1, "categories": [], "buttons": [], "submenus": []}', encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Could not create manifest '{manifest_path}': {exc}") from exc

    return {
        "user_root": user_root,
        "config_path": config_path,
        "manifest_path": manifest_path,
    }


def _assert_path_writable(path: Path) -> None:
    """Raise when path cannot be written to."""

    test_file = path / ".context_pad_write_test"
    test_file.write_text("ok", encoding="utf-8")
    test_file.unlink(missing_ok=True)


def load_user_config() -> Dict[str, Any]:
    """Load user config payload with safe defaults."""

    ensure_user_data_layout()
    config_path = get_user_config_path()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    payload = default_user_config_payload()
    save_user_config(payload)
    return payload


def save_user_config(payload: Dict[str, Any]) -> None:
    """Save user config payload."""

    ensure_user_data_layout()
    config_path = get_user_config_path()
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_active_manifest_path() -> Path:
    """Return current active manifest path from user config."""

    payload = load_user_config()
    configured = str(payload.get("active_manifest_path", "")).strip()
    candidate = Path(configured).expanduser() if configured else get_default_user_manifest_path()
    if candidate.exists():
        return candidate
    fallback = get_default_user_manifest_path()
    if not fallback.exists():
        ensure_user_data_layout()
    return fallback
