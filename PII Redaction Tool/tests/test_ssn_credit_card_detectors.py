"""Unit tests for SSNDetector and CreditCardDetector."""

import unittest
from src.detectors.credit_card_detector import CreditCardDetector
from src.detectors.ssn_detector import SSNDetector
from src.models import SourceLocation, SourceType, TextChunk


class TestSSNDetector(unittest.TestCase):
    """Test suite for SSNDetector positive and negative cases."""

    def setUp(self) -> None:
        """Initialize detector instance."""
        self.detector = SSNDetector()

    def test_positive_ssn(self) -> None:
        """Test detection of valid US SSN formats."""
        valid_ssns = [
            "123-45-6789",
            "456-78-9012",
            "219-09-9999",
        ]

        for ssn_str in valid_ssns:
            chunk = TextChunk(
                chunk_id="p_ssn",
                text=f"User SSN is {ssn_str} for tax verification.",
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 1, f"Failed to detect valid SSN: {ssn_str}")
            entity = entities[0]
            self.assertEqual(entity.entity_type, "SSN")
            self.assertEqual(entity.original_text, ssn_str)
            self.assertEqual(entity.detector, "ssn_regex_detector")
            self.assertEqual(entity.confidence, 1.0)

    def test_negative_ssn_and_company_identifiers(self) -> None:
        """Test rejection of invalid SSNs, PAN, CIN, registration numbers, and financial counts."""
        invalid_inputs = [
            "000-45-6789",  # Invalid area 000
            "666-45-6789",  # Invalid area 666
            "901-45-6789",  # Invalid area 900-999
            "123-00-6789",  # Invalid group 00
            "123-45-0000",  # Invalid serial 0000
            "ABCDE1234F",   # Indian PAN
            "U28129PN1979PLC141032",  # Indian CIN
            "L65920MH1994PLC080618",  # Indian CIN
            "000004058",    # Company registration number
            "26,704,570",   # Share count
            "1234567890",   # 10-digit number without hyphens
            "123-456-789",  # Wrong format
        ]

        for text in invalid_inputs:
            chunk = TextChunk(
                chunk_id="p_test",
                text=text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 0, f"Incorrectly detected invalid input as SSN: '{text}'")


class TestCreditCardDetector(unittest.TestCase):
    """Test suite for CreditCardDetector positive, negative, and Luhn validation cases."""

    def setUp(self) -> None:
        """Initialize detector instance."""
        self.detector = CreditCardDetector()

    def test_positive_credit_cards(self) -> None:
        """Test valid credit card numbers with space, hyphen, and unformatted patterns."""
        valid_cards = [
            ("4111 1111 1111 1111", "4111 1111 1111 1111"),
            ("4111-1111-1111-1111", "4111-1111-1111-1111"),
            ("4111111111111111", "4111111111111111"),
        ]

        for input_str, expected_orig in valid_cards:
            chunk = TextChunk(
                chunk_id="p_cc",
                text=f"Payment card: {input_str}",
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 1, f"Failed to detect valid credit card: '{input_str}'")

            entity = entities[0]
            self.assertEqual(entity.entity_type, "CREDIT_CARD")
            self.assertEqual(entity.original_text, expected_orig)
            self.assertEqual(entity.detector, "credit_card_luhn_detector")
            self.assertEqual(entity.confidence, 1.0)

    def test_negative_invalid_luhn_and_prospectus_numbers(self) -> None:
        """Test rejection of 16-digit non-card numbers, invalid Luhn, share counts, and financial figures."""
        invalid_inputs = [
            "1111 1111 1111 1111",  # Invalid Luhn checksum
            "1111111111111111",     # Invalid Luhn checksum
            "26,704,570",           # Share count with commas
            "47.00%",               # Percentage
            "123456789012",         # 12-digit share count
            "U28129PN1979PLC141032",# CIN
            "₹ 50,00,000",          # Monetary figure
            "000004058",            # Registration number
        ]

        for text in invalid_inputs:
            chunk = TextChunk(
                chunk_id="p_test",
                text=text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 0, f"Incorrectly flagged non-card input as CREDIT_CARD: '{text}'")


if __name__ == "__main__":
    unittest.main()
