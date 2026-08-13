"""Regression and negative test suite covering all false positive/negative edge cases."""

import unittest

from src.detection_pipeline import create_default_pipeline
from src.detectors import (
    AddressDetector,
    CreditCardDetector,
    DOBDetector,
    IPDetector,
    PhoneDetector,
    SSNDetector,
)
from src.evaluation.metrics import MetricsCalculator
from src.models import PIIEntity, SourceLocation, SourceType, TextChunk


class TestRegressionsAndNegatives(unittest.TestCase):
    """Test suite enforcing strict rejection of non-PII financial, numeric, and geographic strings."""

    def setUp(self) -> None:
        """Initialize detectors and common dummy locations."""
        self.dob_detector = DOBDetector()
        self.phone_detector = PhoneDetector()
        self.ssn_detector = SSNDetector()
        self.cc_detector = CreditCardDetector()
        self.ip_detector = IPDetector()
        self.address_detector = AddressDetector()

        self.loc1 = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)
        self.loc_tbl1 = SourceLocation(
            source_type=SourceType.TABLE_CELL,
            table_index=23,
            row_index=1,
            cell_index=1,
            paragraph_index=0,
        )
        self.loc_tbl2 = SourceLocation(
            source_type=SourceType.TABLE_CELL,
            table_index=32,
            row_index=0,
            cell_index=0,
            paragraph_index=0,
        )

    def test_same_local_offsets_different_table_cells(self) -> None:
        """Verify that identical local offsets in different table cells are treated as distinct entities."""
        loc1_tuple = (SourceType.TABLE_CELL.value, None, 23, 1, 1, None, None)
        loc2_tuple = (SourceType.TABLE_CELL.value, None, 32, 0, 0, None, None)

        preds = [
            (loc1_tuple, 0, 21, "Kushal Subbayya Hegde"),
            (loc2_tuple, 0, 21, "Kushal Subbayya Hegde"),
        ]
        gts = [
            (loc1_tuple, 0, 21, "Kushal Subbayya Hegde"),
            (loc2_tuple, 0, 21, "Kushal Subbayya Hegde"),
        ]

        metrics = MetricsCalculator.calculate_category_metrics("PERSON", preds, gts)

        self.assertEqual(metrics.total_ground_truth, 2)
        self.assertEqual(metrics.total_predictions, 2)
        self.assertEqual(metrics.true_positives, 2)
        self.assertEqual(metrics.false_positives, 0)
        self.assertEqual(metrics.false_negatives, 0)
        self.assertEqual(metrics.precision, 1.0)
        self.assertEqual(metrics.recall, 1.0)

    def test_missed_repeated_pii_coreference_propagation(self) -> None:
        """Verify Document-Wide Co-reference Propagation detects repeated PII across chunks."""
        chunk1 = TextChunk("c1", "Promoter details for Kushal Subbayya Hegde.", self.loc1)
        # Chunk 2 has different context where NER might miss it
        chunk2 = TextChunk(
            "c2",
            "We are led by our Individual Promoters Kushal Subbayya Hegde, Pushpa Kushal Hegde.",
            SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=617),
        )

        pipeline = create_default_pipeline()
        entities = pipeline.process_chunks([chunk1, chunk2])

        # Verify Kushal Subbayya Hegde is detected in BOTH chunks
        texts_by_p = [e.original_text for e in entities if "Kushal Subbayya Hegde" in e.original_text]
        self.assertGreaterEqual(len(texts_by_p), 2)

    def test_negative_normal_dates_not_dob(self) -> None:
        """Verify incorporation, filing, and financial period dates are rejected as DOB."""
        chunk1 = TextChunk("c1", "The Red Herring Prospectus is dated December 10, 2025.", self.loc1)
        chunk2 = TextChunk("c2", "The company was incorporated on July 30, 1979.", self.loc1)
        chunk3 = TextChunk("c3", "For the period ended March 31, 2023.", self.loc1)

        self.assertEqual(len(self.dob_detector.detect(chunk1)), 0)
        self.assertEqual(len(self.dob_detector.detect(chunk2)), 0)
        self.assertEqual(len(self.dob_detector.detect(chunk3)), 0)

    def test_negative_financial_amounts_and_share_counts(self) -> None:
        """Verify financial figures and share counts are rejected as PHONE or CC."""
        chunk1 = TextChunk("c1", "Offer of 26,704,570 equity shares at ₹ 50,00,000.", self.loc1)
        chunk2 = TextChunk("c2", "Total paid up capital of 47,000,000 shares.", self.loc1)

        self.assertEqual(len(self.phone_detector.detect(chunk1)), 0)
        self.assertEqual(len(self.phone_detector.detect(chunk2)), 0)
        self.assertEqual(len(self.cc_detector.detect(chunk1)), 0)
        self.assertEqual(len(self.cc_detector.detect(chunk2)), 0)

    def test_negative_page_numbers_and_arbitrary_numbers(self) -> None:
        """Verify page numbers and arbitrary numeric sequences are rejected as PII."""
        chunk1 = TextChunk("c1", "Refer to details on page 398 and page 2025.", self.loc1)
        chunk2 = TextChunk("c2", "Internal reference serial number 123456789012.", self.loc1)

        self.assertEqual(len(self.phone_detector.detect(chunk1)), 0)
        self.assertEqual(len(self.ssn_detector.detect(chunk2)), 0)
        self.assertEqual(len(self.cc_detector.detect(chunk2)), 0)

    def test_negative_company_registration_numbers_not_ssn(self) -> None:
        """Verify CIN and RoC registration numbers are rejected as SSN."""
        chunk = TextChunk("c1", "CIN: U28129PN1979PLC141032, RoC Registration No: 080618.", self.loc1)
        self.assertEqual(len(self.ssn_detector.detect(chunk)), 0)

    def test_negative_invalid_ip_addresses(self) -> None:
        """Verify invalid IPv4 strings are rejected by IP detector."""
        chunk = TextChunk("c1", "Server IPs: 999.999.999.999 and 1234.5.6.7 are invalid.", self.loc1)
        self.assertEqual(len(self.ip_detector.detect(chunk)), 0)

    def test_negative_invalid_credit_card_luhn_failure(self) -> None:
        """Verify 16-digit numbers failing Luhn checksum are rejected by CC detector."""
        chunk = TextChunk("c1", "Card candidate 4111 1111 1111 1112 fails Luhn check.", self.loc1)
        self.assertEqual(len(self.cc_detector.detect(chunk)), 0)

    def test_negative_city_and_state_names_alone(self) -> None:
        """Verify isolated city or state names are rejected as complete ADDRESS."""
        chunk1 = TextChunk("c1", "The meeting was held in Pune.", self.loc1)
        chunk2 = TextChunk("c2", "Operations located in Maharashtra and Delhi.", self.loc1)

        self.assertEqual(len(self.address_detector.detect(chunk1)), 0)
        self.assertEqual(len(self.address_detector.detect(chunk2)), 0)

    def test_careedge_leak_regression(self) -> None:
        """Verify that co-reference propagation correctly recovers missed occurrences of the same entity within the same paragraph.

        Specifically, if statistical NER detects occurrences 2 and 3 but misses occurrence 1,
        propagation should scan the paragraph and recover occurrence 1 without creating duplicate spans.
        """
        text = "Under the agreement, CareEdge Research was selected. Further, CareEdge Research will publish reports. CareEdge Research also confirmed independence."
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)
        chunk = TextChunk("c1", text, loc)

        from src.detectors.base import BaseDetector
        from src.detection_pipeline import DetectionPipeline
        from typing import List

        class MockDetector(BaseDetector):
            @property
            def detector_name(self) -> str:
                return "MockDetector"

            @property
            def supported_entity_types(self) -> List[str]:
                return ["ORGANIZATION"]

            def detect(self, chunk: TextChunk) -> List[PIIEntity]:
                # Return only occurrences 2 and 3
                return [
                    PIIEntity(
                        entity_type="ORGANIZATION",
                        original_text="CareEdge Research",
                        start=62,
                        end=79,
                        confidence=0.85,
                        detector="MockNER",
                        source_location=chunk.source_location,
                    ),
                    PIIEntity(
                        entity_type="ORGANIZATION",
                        original_text="CareEdge Research",
                        start=102,
                        end=119,
                        confidence=0.85,
                        detector="MockNER",
                        source_location=chunk.source_location,
                    )
                ]

        pipeline = DetectionPipeline()
        pipeline.register_detector(MockDetector())

        entities = pipeline.process_chunks([chunk])

        # Verify that all 3 occurrences were detected
        self.assertEqual(len(entities), 3)

        # Spans should be unique and match the 3 occurrences exactly
        spans = sorted([(e.start, e.end) for e in entities])
        expected_spans = [(21, 38), (62, 79), (102, 119)]
        self.assertEqual(spans, expected_spans)

        # All entities should be ORGANIZATION type
        for e in entities:
            self.assertEqual(e.entity_type, "ORGANIZATION")
            self.assertEqual(e.original_text, "CareEdge Research")
            self.assertEqual(e.source_location.paragraph_index, 0)
            self.assertEqual(e.source_location.source_type, SourceType.PARAGRAPH)


if __name__ == "__main__":
    unittest.main()
