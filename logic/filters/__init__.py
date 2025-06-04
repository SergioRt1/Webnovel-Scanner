from abc import ABC, abstractmethod

from logic.entities import Novel

class ContentFilter(ABC):
    @abstractmethod
    def filter_content(self, novel: Novel, threshold: float = 0.75):
        pass