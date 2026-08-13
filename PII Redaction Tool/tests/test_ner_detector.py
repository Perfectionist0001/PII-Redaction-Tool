"""Unit tests for NERDetector using local spaCy model."""

import unittest
from unittest.mock import patch

from src.detectors.ner_detector import NERDetector
from src.models import SourceLocation, SourceType, TextChunk


class TestNERDetector(unittest.TestCase):
    """Test suite for local spaCy NER detector."""

    def setUp(self) -> None:
        """Initialize NERDetector instance."""
        self.detector = NERDetector(model_name="en_core_web_sm")

    def test_required_person_and_organization_detection(self) -> None:
        """Test exact expected detection for 'John Smith works at Example Technologies Limited.'"""
        text = "John Smith works at Example Technologies Limited."
        chunk = TextChunk(
            chunk_id="p_test",
            text=text,
            source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
        )

        entities = self.detector.detect(chunk)
        self.assertGreaterEqual(len(entities), 2)

        person_entities = [e for e in entities if e.entity_type == "PERSON"]
        org_entities = [e for e in entities if e.entity_type == "ORGANIZATION"]

        self.assertEqual(len(person_entities), 1)
        self.assertEqual(person_entities[0].original_text, "John Smith")
        self.assertEqual(person_entities[0].detector, "spaCy_NER")
        self.assertEqual(text[person_entities[0].start:person_entities[0].end], "John Smith")

        self.assertEqual(len(org_entities), 1)
        self.assertEqual(org_entities[0].original_text, "Example Technologies Limited")
        self.assertEqual(org_entities[0].detector, "spaCy_NER")
        self.assertEqual(text[org_entities[0].start:org_entities[0].end], "Example Technologies Limited")

    def test_prospectus_entities_and_false_positives(self) -> None:
        """Test entity detection on corporate prospectus organizations and person names."""
        prospectus_text = (
            "Sarthak Malvadkar is the Compliance Officer of KSH International Limited. "
            "The lead manager is ICICI Securities Limited."
        )
        chunk = TextChunk(
            chunk_id="p_prospectus",
            text=prospectus_text,
            source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=1),
        )

        entities = self.detector.detect(chunk)
        person_names = [e.original_text for e in entities if e.entity_type == "PERSON"]
        org_names = [e.original_text for e in entities if e.entity_type == "ORGANIZATION"]

        self.assertIn("Sarthak Malvadkar", person_names)
        self.assertTrue(
            any("KSH" in org for org in org_names) or any("ICICI" in org for org in org_names)
        )

    def test_capitalized_headings_not_person(self) -> None:
        """Test that ALL-CAPS document titles are not incorrectly tagged as PERSON."""
        text = "RED HERRING PROSPECTUS Dated December 10, 2025. SECTION I - GENERAL."
        chunk = TextChunk(
            chunk_id="p_title",
            text=text,
            source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=2),
        )

        entities = self.detector.detect(chunk)
        person_entities = [e for e in entities if e.entity_type == "PERSON"]
        self.assertEqual(len(person_entities), 0)

    def test_missing_model_error_reporting(self) -> None:
        """Test that attempting to load a non-existent model raises a clear RuntimeError with instructions."""
        with self.assertRaises(RuntimeError) as ctx:
            NERDetector(model_name="non_existent_spacy_model_xyz")

        self.assertIn("python -m spacy download non_existent_spacy_model_xyz", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
