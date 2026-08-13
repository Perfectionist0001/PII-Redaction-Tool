"""Deterministic synthetic data generator and pseudonymization engine."""

import hashlib
from typing import Dict, List, Optional, Tuple

from faker import Faker

from src.models import PIIEntity


class Pseudonymizer:
    """Assigns deterministic synthetic replacement values to detected PII entities."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        self.seed = seed
        self._fake = Faker()
        if seed is not None:
            Faker.seed(seed)

        # Internal cache mapping (entity_type, normalized_original_text) -> replacement
        self._mapping: Dict[Tuple[str, str], str] = {}

    def _generate_seed_int(self, entity_type: str, original_text: str) -> int:
        """Create a deterministic integer seed from entity type and original text string."""
        combined = f"{entity_type.upper()}:{original_text.strip().lower()}"
        hasher = hashlib.md5(combined.encode("utf-8"))
        return int(hasher.hexdigest(), 16) % (2**32)

    def generate_replacement(self, entity_type: str, original_text: str) -> str:
        """Generate or retrieve a deterministic synthetic replacement string.

        Args:
            entity_type: The category of the PII entity (e.g. EMAIL, PERSON).
            original_text: The original text string of the detected entity.

        Returns:
            A deterministic synthetic replacement string.
        """
        etype = entity_type.upper()
        norm_key = (etype, original_text.strip().lower())

        # Return cached replacement if previously generated
        if norm_key in self._mapping:
            return self._mapping[norm_key]

        # Seed Faker instance deterministically for this specific entity
        item_seed = self._generate_seed_int(etype, original_text)
        self._fake.seed_instance(item_seed)

        if etype == "EMAIL":
            # Reserved documentation domain
            user_part = self._fake.user_name()
            replacement = f"{user_part}@example.com"

        elif etype in ("PERSON", "FULL_NAME"):
            replacement = self._fake.name()

        elif etype in ("ORGANIZATION", "COMPANY_NAME"):
            replacement = f"{self._fake.company()}"

        elif etype == "PHONE":
            # Clearly synthetic Indian phone format
            replacement = f"+91 99{self._fake.numerify('########')}"

        elif etype == "ADDRESS":
            replacement = f"{self._fake.building_number()}, {self._fake.street_name()}, {self._fake.city()}, {self._fake.postcode()}, India"

        elif etype == "SSN":
            # Synthetic test SSN (prefix 000)
            replacement = f"000-{self._fake.numerify('##')}-{self._fake.numerify('####')}"

        elif etype == "CREDIT_CARD":
            # Recognized sandbox test card pattern (Visa 4000)
            replacement = f"4000 {self._fake.numerify('####')} {self._fake.numerify('####')} {self._fake.numerify('####')}"

        elif etype == "IP_ADDRESS":
            # RFC 5737 documentation test range (192.0.2.x)
            replacement = f"192.0.2.{self._fake.random_int(min=1, max=254)}"

        elif etype == "DOB":
            replacement = "1990-01-01"

        else:
            replacement = f"[REDACTED_{etype}]"

        self._mapping[norm_key] = replacement
        return replacement

    def assign_replacements(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Assign deterministic synthetic replacements to all PII entities.

        Args:
            entities: List of detected PIIEntity objects.

        Returns:
            List of PIIEntity objects updated with synthetic replacement values.
        """
        for entity in entities:
            entity.replacement = self.generate_replacement(
                entity.entity_type, entity.original_text
            )
        return entities
