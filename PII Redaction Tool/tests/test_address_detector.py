"""Unit tests for AddressDetector."""

import unittest
from src.detectors.address_detector import AddressDetector
from src.models import SourceLocation, SourceType, TextChunk


class TestAddressDetector(unittest.TestCase):
    """Test suite for AddressDetector positive addresses and prospectus-like false positives."""

    def setUp(self) -> None:
        """Initialize AddressDetector instance."""
        self.detector = AddressDetector()

    def test_positive_multi_signal_addresses(self) -> None:
        """Test detection of complete physical and mailing addresses."""
        positive_cases = [
            (
                "201, Tower 2, Montreal Business Centre, Off Pallod Farms, Baner, Pune – 411045, Maharashtra, India",
                "201, Tower 2, Montreal Business Centre, Off Pallod Farms, Baner, Pune – 411045, Maharashtra, India",
            ),
            (
                "Registered Office: 11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India",
                "11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India",
            ),
        ]

        for input_text, expected_address in positive_cases:
            chunk = TextChunk(
                chunk_id="p_addr",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 1, f"Failed to detect valid address in: '{input_text}'")

            entity = entities[0]
            self.assertEqual(entity.entity_type, "ADDRESS")
            self.assertEqual(entity.original_text, expected_address)
            self.assertEqual(entity.detector, "address_context_detector")
            self.assertGreaterEqual(entity.confidence, 0.90)
            self.assertEqual(input_text[entity.start:entity.end], expected_address)

    def test_multi_line_address_in_table_cell(self) -> None:
        """Test detection of multi-line address text within a table cell."""
        multi_line_text = (
            "REGISTERED OFFICE:\n"
            "Plot No. 11/3, Village Birdewadi,\n"
            "Chakan Taluka, Pune – 410501, Maharashtra"
        )
        chunk = TextChunk(
            chunk_id="tbl_0_c_0",
            text=multi_line_text,
            source_location=SourceLocation(
                source_type=SourceType.TABLE_CELL, table_index=0, row_index=0, cell_index=0
            ),
        )

        entities = self.detector.detect(chunk)
        self.assertEqual(len(entities), 1)
        entity = entities[0]
        self.assertEqual(entity.entity_type, "ADDRESS")
        self.assertIn("Birdewadi", entity.original_text)
        self.assertIn("Pune", entity.original_text)
        self.assertEqual(entity.source_location.source_type, SourceType.TABLE_CELL)

    def test_negative_prospectus_false_positives(self) -> None:
        """Test rejection of isolated city names, state names, PIN codes alone, company names, and financial figures."""
        negative_cases = [
            "Pune",
            "Maharashtra",
            "410 501",
            "411045",
            "KSH International Limited",
            "26,704,570",
            "₹ 50,00,000",
            "100% Book Built Offer",
            "Dated December 10, 2025",
        ]

        for input_text in negative_cases:
            chunk = TextChunk(
                chunk_id="p_neg",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(
                len(entities),
                0,
                f"Incorrectly flagged non-address input as ADDRESS: '{input_text}'",
            )


if __name__ == "__main__":
    unittest.main()
