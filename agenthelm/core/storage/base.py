from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseStorage(ABC):
    """Abstract base class for trace storage backends."""

    @abstractmethod
    def save(self, event: Dict[str, Any]) -> None:
        """Save a single trace event."""
        pass

    @abstractmethod
    def load(self) -> List[Dict[str, Any]]:
        """Load all trace events."""
        pass

    def query(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Optional: Query traces with filters."""
        return self.load()
