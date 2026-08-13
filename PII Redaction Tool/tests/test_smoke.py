"""Smoke tests verifying module imports and instantiation."""

import unittest

from src.config import settings
from src.detection_pipeline import create_default_pipeline
from src.detectors import (
    AddressDetector,
    DOBDetector,
    EmailDetector,
    IPDetector,
    NERDetector,
    PhoneDetector,
)
from src.evaluation.metrics import (
    CategoryMetrics,
    MetricsCalculator,
    OverallEvaluationMetrics,
    TokenAccuracyMetrics,
)
from src.extractors.docx_extractor import DOCXExtractor
from src.models import PIIEntity, SourceLocation, SourceType
from src.redaction.docx_redactor import DOCXRedactor
from src.redaction.pseudonymizer import Pseudonymizer


class TestSmoke(unittest.TestCase):
    """Smoke test suite checking package imports and basic instantiation."""

    def test_imports_and_instantiation(self) -> None:
        """Verify key components instantiate without errors."""
        pipeline = create_default_pipeline()
        self.assertIsNotNone(pipeline)

        pseudonymizer = Pseudonymizer()
        self.assertIsNotNone(pseudonymizer)

        calc = MetricsCalculator()
        self.assertIsNotNone(calc)

    def test_settings_loaded(self) -> None:
        """Verify application settings loaded."""
        self.assertIsNotNone(settings.project_root)
        self.assertTrue(settings.primary_input_file.exists())


if __name__ == "__main__":
    unittest.main()
