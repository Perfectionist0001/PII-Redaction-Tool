"""Date of Birth (DOB) PII detector using strict contextual triggers."""

import re
from typing import List

from src.detectors.base import BaseDetector
from src.models import PIIEntity, TextChunk


class DOBDetector(BaseDetector):
    """Detector for identifying Date of Birth (DOB) entities via contextual triggers."""

    # Explicit DOB context prefix triggers (e.g. "DOB:", "Date of Birth:", "Born on")
    DOB_CONTEXT_REGEX = re.compile(
        r"(?i)\b(?:DOB|D\.O\.B|Date\s+of\s+Birth|Birth\s*Date|Born\s+on|Born)[:\s]+"
    )

    # Date formats following a DOB trigger
    DATE_PATTERNS = [
        # Numeric formats: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD.MM.YYYY
        re.compile(r"\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b"),
        re.compile(r"\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b"),
        # Textual month formats: 15 August 1998, 15 Aug 1998
        re.compile(
            r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b",
            re.IGNORECASE,
        ),
        # Textual month formats: August 15, 1998, Aug 15 1998
        re.compile(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b",
            re.IGNORECASE,
        ),
    ]

    @property
    def detector_name(self) -> str:
        """Detector name."""
        return "dob_context_detector"

    @property
    def supported_entity_types(self) -> List[str]:
        """Supported PII categories."""
        return ["DOB"]

    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect Date of Birth (DOB) entities in a given TextChunk.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of detected PIIEntity objects for valid DOBs.
        """
        entities: List[PIIEntity] = []
        text = chunk.text

        if not text:
            return entities

        # Search for explicit DOB context triggers
        for trigger_match in self.DOB_CONTEXT_REGEX.finditer(text):
            trigger_end = trigger_match.end()
            # Look at text immediately following the trigger (up to 35 chars)
            remainder = text[trigger_end : trigger_end + 35]

            for pattern in self.DATE_PATTERNS:
                date_match = pattern.search(remainder)
                if date_match:
                    matched_date = date_match.group()
                    abs_start = trigger_end + date_match.start()
                    abs_end = trigger_end + date_match.end()

                    entities.append(
                        PIIEntity(
                            entity_type="DOB",
                            original_text=matched_date,
                            start=abs_start,
                            end=abs_end,
                            confidence=0.98,
                            detector=self.detector_name,
                            source_location=chunk.source_location,
                        )
                    )
                    break  # Found date for this trigger

        return entities
