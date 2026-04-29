"""JSON I/O utilities for Context Pad manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON object from disk."""

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    """Save a JSON object to disk using stable formatting."""

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
