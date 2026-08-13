"""IPv4 Address PII detector using regex candidates and Python's ipaddress module validation."""

import ipaddress
import re
from typing import List

from src.detectors.base import BaseDetector
from src.models import PIIEntity, TextChunk


class IPDetector(BaseDetector):
    """Detector for identifying valid IPv4 network addresses."""

    # Candidate regex for IPv4 address patterns (ensuring not surrounded by extra digits/dots)
    IPV4_CANDIDATE_REGEX = re.compile(
        r"(?<![\d.])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?![\d.])"
    )

    @property
    def detector_name(self) -> str:
        """Detector name."""
        return "ip_address_detector"

    @property
    def supported_entity_types(self) -> List[str]:
        """Supported PII categories."""
        return ["IP_ADDRESS"]

    def _is_valid_ipv4(self, ip_str: str) -> bool:
        """Validate IP string using ipaddress module."""
        try:
            addr = ipaddress.ip_address(ip_str)
            # Ensure it is IPv4 (version 4)
            return addr.version == 4
        except ValueError:
            return False

    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect valid IPv4 addresses in a given TextChunk.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of detected PIIEntity objects for valid IP addresses.
        """
        entities: List[PIIEntity] = []
        text = chunk.text

        if not text:
            return entities

        for match in self.IPV4_CANDIDATE_REGEX.finditer(text):
            matched_str = match.group()

            if self._is_valid_ipv4(matched_str):
                entities.append(
                    PIIEntity(
                        entity_type="IP_ADDRESS",
                        original_text=matched_str,
                        start=match.start(),
                        end=match.end(),
                        confidence=1.0,
                        detector=self.detector_name,
                        source_location=chunk.source_location,
                    )
                )

        return entities
