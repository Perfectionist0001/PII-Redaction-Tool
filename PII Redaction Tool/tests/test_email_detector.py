"""Unit tests for EmailDetector."""

import unittest
from src.detectors.email_detector import EmailDetector
from src.models import SourceLocation, SourceType, TextChunk


class TestEmailDetector(unittest.TestCase):
    """Test suite for EmailDetector positive, negative, punctuation, and table cell cases."""

    def setUp(self) -> None:
        """Initialize detector instance."""
        self.detector = EmailDetector()

    def test_positive_email_addresses(self) -> None:
        """Test detection of valid email formats."""
        positive_cases = [
            ("john@example.com", "john@example.com"),
            ("john.smith@example.co.in", "john.smith@example.co.in"),
            ("test+abc@example.com", "test+abc@example.com"),
            ("cs.connect@kshinternational.com", "cs.connect@kshinternational.com"),
        ]

        for input_text, expected_email in positive_cases:
            chunk = TextChunk(
                chunk_id="p_test",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 1, f"Failed to detect valid email in: {input_text}")
            entity = entities[0]
            self.assertEqual(entity.entity_type, "EMAIL")
            self.assertEqual(entity.original_text, expected_email)
            self.assertEqual(entity.detector, "email_regex_detector")
            self.assertEqual(entity.confidence, 1.0)
            self.assertEqual(input_text[entity.start:entity.end], expected_email)

    def test_negative_email_addresses(self) -> None:
        """Test non-matching invalid email inputs."""
        negative_cases = [
            "john@example",
            "example.com",
            "@domain.com",
            "just plain text",
            "user@",
            "http://example.com",
        ]

        for input_text in negative_cases:
            chunk = TextChunk(
                chunk_id="p_test",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 0, f"Incorrectly detected invalid email in: {input_text}")

    def test_trailing_punctuation_avoidance(self) -> None:
        """Test that trailing punctuation like periods or commas is excluded from match."""
        input_text = "Contact us at john@example.com. Or send mail to john.smith@example.co.in,"
        chunk = TextChunk(
            chunk_id="p_punct",
            text=input_text,
            source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=1),
        )

        entities = self.detector.detect(chunk)
        self.assertEqual(len(entities), 2)

        self.assertEqual(entities[0].original_text, "john@example.com")
        self.assertFalse(entities[0].original_text.endswith("."))
        self.assertEqual(input_text[entities[0].start:entities[0].end], "john@example.com")

        self.assertEqual(entities[1].original_text, "john.smith@example.co.in")
        self.assertFalse(entities[1].original_text.endswith(","))
        self.assertEqual(input_text[entities[1].start:entities[1].end], "john.smith@example.co.in")

    def test_email_in_table_cell(self) -> None:
        """Test email detection inside table cell chunks with source location preservation."""
        cell_text = "E-MAIL AND TELEPHONE: customercare@icicisecurities.com / +91 22 4009 4400"
        loc = SourceLocation(
            source_type=SourceType.TABLE_CELL,
            table_index=2,
            row_index=1,
            cell_index=3,
            paragraph_index=0,
        )
        chunk = TextChunk(
            chunk_id="tbl_2_r_1_c_3_p_0",
            text=cell_text,
            source_location=loc,
        )

        entities = self.detector.detect(chunk)
        self.assertEqual(len(entities), 1)

        entity = entities[0]
        self.assertEqual(entity.entity_type, "EMAIL")
        self.assertEqual(entity.original_text, "customercare@icicisecurities.com")
        self.assertEqual(cell_text[entity.start:entity.end], "customercare@icicisecurities.com")
        self.assertIsNotNone(entity.source_location)
        self.assertEqual(entity.source_location.source_type, SourceType.TABLE_CELL)
        self.assertEqual(entity.source_location.table_index, 2)
        self.assertEqual(entity.source_location.row_index, 1)
        self.assertEqual(entity.source_location.cell_index, 3)


if __name__ == "__main__":
    unittest.main()
