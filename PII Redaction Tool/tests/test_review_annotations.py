"""Unit tests for GroundTruthReviewer human-review workflow."""

import json
import tempfile
import unittest
from pathlib import Path

from evaluation.review_annotations import GroundTruthReviewer


class TestGroundTruthReviewer(unittest.TestCase):
    """Test suite for GroundTruthReviewer actions and ground_truth.json generation."""

    def setUp(self) -> None:
        """Create temporary candidates JSON file for reviewer testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cand_path = Path(self.temp_dir.name) / "candidate_annotations.json"
        self.gt_path = Path(self.temp_dir.name) / "ground_truth.json"

        cand_data = {
            "document_name": "Red Herring Prospectus.docx",
            "total_candidates": 2,
            "summary_by_category": {"EMAIL": 1, "PERSON": 1},
            "candidates": [
                {
                    "candidate_id": "cand_1",
                    "entity_type": "EMAIL",
                    "original_text": "cs.connect@kshinternational.com",
                    "start": 0,
                    "end": 31,
                    "confidence": 1.0,
                    "detector": "email_detector",
                    "source_location": {"source_type": "paragraph", "paragraph_index": 0},
                },
                {
                    "candidate_id": "cand_2",
                    "entity_type": "PERSON",
                    "original_text": "RED HERRING PROSPECTUS",
                    "start": 35,
                    "end": 57,
                    "confidence": 0.85,
                    "detector": "spaCy_NER",
                    "source_location": {"source_type": "paragraph", "paragraph_index": 1},
                },
            ],
        }

        with open(self.cand_path, "w", encoding="utf-8") as f:
            json.dump(cand_data, f, indent=2)

        self.reviewer = GroundTruthReviewer(self.cand_path)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_accept_and_reject_candidate(self) -> None:
        """Test accepting a valid candidate and rejecting a false positive."""
        cand_1 = self.reviewer.raw_candidates[0]
        cand_2 = self.reviewer.raw_candidates[1]

        # Accept cand_1 as human verified
        gt1 = self.reviewer.accept_candidate(cand_1, notes="Valid corporate contact email", is_human=True)
        self.assertEqual(gt1["entity_type"], "EMAIL")
        self.assertEqual(gt1["text"], "cs.connect@kshinternational.com")
        self.assertEqual(gt1["review_status"], "human_verified")

        # Reject cand_2 (heading false positive)
        self.reviewer.reject_candidate(cand_2, reason="Document title heading, not a person")
        self.assertEqual(len(self.reviewer.ground_truth_entities), 1)
        self.assertEqual(len(self.reviewer.rejected_candidates), 1)

    def test_change_entity_type_and_correct_span(self) -> None:
        """Test reclassifying entity category and correcting text span."""
        cand = self.reviewer.raw_candidates[0]

        # Change entity type
        gt_mod = self.reviewer.change_entity_type(cand, "ORGANIZATION", notes="Reclassified")
        self.assertEqual(gt_mod["entity_type"], "ORGANIZATION")

        # Correct span
        gt_corr = self.reviewer.correct_entity_span(
            cand, new_text="cs.connect@ksh", new_start=0, new_end=14
        )
        self.assertEqual(gt_corr["text"], "cs.connect@ksh")
        self.assertEqual(gt_corr["start"], 0)
        self.assertEqual(gt_corr["end"], 14)

    def test_add_missing_annotation(self) -> None:
        """Test manually adding a missing entity annotation."""
        gt_add = self.reviewer.add_missing_annotation(
            entity_type="PERSON",
            text="Sarthak Malvadkar",
            start=10,
            end=27,
            source_location={"source_type": "paragraph", "paragraph_index": 5},
        )
        self.assertEqual(gt_add["entity_type"], "PERSON")
        self.assertEqual(gt_add["text"], "Sarthak Malvadkar")
        self.assertEqual(gt_add["review_status"], "human_added_manually")

    def test_save_ground_truth_json_schema(self) -> None:
        """Test saving ground_truth.json and validating output schema."""
        self.reviewer.accept_candidate(self.reviewer.raw_candidates[0], is_human=True)
        out_file = self.reviewer.save_ground_truth(self.gt_path)

        self.assertTrue(out_file.exists())
        with open(out_file, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        self.assertEqual(gt_data["document_name"], "Red Herring Prospectus.docx")
        self.assertEqual(gt_data["total_ground_truth_entities"], 1)
        self.assertIn("annotated_entities", gt_data)
        self.assertEqual(gt_data["annotated_entities"][0]["text"], "cs.connect@kshinternational.com")


if __name__ == "__main__":
    unittest.main()
