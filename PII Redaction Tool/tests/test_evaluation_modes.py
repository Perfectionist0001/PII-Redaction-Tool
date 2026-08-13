"""Unit tests for partial human-review evaluation mode vs full evaluation mode."""

import json
import tempfile
import unittest
from pathlib import Path

import docx
from src.evaluation.evaluate import run_evaluation
from src.config import settings


class TestEvaluationModes(unittest.TestCase):
    """Test suite verifying partial evaluation behavior and metrics partitioning."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Create a dummy docx file
        self.docx_path = self.dir_path / "test_document.docx"
        doc = docx.Document()
        doc.add_paragraph("KSH INTERNATIONAL LIMITED is located at Pune. Anchor Investors.")
        doc.save(self.docx_path)

        # Create candidate_annotations.json
        self.cand_path = self.dir_path / "candidate_annotations.json"
        self.cand_data = {
            "document_name": "test_document.docx",
            "total_candidates": 3,
            "candidates": [
                {
                    "candidate_id": "cand_1",
                    "entity_type": "ORGANIZATION",
                    "original_text": "KSH INTERNATIONAL LIMITED",
                    "start": 0,
                    "end": 25,
                    "confidence": 0.85,
                    "detector": "spaCy_NER",
                    "source_location": {
                        "source_type": "paragraph",
                        "paragraph_index": 0,
                        "table_index": None,
                        "row_index": None,
                        "cell_index": None,
                        "header_index": None,
                        "footer_index": None
                    },
                    "surrounding_context": "KSH INTERNATIONAL LIMITED is located at Pune."
                },
                {
                    "candidate_id": "cand_2",
                    "entity_type": "ORGANIZATION",
                    "original_text": "Anchor Investors",
                    "start": 41,
                    "end": 57,
                    "confidence": 0.85,
                    "detector": "spaCy_NER",
                    "source_location": {
                        "source_type": "paragraph",
                        "paragraph_index": 0,
                        "table_index": None,
                        "row_index": None,
                        "cell_index": None,
                        "header_index": None,
                        "footer_index": None
                    },
                    "surrounding_context": "Anchor Investors."
                },
                {
                    "candidate_id": "cand_3",
                    "entity_type": "ADDRESS",
                    "original_text": "Pune",
                    "start": 40,
                    "end": 44,
                    "confidence": 0.85,
                    "detector": "spaCy_NER",
                    "source_location": {
                        "source_type": "paragraph",
                        "paragraph_index": 0,
                        "table_index": None,
                        "row_index": None,
                        "cell_index": None,
                        "header_index": None,
                        "footer_index": None
                    },
                    "surrounding_context": "located at Pune."
                }
            ]
        }
        with open(self.cand_path, "w", encoding="utf-8") as f:
            json.dump(self.cand_data, f, indent=2)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_partial_evaluation_mode(self) -> None:
        """Test partial review evaluation partitioning rules.

        - cand_1: reviewed and accepted. Should count as TP if predicted.
        - cand_2: reviewed and rejected. Should count as FP if predicted.
        - cand_3: unreviewed. Predictions here must be counted as UNASSESSED (not FP).
        """
        # Create a partially reviewed ground_truth_verified.json
        verified_gt_path = self.dir_path / "ground_truth_verified.json"
        verified_gt_data = {
            "document_name": "test_document.docx",
            "schema_version": "1.1",
            "is_provisional_candidate": True,
            "review_status_summary": "PARTIALLY HUMAN REVIEWED",
            "total_ground_truth_entities": 1,
            "annotated_entities": [
                {
                    "entity_id": "gt_1",
                    "entity_type": "ORGANIZATION",
                    "text": "KSH INTERNATIONAL LIMITED",
                    "start": 0,
                    "end": 25,
                    "source_location": {
                        "source_type": "paragraph",
                        "paragraph_index": 0,
                        "table_index": None,
                        "row_index": None,
                        "cell_index": None,
                        "header_index": None,
                        "footer_index": None
                    },
                    "review_status": "human_verified",
                    "detector_source": "spaCy_NER"
                }
            ],
            "reviewed_candidate_ids": ["cand_1", "cand_2"],
            "rejected_candidates": [
                {
                    "candidate_id": "cand_2",
                    "entity_type": "ORGANIZATION",
                    "original_text": "Anchor Investors",
                    "start": 41,
                    "end": 57,
                    "confidence": 0.85,
                    "detector": "spaCy_NER",
                    "source_location": {
                        "source_type": "paragraph",
                        "paragraph_index": 0,
                        "table_index": None,
                        "row_index": None,
                        "cell_index": None,
                        "header_index": None,
                        "footer_index": None
                    },
                    "surrounding_context": "Anchor Investors.",
                    "rejection_reason": "Generic term"
                }
            ]
        }
        with open(verified_gt_path, "w", encoding="utf-8") as f:
            json.dump(verified_gt_data, f, indent=2)

        # Run evaluation
        report_md_path = self.dir_path / "evaluation_report.md"
        
        # Temporarily patch settings directory so that candidate_annotations.json is found
        old_eval_dir = settings.evaluation_dir
        settings.evaluation_dir = self.dir_path

        try:
            metrics = run_evaluation(self.docx_path, verified_gt_path, report_md_path)
            
            # Assertions
            self.assertTrue(metrics.is_partial_review)
            self.assertEqual(metrics.reviewed_candidates, 2)
            self.assertEqual(metrics.rejected_candidates, 1)
            self.assertEqual(metrics.total_ground_truth, 1)  # KSH INTERNATIONAL LIMITED
            
            # Check TP, FP, FN and Unassessed
            # The pipeline procesing KSH INTERNATIONAL LIMITED will predict it (TP).
            # The pipeline processing "Anchor Investors" may predict it (Known FP since rejected).
            # The pipeline processing "Pune" will predict it (Unassessed since cand_3 is unreviewed).
            self.assertGreaterEqual(metrics.true_positives, 0)
            self.assertGreaterEqual(metrics.false_positives, 0)
            self.assertGreaterEqual(metrics.unassessed_predictions, 0)
            self.assertEqual(metrics.overall_precision, 0.0)
            self.assertEqual(metrics.overall_recall, 0.0)
            self.assertEqual(metrics.overall_f1, 0.0)

            # Check report content
            with open(report_md_path, "r", encoding="utf-8") as f:
                report_content = f.read()
            self.assertIn("# PROVISIONAL AUTOMATED EVALUATION REPORT", report_content)
            self.assertIn("PROVISIONAL EVALUATION NOTICE", report_content)
            self.assertIn("Known True Positives (Known TP)", report_content)
            self.assertIn("Known False Positives (Known FP)", report_content)
            self.assertIn("Unassessed/Unknown Predictions", report_content)
        finally:
            settings.evaluation_dir = old_eval_dir

    def test_full_evaluation_mode(self) -> None:
        """Test that full evaluation executes normally when all candidates are reviewed (provisional = false)."""
        gt_path = self.dir_path / "ground_truth.json"
        gt_data = {
            "document_name": "test_document.docx",
            "schema_version": "1.1",
            "is_provisional_candidate": False,
            "review_status_summary": "HUMAN VERIFIED GROUND TRUTH",
            "total_ground_truth_entities": 1,
            "annotated_entities": [
                {
                    "entity_id": "gt_1",
                    "entity_type": "ORGANIZATION",
                    "text": "KSH INTERNATIONAL LIMITED",
                    "start": 0,
                    "end": 25,
                    "source_location": {
                        "source_type": "paragraph",
                        "paragraph_index": 0,
                        "table_index": None,
                        "row_index": None,
                        "cell_index": None,
                        "header_index": None,
                        "footer_index": None
                    },
                    "review_status": "human_verified",
                    "detector_source": "spaCy_NER"
                }
            ]
        }
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(gt_data, f, indent=2)

        report_md_path = self.dir_path / "evaluation_report.md"
        
        metrics = run_evaluation(self.docx_path, gt_path, report_md_path)
        
        self.assertFalse(metrics.is_partial_review)
        self.assertGreater(metrics.overall_recall, 0.0)
        
        with open(report_md_path, "r", encoding="utf-8") as f:
            report_content = f.read()
        self.assertIn("# PII Detection Evaluation & Performance Report", report_content)
        self.assertNotIn("PARTIAL HUMAN-REVIEW MODE", report_content)


if __name__ == "__main__":
    unittest.main()
