"""Registry abstraction for scene-local selection sets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class SetEntry:
    """Data object describing a scene set launcher item."""

    set_id: str
    label: str
    category_id: str


class SetRegistry:
    """Read-only placeholder registry for scene set entries."""

    def list_sets(self) -> List[SetEntry]:
        """Return all scene set entries."""

        return []

    def by_category(self, category_id: str) -> Iterable[SetEntry]:
        """Return set entries for a category id."""

        return [entry for entry in self.list_sets() if entry.category_id == category_id]
