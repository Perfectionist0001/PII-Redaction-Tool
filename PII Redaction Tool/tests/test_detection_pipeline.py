"""Unit tests for DetectionPipeline overlap resolution and conflict prioritization."""

import unittest
from src.detection_pipeline import DetectionPipeline, create_default_pipeline
from src.models import PIIEntity, SourceLocation, SourceType, TextChunk


class TestDetectionPipeline(unittest.TestCase):
    """Test suite for DetectionPipeline conflict resolution and overlap management."""

    def setUp(self) -> None:
        """Initialize pipeline instance."""
        self.pipeline = DetectionPipeline()

    def test_duplicate_detections_removed(self) -> None:
        """Test that exact duplicate entity detections are deduplicated."""
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)
        e1 = PIIEntity(
            entity_type="EMAIL",
            original_text="john@example.com",
            start=0,
            end=16,
            confidence=1.0,
            detector="email_detector",
            source_location=loc,
        )
        e2 = PIIEntity(
            entity_type="EMAIL",
            original_text="john@example.com",
            start=0,
            end=16,
            confidence=1.0,
            detector="email_detector",
            source_location=loc,
        )

        resolved = self.pipeline.deduplicate_and_resolve_overlaps([e1, e2])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].original_text, "john@example.com")

    def test_email_vs_ner_overlap(self) -> None:
        """Test that structured EMAIL detector wins over overlapping PERSON/ORGANIZATION NER detections."""
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)

        email_entity = PIIEntity(
            entity_type="EMAIL",
            original_text="john@example.com",
            start=0,
            end=16,
            confidence=1.0,
            detector="email_regex_detector",
            source_location=loc,
        )
        person_entity = PIIEntity(
            entity_type="PERSON",
            original_text="john",
            start=0,
            end=4,
            confidence=0.85,
            detector="spaCy_NER",
            source_location=loc,
        )
        org_entity = PIIEntity(
            entity_type="ORGANIZATION",
            original_text="example.com",
            start=5,
            end=16,
            confidence=0.85,
            detector="spaCy_NER",
            source_location=loc,
        )

        resolved = self.pipeline.deduplicate_and_resolve_overlaps(
            [person_entity, email_entity, org_entity]
        )

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].entity_type, "EMAIL")
        self.assertEqual(resolved[0].original_text, "john@example.com")

    def test_nested_person_detections_prefer_longer_span(self) -> None:
        """Test that larger meaningful span wins for nested detections of same priority."""
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)

        short_span = PIIEntity(
            entity_type="PERSON",
            original_text="John",
            start=0,
            end=4,
            confidence=0.85,
            detector="spaCy_NER",
            source_location=loc,
        )
        long_span = PIIEntity(
            entity_type="PERSON",
            original_text="John Smith",
            start=0,
            end=10,
            confidence=0.85,
            detector="spaCy_NER",
            source_location=loc,
        )

        resolved = self.pipeline.deduplicate_and_resolve_overlaps([short_span, long_span])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].original_text, "John Smith")

    def test_phone_vs_number_overlap(self) -> None:
        """Test that structured PHONE entity wins over partial numeric candidate."""
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)

        phone_entity = PIIEntity(
            entity_type="PHONE",
            original_text="+91 9876543210",
            start=0,
            end=14,
            confidence=1.0,
            detector="phone_regex_detector",
            source_location=loc,
        )
        num_entity = PIIEntity(
            entity_type="PHONE",
            original_text="9876543210",
            start=4,
            end=14,
            confidence=0.90,
            detector="phone_regex_detector",
            source_location=loc,
        )

        resolved = self.pipeline.deduplicate_and_resolve_overlaps([num_entity, phone_entity])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].original_text, "+91 9876543210")

    def test_address_vs_person_overlap(self) -> None:
        """Test that ADDRESS priority wins over overlapping PERSON/ORGANIZATION inside address."""
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)

        address_entity = PIIEntity(
            entity_type="ADDRESS",
            original_text="201, Tower 2, Baner, Pune – 411045, Maharashtra, India",
            start=0,
            end=54,
            confidence=0.95,
            detector="address_context_detector",
            source_location=loc,
        )
        person_inside = PIIEntity(
            entity_type="PERSON",
            original_text="Baner",
            start=14,
            end=19,
            confidence=0.85,
            detector="spaCy_NER",
            source_location=loc,
        )

        resolved = self.pipeline.deduplicate_and_resolve_overlaps([person_inside, address_entity])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].entity_type, "ADDRESS")

    def test_organization_vs_person_overlap(self) -> None:
        """Test priority resolution between overlapping ORGANIZATION and PERSON."""
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)

        org_entity = PIIEntity(
            entity_type="ORGANIZATION",
            original_text="Acme International Limited",
            start=0,
            end=26,
            confidence=0.90,
            detector="spaCy_NER",
            source_location=loc,
        )
        person_entity = PIIEntity(
            entity_type="PERSON",
            original_text="Acme International",
            start=0,
            end=18,
            confidence=0.85,
            detector="spaCy_NER",
            source_location=loc,
        )

        resolved = self.pipeline.deduplicate_and_resolve_overlaps([person_entity, org_entity])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].entity_type, "ORGANIZATION")

    def test_default_pipeline_e2e_chunk_processing(self) -> None:
        """Test end-to-end default pipeline execution on a chunk with multiple entity types."""
        pipeline = create_default_pipeline()
        text = "Contact Sarthak Malvadkar at cs.connect@kshinternational.com or +91 20 6729 5100."
        chunk = TextChunk(
            chunk_id="p_e2e",
            text=text,
            source_location=SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0),
        )

        entities = pipeline.process_chunk(chunk)
        entity_types = {e.entity_type for e in entities}

        self.assertIn("EMAIL", entity_types)
        self.assertIn("PHONE", entity_types)
        self.assertIn("PERSON", entity_types)

        # Assert no overlapping character spans exist in output
        for i in range(len(entities) - 1):
            self.assertLessEqual(entities[i].end, entities[i + 1].start)


if __name__ == "__main__":
    unittest.main()
