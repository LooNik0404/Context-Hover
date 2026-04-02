"""Command execution service for Context Pad button actions."""

from __future__ import annotations

from pathlib import Path
import traceback
from typing import Any, Dict, Optional

try:
    import maya.cmds as cmds  # type: ignore
except Exception:  # pragma: no cover - outside Maya
    cmds = None

try:
    import maya.mel as maya_mel  # type: ignore
except Exception:  # pragma: no cover - outside Maya
    maya_mel = None


def run_button_action(button_data: Dict[str, Any]) -> bool:
    """Execute a button action payload and return success status.

    Expected keys:
      - type: one of python_inline, python_file, mel_inline, mel_file
      - label: optional display name for logs
      - code: inline code string for *_inline
      - file_path: path string for *_file
    """

    action_type = str(button_data.get("type", "")).strip()
    label = str(button_data.get("label", action_type or "unnamed_action"))

    if not action_type:
        _log_error(f"Button '{label}' missing required field: type")
        return False

    try:
        if action_type == "python_inline":
            code = _required_string(button_data, "code")
            _log_info(f"Running Python inline action: {label}")
            _run_python(code, source_hint=f"inline:{label}")
            _log_info(f"Success: {label}")
            return True

        if action_type == "python_file":
            file_path = _existing_file(button_data)
            _log_info(f"Running Python file action: {label} -> {file_path}")
            _run_python(file_path.read_text(encoding="utf-8"), source_hint=str(file_path))
            _log_info(f"Success: {label}")
            return True

        if action_type == "mel_inline":
            code = _required_string(button_data, "code")
            _log_info(f"Running MEL inline action: {label}")
            _run_mel(code)
            _log_info(f"Success: {label}")
            return True

        if action_type == "mel_file":
            file_path = _existing_file(button_data)
            _log_info(f"Running MEL file action: {label} -> {file_path}")
            _run_mel(file_path.read_text(encoding="utf-8"))
            _log_info(f"Success: {label}")
            return True

        _log_error(f"Unsupported action type '{action_type}' for button '{label}'")
        return False

    except Exception as exc:
        _log_error(f"Failed: {label} | {exc}")
        _log_error(traceback.format_exc(limit=1).strip())
        return False


def _required_string(button_data: Dict[str, Any], key: str) -> str:
    """Return required non-empty string field from button payload."""

    value = str(button_data.get(key, "")).strip()
    if not value:
        raise ValueError(f"missing required field: {key}")
    return value


def _existing_file(button_data: Dict[str, Any]) -> Path:
    """Resolve and validate existing file path from button payload."""

    raw_path = _required_string(button_data, "file_path")
    file_path = Path(raw_path).expanduser()
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"file not found: {file_path}")
    return file_path


def _run_python(code: str, source_hint: str) -> None:
    """Execute Python code in a small controlled namespace."""

    namespace: Dict[str, Any] = {"__name__": "__context_pad_button__"}
    if cmds is not None:
        namespace["cmds"] = cmds
    if maya_mel is not None:
        namespace["mel"] = maya_mel
    exec(compile(code, source_hint, "exec"), namespace, namespace)


def _run_mel(code: str) -> None:
    """Execute MEL code through Maya mel module."""

    if maya_mel is None:
        raise RuntimeError("MEL execution unavailable outside Maya")
    maya_mel.eval(code)


def _log_info(message: str) -> None:
    """Write informational message to Script Editor safely."""

    print(f"[ContextPad] {message}")


def _log_error(message: str) -> None:
    """Write error message to Script Editor safely."""

    if cmds is not None:
        cmds.warning(f"[ContextPad] {message}")
    else:
        print(f"[ContextPad][ERROR] {message}")
