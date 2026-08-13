"""Configuration settings for PII Redaction Tool."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Settings:
    """Project-wide settings and directory paths."""

    project_root: Path = Path(__file__).parent.parent
    input_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "input")
    output_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "output")
    docs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "docs")
    evaluation_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "evaluation")
    primary_input_file: Path = field(
        default_factory=lambda: Path(__file__).parent.parent / "input" / "Red Herring Prospectus.docx"
    )

    target_entity_types: List[str] = field(
        default_factory=lambda: [
            "FULL_NAME",
            "EMAIL",
            "PHONE",
            "COMPANY_NAME",
            "ADDRESS",
            "SSN",
            "CREDIT_CARD",
            "DOB",
            "IP_ADDRESS",
        ]
    )


settings = Settings()
