"""Unit tests for DOBDetector focusing on contextual ambiguity."""

import unittest
from src.detectors.dob_detector import DOBDetector
from src.models import SourceLocation, SourceType, TextChunk


class TestDOBDetector(unittest.TestCase):
    """Test suite for DOBDetector positive DOB triggers and negative non-DOB dates."""

    def setUp(self) -> None:
        """Initialize DOBDetector instance."""
        self.detector = DOBDetector()

    def test_positive_dob_triggers(self) -> None:
        """Test detection of dates preceded by explicit DOB triggers."""
        positive_cases = [
            ("DOB: 15/08/1998", "15/08/1998"),
            ("Date of Birth: 15 August 1998", "15 August 1998"),
            ("Born on 15 August 1998", "15 August 1998"),
            ("Birth Date: 1998-08-15", "1998-08-15"),
            ("D.O.B: Aug 15, 1998", "Aug 15, 1998"),
        ]

        for input_text, expected_date in positive_cases:
            chunk = TextChunk(
                chunk_id="p_dob",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(len(entities), 1, f"Failed to detect DOB in: '{input_text}'")

            entity = entities[0]
            self.assertEqual(entity.entity_type, "DOB")
            self.assertEqual(entity.original_text, expected_date)
            self.assertEqual(entity.detector, "dob_context_detector")
            self.assertGreaterEqual(entity.confidence, 0.90)
            self.assertEqual(input_text[entity.start:entity.end], expected_date)

    def test_negative_contextual_ambiguity_dates(self) -> None:
        """Test rejection of filing, incorporation, offer, and financial dates."""
        negative_cases = [
            "The Red Herring Prospectus is dated December 10, 2025.",
            "The company was incorporated on July 30, 1979.",
            "Fiscal year ended March 31, 2023.",
            "Offer opening date: December 1, 2025.",
            "The agreement was signed on 15/08/2020.",
            "Dated December 10, 2025",
            "Period ended September 30, 2023",
            "Certificate issued on October 13, 2011",
        ]

        for input_text in negative_cases:
            chunk = TextChunk(
                chunk_id="p_non_dob",
                text=input_text,
                source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
            )
            entities = self.detector.detect(chunk)
            self.assertEqual(
                len(entities),
                0,
                f"Incorrectly flagged non-DOB date as DOB in: '{input_text}'",
            )


if __name__ == "__main__":
    unittest.main()
