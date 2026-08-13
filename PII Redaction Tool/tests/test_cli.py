"""Unit tests for PII Redaction Tool CLI orchestrator."""

import tempfile
import unittest
from pathlib import Path

from src.config import settings
from src.main import build_parser, run_pipeline


class TestCLI(unittest.TestCase):
    """Test suite for CLI argument parsing and run_pipeline execution."""

    def test_build_parser_defaults(self) -> None:
        """Verify CLI argument parser defaults."""
        parser = build_parser()
        args = parser.parse_args([])

        self.assertEqual(Path(args.input), settings.primary_input_file)
        self.assertFalse(args.evaluate)
        self.assertFalse(args.verbose)

    def test_run_pipeline_execution(self) -> None:
        """Test run_pipeline end-to-end execution on a temporary output file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            out_docx = Path(temp_dir) / "test_out.docx"
            exit_code = run_pipeline(
                input_path=settings.primary_input_file,
                output_path=out_docx,
                evaluate=False,
                verbose=False,
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(out_docx.exists())


if __name__ == "__main__":
    unittest.main()
