"""Indian Phone Number PII detector using regex and structural rules."""

import re
from typing import List, Tuple

from src.detectors.base import BaseDetector
from src.models import PIIEntity, TextChunk


class PhoneDetector(BaseDetector):
    """Detector for identifying Indian mobile and landline phone numbers."""

    # Regex for explicit phone labels preceding phone numbers
    LABEL_PREFIX_REGEX = re.compile(
        r"(?i)\b(?:Tel|Telephone|Phone|Mobile|Fax|Contact|Tel No|Fax No)[:\s]+"
    )

    # 1. International Indian format starting with +91 or + 91
    #    e.g. +91 9876543210, +91-9876543210, +91 20 45053237, + 91 (20) 6729 5100, +91 81081 14949
    PATTERN_PLUS91 = re.compile(
        r"\+\s*91[-\s]?(?:\(\d{2,4}\)|\d{2,4})?[-\s]?\d{3,5}[-\s]?\d{3,5}\b"
    )

    # 2. STD Landline numbers starting with 0
    #    e.g. 022-68052182, 020 67694648
    PATTERN_STD_LANDLINE = re.compile(
        r"\b0\d{2,4}[-\s]?\d{6,8}\b"
    )

    # 3. Standard 10-digit Indian mobile numbers starting with 6, 7, 8, 9
    #    e.g. 9876543210, 81081 14949, 91586-40360
    PATTERN_MOBILE_10 = re.compile(
        r"\b[6-9]\d{9}\b|\b[6-9]\d{4}[-\s]\d{5}\b|\b[6-9]\d{2}[-\s]\d{3}[-\s]\d{4}\b"
    )

    @property
    def detector_name(self) -> str:
        """Detector name."""
        return "phone_regex_detector"

    @property
    def supported_entity_types(self) -> List[str]:
        """Supported PII categories."""
        return ["PHONE"]

    def _is_financial_or_non_phone(self, text: str, match_str: str, start: int) -> bool:
        """Check if candidate match is a financial figure, percentage, or page number."""
        # Exclude if contains decimals, percentages, or commas
        if "%" in match_str or "." in match_str or "," in match_str:
            return True

        # Extract digits only
        digits = re.sub(r"\D", "", match_str)

        # Indian mobile/landline digit length check (10 digits, or 11/12 with country code 91 or STD 0)
        if len(digits) not in (10, 11, 12):
            return True

        # Check preceding context (e.g. Page 2025, Fiscal 2025, Rs. 1234567890)
        prefix_context = text[max(0, start - 20) : start].lower()
        if any(kw in prefix_context for kw in ["page", "p.", "fiscal", "year", "rs", "₹", "inr", "$", "section"]):
            # If preceding context is page/financial AND match is a 4-digit year or plain number without phone label
            if len(digits) < 10 or not any(lbl in prefix_context for lbl in ["tel", "phone", "mobile", "fax", "contact"]):
                return True

        return False

    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect Indian phone numbers in a TextChunk.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of PIIEntity objects for detected phone numbers.
        """
        entities: List[PIIEntity] = []
        text = chunk.text

        if not text:
            return entities

        found_spans: List[Tuple[int, int]] = []

        # Strategy 1: Check matches following explicit Phone/Tel labels
        for label_match in self.LABEL_PREFIX_REGEX.finditer(text):
            label_end = label_match.end()
            remainder = text[label_end:]

            # Match phone number right after label
            phone_match = (
                self.PATTERN_PLUS91.match(remainder)
                or self.PATTERN_STD_LANDLINE.match(remainder)
                or self.PATTERN_MOBILE_10.match(remainder)
            )

            if phone_match:
                matched_str = phone_match.group()
                abs_start = label_end + phone_match.start()
                abs_end = label_end + phone_match.end()

                if not self._is_financial_or_non_phone(text, matched_str, abs_start):
                    found_spans.append((abs_start, abs_end))
                    entities.append(
                        PIIEntity(
                            entity_type="PHONE",
                            original_text=matched_str,
                            start=abs_start,
                            end=abs_end,
                            confidence=1.0,
                            detector=self.detector_name,
                            source_location=chunk.source_location,
                        )
                    )

        # Strategy 2: Standalone matches (+91, STD landline, 10-digit mobile)
        for pattern, conf in [
            (self.PATTERN_PLUS91, 1.0),
            (self.PATTERN_STD_LANDLINE, 0.95),
            (self.PATTERN_MOBILE_10, 0.90),
        ]:
            for match in pattern.finditer(text):
                abs_start = match.start()
                abs_end = match.end()
                matched_str = match.group()

                # Avoid duplicate matches already captured with labels
                if any(s <= abs_start and abs_end <= e for s, e in found_spans):
                    continue

                if self._is_financial_or_non_phone(text, matched_str, abs_start):
                    continue

                found_spans.append((abs_start, abs_end))
                entities.append(
                    PIIEntity(
                        entity_type="PHONE",
                        original_text=matched_str,
                        start=abs_start,
                        end=abs_end,
                        confidence=conf,
                        detector=self.detector_name,
                        source_location=chunk.source_location,
                    )
                )

        # Sort entities by start offset
        entities.sort(key=lambda e: e.start)
        return entities
