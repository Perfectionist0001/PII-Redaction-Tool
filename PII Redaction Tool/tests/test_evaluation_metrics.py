"""Unit tests for evaluation metric calculations (Precision, Recall, F1, Token-Level Accuracy)."""

import unittest
from src.evaluation.metrics import MetricsCalculator, TokenAccuracyMetrics
from src.models import PIIEntity, SourceLocation, SourceType, TextChunk


class TestEvaluationMetrics(unittest.TestCase):
    """Test suite for entity-level and token-level metric calculations."""

    def test_category_metrics_calculation(self) -> None:
        """Test calculation of TP, FP, FN, Precision, Recall, and F1 for a category."""
        loc_p0 = ("paragraph", 0, None, None, None, None, None)
        predictions = [
            (loc_p0, 0, 10, "John Smith"),
            (loc_p0, 20, 30, "Fake Corp"),
        ]
        ground_truth = [
            (loc_p0, 0, 10, "John Smith"),
            (loc_p0, 40, 50, "Jane Doe"),
        ]

        metrics = MetricsCalculator.calculate_category_metrics(
            "PERSON", predictions, ground_truth
        )

        self.assertEqual(metrics.true_positives, 1)
        self.assertEqual(metrics.false_positives, 1)
        self.assertEqual(metrics.false_negatives, 1)
        self.assertEqual(metrics.total_predictions, 2)
        self.assertEqual(metrics.total_ground_truth, 2)

        self.assertAlmostEqual(metrics.precision, 0.5)
        self.assertAlmostEqual(metrics.recall, 0.5)
        self.assertAlmostEqual(metrics.f1_score, 0.5)

    def test_zero_ground_truth_returns_none(self) -> None:
        """Test that categories with zero ground-truth instances report None (N/A) scores."""
        predictions = []
        ground_truth = []

        metrics = MetricsCalculator.calculate_category_metrics(
            "SSN", predictions, ground_truth
        )

        self.assertEqual(metrics.true_positives, 0)
        self.assertEqual(metrics.false_positives, 0)
        self.assertEqual(metrics.false_negatives, 0)
        self.assertIsNone(metrics.precision)
        self.assertIsNone(metrics.recall)
        self.assertIsNone(metrics.f1_score)

    def test_token_accuracy_calculation(self) -> None:
        """Test token-level binary classification accuracy calculation."""
        text = "John Smith lives in Pune today."
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)
        chunk = TextChunk(chunk_id="p0", text=text, source_location=loc)

        # GT span: "John Smith" (0..10) -> tokens "John", "Smith" are Positive (2)
        # Non-PII tokens: "lives", "in", "Pune", "today." are Negative (4)
        ground_truth = [
            {
                "entity_type": "PERSON",
                "text": "John Smith",
                "start": 0,
                "end": 10,
                "source_location": {"source_type": "paragraph", "paragraph_index": 0},
            }
        ]

        # Prediction span: "John Smith" (0..10)
        predictions = [
            PIIEntity(
                entity_type="PERSON",
                original_text="John Smith",
                start=0,
                end=10,
                confidence=1.0,
                detector="test",
                source_location=loc,
            )
        ]

        tok_metrics = MetricsCalculator.calculate_token_accuracy(
            [chunk], predictions, ground_truth
        )

        self.assertEqual(tok_metrics.total_tokens, 6)
        self.assertEqual(tok_metrics.tp_tokens, 2)  # John, Smith
        self.assertEqual(tok_metrics.tn_tokens, 4)  # lives, in, Pune, today.
        self.assertEqual(tok_metrics.fp_tokens, 0)
        self.assertEqual(tok_metrics.fn_tokens, 0)
        self.assertAlmostEqual(tok_metrics.accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()
