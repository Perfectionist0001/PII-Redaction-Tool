"""Email address PII detector using compiled regex."""

import re
from typing import List

from src.detectors.base import BaseDetector
from src.models import PIIEntity, TextChunk


class EmailDetector(BaseDetector):
    """Detector for identifying email addresses in text chunks."""

    # Compiled regex pattern for standard email addresses
    EMAIL_REGEX = re.compile(
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
    )

    @property
    def detector_name(self) -> str:
        """Name of the detector."""
        return "email_regex_detector"

    @property
    def supported_entity_types(self) -> List[str]:
        """Supported PII categories."""
        return ["EMAIL"]

    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect email addresses in a given TextChunk.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of detected PIIEntity objects for email addresses.
        """
        entities: List[PIIEntity] = []
        text = chunk.text

        if not text:
            return entities

        for match in self.EMAIL_REGEX.finditer(text):
            matched_text = match.group()
            start = match.start()
            end = match.end()

            # Strip trailing punctuation if present
            while matched_text and matched_text[-1] in ".,;:!?)'\"]":
                matched_text = matched_text[:-1]
                end -= 1

            if not matched_text:
                continue

            entities.append(
                PIIEntity(
                    entity_type="EMAIL",
                    original_text=matched_text,
                    start=start,
                    end=end,
                    confidence=1.0,
                    detector=self.detector_name,
                    source_location=chunk.source_location,
                )
            )

        return entities
