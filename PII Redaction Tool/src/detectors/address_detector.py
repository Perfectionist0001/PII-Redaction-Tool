"""Physical and Mailing Address PII detector using multi-signal context matching."""

import re
from typing import List, Set, Tuple

from src.detectors.base import BaseDetector
from src.models import PIIEntity, TextChunk


class AddressDetector(BaseDetector):
    """Detector for identifying physical and mailing addresses in text chunks."""

    # Explicit address prefix triggers
    ADDRESS_PREFIX_REGEX = re.compile(
        r"(?i)\b(?:Registered Office|Corporate Office|Head Office|Branch Office|Registered office at|Corporate office at|Address)[:\s]+"
    )

    # Keywords for multi-signal category scoring
    STRUCTURE_KEYWORDS: Set[str] = {
        "flat",
        "floor",
        "plot",
        "building",
        "tower",
        "block",
        "unit",
        "suite",
        "office",
        "apartment",
        "industrial area",
        "industrial estate",
        "midc",
        "premise",
        "premises",
        "survey",
        "door no",
    }

    LOCALITY_KEYWORDS: Set[str] = {
        "road",
        "street",
        "lane",
        "marg",
        "nagar",
        "village",
        "taluka",
        "district",
        "chakan",
        "baner",
        "birdewadi",
        "khed",
        "bypass",
        "highway",
        "chowk",
        "cross",
    }

    REGION_KEYWORDS: Set[str] = {
        "pune",
        "mumbai",
        "delhi",
        "maharashtra",
        "gujarat",
        "karnataka",
        "tamil nadu",
        "bengaluru",
        "chennai",
        "hyderabad",
        "kolkata",
        "ahmedabad",
        "india",
    }

    PINCODE_REGEX = re.compile(
        r"\b(?:pin(?:\s*code)?|postal\s*code)?\s*[-–:]?\s*\d{3}\s*[-–]?\s*\d{3}\b",
        re.IGNORECASE,
    )

    # Combined multi-line address regex pattern matching structured address text
    ADDRESS_SPAN_REGEX = re.compile(
        r"(?i)\b(?:\d{1,4}[a-z]?[\/\-]\d{1,4}|\d{1,4})\s*,\s*(?:[^\n.,;]+[,\s]+){1,6}(?:pune|mumbai|delhi|maharashtra|gujarat|karnataka|india|\d{6}|\d{3}\s*[-–]?\s*\d{3})\b"
    )

    @property
    def detector_name(self) -> str:
        """Detector name."""
        return "address_context_detector"

    @property
    def supported_entity_types(self) -> List[str]:
        """Supported PII categories."""
        return ["ADDRESS"]

    def _evaluate_address_signals(self, text_span: str) -> int:
        """Calculate the number of distinct address signal categories present in text_span."""
        lower_span = text_span.lower()
        categories_found = 0

        # Category 1: Structural premises
        if any(kw in lower_span for kw in self.STRUCTURE_KEYWORDS):
            categories_found += 1

        # Category 2: Locality / Road / Village
        if any(kw in lower_span for kw in self.LOCALITY_KEYWORDS):
            categories_found += 1

        # Category 3: City / State / Region
        if any(kw in lower_span for kw in self.REGION_KEYWORDS):
            categories_found += 1

        # Category 4: PIN code / Postal code
        if self.PINCODE_REGEX.search(lower_span):
            categories_found += 1

        return categories_found

    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect physical and mailing addresses in a TextChunk.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of detected PIIEntity objects for valid physical addresses.
        """
        entities: List[PIIEntity] = []
        text = chunk.text

        if not text or not text.strip():
            return entities

        found_spans: List[Tuple[int, int]] = []

        # Strategy 1: Explicit address prefix matching (e.g. Registered Office: ...)
        for prefix_match in self.ADDRESS_PREFIX_REGEX.finditer(text):
            prefix_end = prefix_match.end()
            remainder = text[prefix_end:]

            # Extract lines across multi-line paragraphs/cells until non-address content
            lines = remainder.split("\n")
            addr_lines = []
            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    break
                # Stop if next line begins another section header (e.g. Tel:, Email:, Website:)
                if addr_lines and re.match(
                    r"(?i)^(tel|telephone|phone|fax|e-mail|email|website|cin|pan)[:\s]",
                    stripped_line,
                ):
                    break
                addr_lines.append(stripped_line)

            candidate_text = " ".join(addr_lines).strip()
            if not candidate_text:
                continue

            signals_count = self._evaluate_address_signals(candidate_text)
            if signals_count >= 1:
                abs_start = prefix_end
                abs_end = prefix_end + len(candidate_text)

                found_spans.append((abs_start, abs_end))
                entities.append(
                    PIIEntity(
                        entity_type="ADDRESS",
                        original_text=candidate_text,
                        start=abs_start,
                        end=abs_end,
                        confidence=0.95,
                        detector=self.detector_name,
                        source_location=chunk.source_location,
                    )
                )

        # Strategy 2: Multi-signal structured address pattern matching
        for span_match in self.ADDRESS_SPAN_REGEX.finditer(text):
            abs_start = span_match.start()
            abs_end = span_match.end()
            matched_text = span_match.group().strip()

            # Skip if overlapping with Strategy 1 matches
            if any(
                (s <= abs_start <= e) or (s <= abs_end <= e) or (abs_start <= s and e <= abs_end)
                for s, e in found_spans
            ):
                continue

            signals_count = self._evaluate_address_signals(matched_text)
            if signals_count >= 2:
                found_spans.append((abs_start, abs_end))
                entities.append(
                    PIIEntity(
                        entity_type="ADDRESS",
                        original_text=matched_text,
                        start=abs_start,
                        end=abs_end,
                        confidence=0.90,
                        detector=self.detector_name,
                        source_location=chunk.source_location,
                    )
                )

        entities.sort(key=lambda e: e.start)
        return entities
