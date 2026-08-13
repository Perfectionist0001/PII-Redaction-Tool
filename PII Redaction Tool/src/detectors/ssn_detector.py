"""Social Security Number (SSN) PII detector using regex and structural rules."""

import re
from typing import List

from src.detectors.base import BaseDetector
from src.models import PIIEntity, TextChunk


class SSNDetector(BaseDetector):
    """Detector for identifying US Social Security Numbers (SSNs)."""

    # Strict SSN regex pattern NNN-NN-NNNN
    SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    @property
    def detector_name(self) -> str:
        """Detector name."""
        return "ssn_regex_detector"

    @property
    def supported_entity_types(self) -> List[str]:
        """Supported PII categories."""
        return ["SSN"]

    def _is_valid_ssn(self, ssn_str: str) -> bool:
        """Validate SSN area, group, and serial number rules."""
        parts = ssn_str.split("-")
        if len(parts) != 3:
            return False

        area, group, serial = parts[0], parts[1], parts[2]

        # Area number rules: cannot be 000, 666, or 900-999
        area_num = int(area)
        if area_num == 0 or area_num == 666 or 900 <= area_num <= 999:
            return False

        # Group number rules: cannot be 00
        if group == "00":
            return False

        # Serial number rules: cannot be 0000
        if serial == "0000":
            return False

        return True

    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect SSNs in a given TextChunk.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of detected PIIEntity objects for valid SSNs.
        """
        entities: List[PIIEntity] = []
        text = chunk.text

        if not text:
            return entities

        for match in self.SSN_REGEX.finditer(text):
            matched_str = match.group()

            if self._is_valid_ssn(matched_str):
                entities.append(
                    PIIEntity(
                        entity_type="SSN",
                        original_text=matched_str,
                        start=match.start(),
                        end=match.end(),
                        confidence=1.0,
                        detector=self.detector_name,
                        source_location=chunk.source_location,
                    )
                )

        return entities
