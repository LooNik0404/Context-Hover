"""Shared in-memory state objects for UI and services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AppState:
    """Simple application state container used across UI components."""

    is_pinned: bool = False
    active_category: str = ""
    preferences: Dict[str, str] = field(default_factory=dict)
