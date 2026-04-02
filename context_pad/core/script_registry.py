"""Registry abstraction for globally stored scripts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ScriptEntry:
    """Data object describing a script button entry."""

    script_id: str
    label: str
    language: str
    category_id: str


class ScriptRegistry:
    """Read-only placeholder registry for script entries."""

    def list_scripts(self) -> List[ScriptEntry]:
        """Return all registered script entries."""

        return []

    def by_category(self, category_id: str) -> Iterable[ScriptEntry]:
        """Return scripts for a category id."""

        return [entry for entry in self.list_scripts() if entry.category_id == category_id]
