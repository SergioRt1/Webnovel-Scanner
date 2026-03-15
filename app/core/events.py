from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class ProgressEvent:
    message: str
    current: int = 0
    total: int = 0

    @property
    def ratio(self) -> float:
        if self.total <= 0:
            return 0.0
        return self.current / self.total


ProgressCallback = Callable[[ProgressEvent], None]
