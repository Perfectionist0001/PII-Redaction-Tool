"""Unit tests for Pseudonymizer deterministic synthetic data generation."""

import unittest
from src.models import PIIEntity, SourceLocation, SourceType
from src.redaction.pseudonymizer import Pseudonymizer


class TestPseudonymizer(unittest.TestCase):
    """Test suite for Pseudonymizer determinism, category formatting, and mapping isolation."""

    def setUp(self) -> None:
        """Initialize Pseudonymizer instance."""
        self.pseudonymizer = Pseudonymizer(seed=42)

    def test_same_original_produces_same_replacement(self) -> None:
        """Verify that identical original entities produce 100% identical synthetic replacements."""
        original_person = "Rashi Patil"
        original_email = "rashi.patil@gmail.com"

        # Generate replacement 20 times for person
        person_replacements = [
            self.pseudonymizer.generate_replacement("PERSON", original_person)
            for _ in range(20)
        ]
        self.assertEqual(len(set(person_replacements)), 1)

        # Generate replacement 20 times for email
        email_replacements = [
            self.pseudonymizer.generate_replacement("EMAIL", original_email)
            for _ in range(20)
        ]
        self.assertEqual(len(set(email_replacements)), 1)

    def test_different_originals_produce_different_replacements(self) -> None:
        """Verify that different original entities produce distinct synthetic replacements."""
        rep1 = self.pseudonymizer.generate_replacement("PERSON", "Rashi Patil")
        rep2 = self.pseudonymizer.generate_replacement("PERSON", "Sarthak Malvadkar")

        self.assertNotEqual(rep1, rep2)

    def test_different_entity_types_isolated_in_mapping(self) -> None:
        """Verify that different entity types sharing the same text string do not collide."""
        person_rep = self.pseudonymizer.generate_replacement("PERSON", "Acme")
        org_rep = self.pseudonymizer.generate_replacement("ORGANIZATION", "Acme")

        self.assertNotEqual(person_rep, org_rep)

    def test_replacement_domain_formatting(self) -> None:
        """Verify that entity replacement strings conform to domain and security specifications."""
        email_rep = self.pseudonymizer.generate_replacement("EMAIL", "test@domain.com")
        self.assertTrue(email_rep.endswith("@example.com"))

        phone_rep = self.pseudonymizer.generate_replacement("PHONE", "+91 9876543210")
        self.assertTrue(phone_rep.startswith("+91 99"))

        ip_rep = self.pseudonymizer.generate_replacement("IP_ADDRESS", "10.0.0.1")
        self.assertTrue(ip_rep.startswith("192.0.2."))

        cc_rep = self.pseudonymizer.generate_replacement("CREDIT_CARD", "4111 1111 1111 1111")
        self.assertTrue(cc_rep.startswith("4000 "))

        ssn_rep = self.pseudonymizer.generate_replacement("SSN", "123-45-6789")
        self.assertTrue(ssn_rep.startswith("000-"))

        dob_rep = self.pseudonymizer.generate_replacement("DOB", "15 August 1998")
        self.assertEqual(dob_rep, "1990-01-01")

    def test_assign_replacements_updates_entity_objects(self) -> None:
        """Verify assign_replacements populates replacement attribute on PIIEntity objects."""
        loc = SourceLocation(source_type=SourceType.PARAGRAPH, paragraph_index=0)
        entities = [
            PIIEntity("PERSON", "Rashi Patil", 0, 11, 0.85, "spaCy_NER", source_location=loc),
            PIIEntity("EMAIL", "rashi.patil@gmail.com", 12, 33, 1.0, "email_detector", source_location=loc),
        ]

        updated = self.pseudonymizer.assign_replacements(entities)

        self.assertIsNotNone(updated[0].replacement)
        self.assertIsNotNone(updated[1].replacement)
        self.assertTrue(updated[1].replacement.endswith("@example.com"))


if __name__ == "__main__":
    unittest.main()
