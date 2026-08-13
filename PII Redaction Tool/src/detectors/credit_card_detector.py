"""Credit Card PII detector using regex candidates and Luhn checksum validation."""

import re
from typing import List

from src.detectors.base import BaseDetector
from src.models import PIIEntity, TextChunk


class CreditCardDetector(BaseDetector):
    """Detector for identifying credit card numbers validated via Luhn algorithm."""

    # Regex for candidate credit card numbers (13-19 digits with optional spaces or hyphens)
    CARD_CANDIDATE_REGEX = re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{1,7}\b|\b\d{13,19}\b"
    )

    @property
    def detector_name(self) -> str:
        """Detector name."""
        return "credit_card_luhn_detector"

    @property
    def supported_entity_types(self) -> List[str]:
        """Supported PII categories."""
        return ["CREDIT_CARD"]

    def _luhn_check(self, card_number_digits: str) -> bool:
        """Validate digit sequence using Luhn algorithm (mod 10)."""
        if not card_number_digits.isdigit():
            return False

        num_digits = len(card_number_digits)
        if num_digits < 13 or num_digits > 19:
            return False

        checksum = 0
        reverse_digits = [int(d) for d in reversed(card_number_digits)]

        for idx, digit in enumerate(reverse_digits):
            if idx % 2 == 1:
                doubled = digit * 2
                checksum += doubled - 9 if doubled > 9 else doubled
            else:
                checksum += digit

        return checksum % 10 == 0

    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect credit card numbers in a given TextChunk.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of detected PIIEntity objects for valid credit cards.
        """
        entities: List[PIIEntity] = []
        text = chunk.text

        if not text:
            return entities

        for match in self.CARD_CANDIDATE_REGEX.finditer(text):
            matched_str = match.group()

            # Normalize to digits only for Luhn verification
            digits_only = re.sub(r"\D", "", matched_str)

            # Skip if digit count is outside credit card range (13 to 19 digits)
            if len(digits_only) < 13 or len(digits_only) > 19:
                continue

            # Skip if matched text contains commas or decimals (financial amounts / share counts)
            if "," in matched_str or "." in matched_str:
                continue

            # Perform Luhn checksum validation
            if self._luhn_check(digits_only):
                entities.append(
                    PIIEntity(
                        entity_type="CREDIT_CARD",
                        original_text=matched_str,  # Retain original formatting
                        start=match.start(),
                        end=match.end(),
                        confidence=1.0,
                        detector=self.detector_name,
                        source_location=chunk.source_location,
                    )
                )

        return entities
