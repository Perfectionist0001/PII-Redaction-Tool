"""Base interface and protocol for PII detectors."""

from abc import ABC, abstractmethod
from typing import List

from src.models import PIIEntity, TextChunk


class BaseDetector(ABC):
    """Abstract Base Class defining the contract for all PII detectors."""

    @property
    @abstractmethod
    def detector_name(self) -> str:
        """Unique identifier name of the detector."""
        pass

    @property
    @abstractmethod
    def supported_entity_types(self) -> List[str]:
        """List of entity categories supported by this detector."""
        pass

    @abstractmethod
    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect PII entities within a given text chunk.

        Args:
            chunk: TextChunk containing document text and source location metadata.

        Returns:
            List of detected PIIEntity objects.
        """
        pass
