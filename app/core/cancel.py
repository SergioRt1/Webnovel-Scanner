from __future__ import annotations
from abc import ABC, abstractmethod

import threading


class TaskCancelledError(Exception):
    pass

class EventToken(ABC):
    @abstractmethod
    def is_cancelled(self):
        pass

    @abstractmethod
    def raise_if_cancelled(self):
        pass

class CancelToken(EventToken):
    def __init__(self):
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise TaskCancelledError("Process canceled by user.")

class NoopToken(EventToken):
    def is_cancelled(self) -> bool:
        return False

    def raise_if_cancelled(self) -> None:
        pass
