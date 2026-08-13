"""Unit tests for IPDetector."""

import unittest
from src.detectors.ip_detector import IPDetector
from src.models import SourceLocation, SourceType, TextChunk


class TestIPDetector(unittest.TestCase):
    """Test suite for IPDetector positive and negative cases."""

    def setUp(self) -> None:
        """Initialize IPDetector instance."""
        self.detector = IPDetector()

    def test_positive_ip_addresses(self) -> None:
        """Test valid IPv4 address detection."""
        positive_cases = [
            ("192.168.1.1", "192.168.1.1"),
            ("10.0.0.1", "10.0.0.1"),
            ("172.16.0.10", "172.16.0.10"),
            ("8.8.8.8", "8.8.8.8"),
        ]

        for input_text, expected_ip in positive_cases:
            chunk = TextChunk(
                chunk_id="p_test",
                text=f"Server address: {input_text}",
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 1, f"Failed to detect valid IP: '{input_text}'")

            entity = entities[0]
            self.assertEqual(entity.entity_type, "IP_ADDRESS")
            self.assertEqual(entity.original_text, expected_ip)
            self.assertEqual(entity.detector, "ip_address_detector")
            self.assertEqual(entity.confidence, 1.0)
            self.assertEqual(chunk.text[entity.start:entity.end], expected_ip)

    def test_negative_invalid_ips_and_financial_numbers(self) -> None:
        """Test rejection of out-of-range IP strings, invalid numbers, and financial data."""
        negative_cases = [
            "999.999.999.999",
            "1234.5.6.7",
            "256.1.1.1",
            "300.0.0.1",
            "1,000.00",
            "10.5.2023",
            "1.2.3.4.5",
            "2025.10.15",
            "26,704,570",
        ]

        for input_text in negative_cases:
            chunk = TextChunk(
                chunk_id="p_test",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 0, f"Incorrectly detected invalid input as IP: '{input_text}'")


if __name__ == "__main__":
    unittest.main()
