"""Unit tests for PhoneDetector."""

import unittest
from src.detectors.phone_detector import PhoneDetector
from src.models import SourceLocation, SourceType, TextChunk


class TestPhoneDetector(unittest.TestCase):
    """Test suite for PhoneDetector positive and negative cases."""

    def setUp(self) -> None:
        """Initialize PhoneDetector instance."""
        self.detector = PhoneDetector()

    def test_positive_indian_phone_numbers(self) -> None:
        """Test detection of common Indian mobile and landline phone formats."""
        positive_cases = [
            ("+91 9876543210", "+91 9876543210"),
            ("+91-9876543210", "+91-9876543210"),
            ("+91 20 45053237", "+91 20 45053237"),
            ("+91 22 68077100", "+91 22 68077100"),
            ("9876543210", "9876543210"),
            ("022-68052182", "022-68052182"),
            ("+91 (20) 6729 5100", "+91 (20) 6729 5100"),
            ("Tel: +91 22 6807 7100", "+91 22 6807 7100"),
        ]

        for input_text, expected_phone in positive_cases:
            chunk = TextChunk(
                chunk_id="p_test",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 1, f"Failed to detect valid phone in: '{input_text}'")

            entity = entities[0]
            self.assertEqual(entity.entity_type, "PHONE")
            self.assertEqual(entity.original_text, expected_phone)
            self.assertEqual(entity.detector, "phone_regex_detector")
            self.assertGreaterEqual(entity.confidence, 0.90)
            self.assertEqual(input_text[entity.start:entity.end], expected_phone)

    def test_negative_prospectus_numbers(self) -> None:
        """Test rejection of financial figures, share counts, years, percentages, and non-phone numbers."""
        negative_cases = [
            "26,704,570",
            "2025",
            "47.00%",
            "123456789012",
            "1234567890",
            "000004058",
            "000011179",
            "₹ 50,00,000",
            "Page 398",
            "Section 32 of Companies Act, 2013",
            "100% Book Built Offer",
        ]

        for input_text in negative_cases:
            chunk = TextChunk(
                chunk_id="p_test",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 0, f"Incorrectly flagged non-phone input as phone: '{input_text}'")

    def test_phone_in_table_cell(self) -> None:
        """Test detection of phone number inside table cell with source location preservation."""
        cell_text = "CONTACT PERSON: Sarthak Malvadkar TELEPHONE: +91 20 6729 5100"
        loc = SourceLocation(
            source_type=SourceType.TABLE_CELL,
            table_index=0,
            row_index=1,
            cell_index=2,
            paragraph_index=0,
        )
        chunk = TextChunk(
            chunk_id="tbl_0_r_1_c_2_p_0",
            text=cell_text,
            source_location=loc,
        )

        entities = self.detector.detect(chunk)
        self.assertEqual(len(entities), 1)

        entity = entities[0]
        self.assertEqual(entity.entity_type, "PHONE")
        self.assertEqual(entity.original_text, "+91 20 6729 5100")
        self.assertEqual(cell_text[entity.start:entity.end], "+91 20 6729 5100")
        self.assertEqual(entity.source_location.source_type, SourceType.TABLE_CELL)
        self.assertEqual(entity.source_location.table_index, 0)
        self.assertEqual(entity.source_location.row_index, 1)
        self.assertEqual(entity.source_location.cell_index, 2)


if __name__ == "__main__":
    unittest.main()
