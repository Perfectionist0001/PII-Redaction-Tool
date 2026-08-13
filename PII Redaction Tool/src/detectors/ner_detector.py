"""Named Entity Recognition (NER) detector using local spaCy model."""

from typing import Any, ClassVar, Dict, List, Optional

from src.detectors.base import BaseDetector
from src.models import PIIEntity, TextChunk


class NERDetector(BaseDetector):
    """Detector for identifying Person and Organization entities via local spaCy NER."""

    # Class-level cached spaCy models keyed by model_name to ensure loading once per model
    _nlp_models: ClassVar[Dict[str, Any]] = {}

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        self.model_name = model_name
        self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> None:
        """Load and cache the spaCy model once across detector instances."""
        if self.model_name not in NERDetector._nlp_models:
            try:
                import spacy
            except ImportError:
                raise ImportError(
                    "spaCy package is not installed. "
                    "Please install it using: python -m pip install spacy"
                )

            try:
                NERDetector._nlp_models[self.model_name] = spacy.load(self.model_name)
            except Exception as err:
                raise RuntimeError(
                    f"spaCy model '{self.model_name}' is not installed or failed to load. "
                    f"Please install the model using: python -m spacy download {self.model_name}"
                ) from err

    @property
    def detector_name(self) -> str:
        """Detector name."""
        return "spaCy_NER"

    @property
    def supported_entity_types(self) -> List[str]:
        """Supported PII categories."""
        return ["PERSON", "ORGANIZATION"]

    def detect(self, chunk: TextChunk) -> List[PIIEntity]:
        """Detect PERSON and ORGANIZATION entities in a TextChunk.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of PIIEntity objects for detected PERSON and ORGANIZATION entities.
        """
        entities: List[PIIEntity] = []
        text = chunk.text

        if not text or not text.strip():
            return entities

        if self.model_name not in NERDetector._nlp_models:
            self._ensure_model_loaded()

        nlp_model = NERDetector._nlp_models[self.model_name]
        doc = nlp_model(text)

        # Mapping spaCy entity labels to required target categories
        LABEL_MAP = {
            "PERSON": "PERSON",
            "ORG": "ORGANIZATION",
        }

        for ent in doc.ents:
            if ent.label_ in LABEL_MAP:
                entities.append(
                    PIIEntity(
                        entity_type=LABEL_MAP[ent.label_],
                        original_text=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.85,
                        detector=self.detector_name,
                        source_location=chunk.source_location,
                    )
                )

        return entities
