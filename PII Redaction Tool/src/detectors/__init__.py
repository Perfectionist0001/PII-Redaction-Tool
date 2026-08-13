"""Detectors module."""

from src.detectors.address_detector import AddressDetector
from src.detectors.base import BaseDetector
from src.detectors.credit_card_detector import CreditCardDetector
from src.detectors.dob_detector import DOBDetector
from src.detectors.email_detector import EmailDetector
from src.detectors.ip_detector import IPDetector
from src.detectors.ner_detector import NERDetector
from src.detectors.phone_detector import PhoneDetector
from src.detectors.ssn_detector import SSNDetector

__all__ = [
    "BaseDetector",
    "EmailDetector",
    "PhoneDetector",
    "SSNDetector",
    "CreditCardDetector",
    "IPDetector",
    "DOBDetector",
    "NERDetector",
    "AddressDetector",
]
