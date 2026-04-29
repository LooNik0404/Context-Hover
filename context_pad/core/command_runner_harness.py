"""Temporary execution harness for Context Pad command runner tests."""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any, Dict, List

from .command_runner import run_button_action


def build_demo_payloads(base_dir: str | None = None) -> List[Dict[str, Any]]:
    """Build demo payloads for all supported command types."""

    root = Path(base_dir or Path(tempfile.gettempdir()) / "context_pad_exec_demo")
    root.mkdir(parents=True, exist_ok=True)

    py_file = root / "demo_action.py"
    py_file.write_text('print("[ContextPadDemo] Python file ran")\n', encoding="utf-8")

    mel_file = root / "demo_action.mel"
    mel_file.write_text('print "[ContextPadDemo] MEL file ran\\n";\n', encoding="utf-8")

    return [
        {
            "label": "Py Inline Demo",
            "type": "python_inline",
            "code": 'print("[ContextPadDemo] Python inline ran")',
        },
        {
            "label": "Py File Demo",
            "type": "python_file",
            "file_path": str(py_file),
        },
        {
            "label": "MEL Inline Demo",
            "type": "mel_inline",
            "code": 'print "[ContextPadDemo] MEL inline ran\\n";',
        },
        {
            "label": "MEL File Demo",
            "type": "mel_file",
            "file_path": str(mel_file),
        },
        {
            "label": "Missing File Demo",
            "type": "python_file",
            "file_path": str(root / "does_not_exist.py"),
        },
        {
            "label": "Broken Python Demo",
            "type": "python_inline",
            "code": "for i in range(3) print(i)",
        },
    ]


def run_demo_execution_tests(base_dir: str | None = None) -> Dict[str, bool]:
    """Run demo execution cases and return pass/fail by label."""

    results: Dict[str, bool] = {}
    for payload in build_demo_payloads(base_dir=base_dir):
        label = str(payload.get("label", payload.get("type", "unknown")))
        results[label] = run_button_action(payload)
    return results
