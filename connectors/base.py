from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Mapping

class SensorConnector(ABC):
    @abstractmethod
    def read(self) -> Iterable[Mapping[str, float]]:
        """Return rows keyed by configured sensor names."""
        raise NotImplementedError
