"""Detection pipeline orchestrator and overlap resolution engine."""

import re
from typing import Dict, List, Set, Tuple

from src.detectors.address_detector import AddressDetector
from src.detectors.base import BaseDetector
from src.detectors.credit_card_detector import CreditCardDetector
from src.detectors.dob_detector import DOBDetector
from src.detectors.email_detector import EmailDetector
from src.detectors.ip_detector import IPDetector
from src.detectors.ner_detector import NERDetector
from src.detectors.phone_detector import PhoneDetector
from src.detectors.ssn_detector import SSNDetector
from src.models import PIIEntity, TextChunk


class DetectionPipeline:
    """Orchestrates registered detectors, resolves overlapping PII entity spans, and propagates known entities."""

    # Category priority weighting for conflict resolution (higher value = higher priority)
    ENTITY_PRIORITY = {
        "EMAIL": 10,
        "PHONE": 10,
        "SSN": 10,
        "CREDIT_CARD": 10,
        "IP_ADDRESS": 10,
        "DOB": 9,
        "ADDRESS": 8,
        "ORGANIZATION": 6,
        "PERSON": 5,
    }

    def __init__(self, detectors: List[BaseDetector] | None = None) -> None:
        self.detectors: List[BaseDetector] = detectors or []

    def register_detector(self, detector: BaseDetector) -> None:
        """Register a new detector instance into the pipeline."""
        self.detectors.append(detector)

    def _same_source_location(self, e1: PIIEntity, e2: PIIEntity) -> bool:
        """Return True if both entities share the same DOCX source location.

        Two entities can only truly overlap if they live in the same paragraph,
        table cell, header, or footer. Entities in different table cells that happen
        to share identical local character offsets are NOT overlapping — they are
        independent occurrences in distinct document locations.
        """
        loc1 = e1.source_location
        loc2 = e2.source_location

        if loc1 is None and loc2 is None:
            return True
        if loc1 is None or loc2 is None:
            return False

        return (
            loc1.source_type == loc2.source_type
            and loc1.paragraph_index == loc2.paragraph_index
            and loc1.table_index == loc2.table_index
            and loc1.row_index == loc2.row_index
            and loc1.cell_index == loc2.cell_index
            and loc1.header_index == loc2.header_index
            and loc1.footer_index == loc2.footer_index
        )

    def _are_overlapping(self, e1: PIIEntity, e2: PIIEntity) -> bool:
        """Check if two entities have overlapping character spans."""
        return max(e1.start, e2.start) < min(e1.end, e2.end)

    def _resolve_overlap(self, e1: PIIEntity, e2: PIIEntity) -> PIIEntity:
        """Determine the winning entity between two overlapping spans based on priority rules.

        Rules:
        0. If one entity is a co-reference propagated match whose text is a clean prefix of the
           other entity's text, prefer the propagated (known-boundary) entity. This corrects NER
           over-spans such as 'Sarthak Malvadkar Company' when the confirmed entity is
           'Sarthak Malvadkar'.
        1. Higher entity category priority wins (e.g. EMAIL > PERSON).
        2. If equal category priority, longer span length wins (e.g. "John Smith" > "John").
        3. If equal span length, higher confidence score wins.
        """
        p1 = self.ENTITY_PRIORITY.get(e1.entity_type, 1)
        p2 = self.ENTITY_PRIORITY.get(e2.entity_type, 1)

        # Rule 0: Propagated known-entity corrects NER over-span.
        # If one entity is propagated and the other (NER) has a text that starts with the
        # propagated entity's text followed by a non-name separator (space/punctuation),
        # then the propagated entity has the correct boundary.
        if p1 == p2:  # only applies within same priority tier (e.g., PERSON vs PERSON)
            if "_propagated" in e1.detector and e2.original_text.startswith(e1.original_text):
                suffix = e2.original_text[len(e1.original_text):]
                if suffix and not suffix[0].isalpha():
                    return e1
            if "_propagated" in e2.detector and e1.original_text.startswith(e2.original_text):
                suffix = e1.original_text[len(e2.original_text):]
                if suffix and not suffix[0].isalpha():
                    return e2

        # Rule 0b: Sub-span containment.
        # If one entity is completely contained within the other, always prefer the longer
        # entity to prevent partial redaction leaks (e.g. a last name 'Hegde' misclassified
        # as ORGANIZATION preferred over the full PERSON name 'Kushal Subbayya Hegde').
        len1 = e1.end - e1.start
        len2 = e2.end - e2.start
        if e1.start >= e2.start and e1.end <= e2.end and len1 < len2:
            return e2
        if e2.start >= e1.start and e2.end <= e1.end and len2 < len1:
            return e1

        # Rule 1: High precision category priority
        if p1 != p2:
            return e1 if p1 > p2 else e2

        # Rule 2: Span length preference
        len1 = e1.end - e1.start
        len2 = e2.end - e2.start
        if len1 != len2:
            return e1 if len1 > len2 else e2

        # Rule 3: Confidence score
        if e1.confidence != e2.confidence:
            return e1 if e1.confidence > e2.confidence else e2

        # Tie-breaker
        return e1

    def deduplicate_and_resolve_overlaps(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Normalize metadata, remove exact duplicates, and resolve overlapping spans.

        Args:
            entities: Raw list of detected PIIEntity objects from all detectors.

        Returns:
            Clean, deduplicated, non-overlapping list of PIIEntity objects sorted by start offset.

        NOTE: Overlap resolution only occurs between entities sharing the SAME source location.
        Entities in different table cells (even with identical local offsets) are independent and
        are never merged or dropped due to apparent offset collision.
        """
        if not entities:
            return []

        # Step 1: Remove exact duplicates — key includes full source location so entities in
        # different table cells with identical local offsets are NOT collapsed.
        unique_entities: List[PIIEntity] = []
        seen_keys: Set[Tuple] = set()

        for e in entities:
            loc_tuple = (
                e.source_location.source_type if e.source_location else "",
                e.source_location.paragraph_index if e.source_location else None,
                e.source_location.table_index if e.source_location else None,
                e.source_location.row_index if e.source_location else None,
                e.source_location.cell_index if e.source_location else None,
                e.source_location.header_index if e.source_location else None,
                e.source_location.footer_index if e.source_location else None,
            )
            key = (e.entity_type, e.original_text, e.start, e.end, loc_tuple)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_entities.append(e)

        # Step 2: Sort by source location then start offset ascending, longer spans first
        def _sort_key(e: PIIEntity) -> Tuple:
            loc = e.source_location
            return (
                str(loc.source_type) if loc else "",
                loc.table_index if loc and loc.table_index is not None else -1,
                loc.row_index if loc and loc.row_index is not None else -1,
                loc.cell_index if loc and loc.cell_index is not None else -1,
                loc.paragraph_index if loc and loc.paragraph_index is not None else -1,
                e.start,
                -(e.end - e.start),
            )

        unique_entities.sort(key=_sort_key)

        # Step 3: Non-overlapping graph resolution — only compare entities sharing the same
        # source location. Entities in different table cells NEVER overlap each other.
        resolved: List[PIIEntity] = []

        for candidate in unique_entities:
            overlapping_idx = -1
            for idx, existing in enumerate(resolved):
                # Only entities in the same source location can truly overlap
                if not self._same_source_location(candidate, existing):
                    continue
                if self._are_overlapping(candidate, existing):
                    overlapping_idx = idx
                    break

            if overlapping_idx == -1:
                resolved.append(candidate)
            else:
                existing = resolved[overlapping_idx]
                winner = self._resolve_overlap(candidate, existing)
                resolved[overlapping_idx] = winner

        resolved.sort(key=_sort_key)
        return resolved

    def process_chunk(self, chunk: TextChunk) -> List[PIIEntity]:
        """Run all registered detectors on a single chunk and resolve overlaps.

        Args:
            chunk: TextChunk containing document text and source metadata.

        Returns:
            List of non-overlapping PIIEntity objects for this chunk.
        """
        raw_entities: List[PIIEntity] = []
        for detector in self.detectors:
            raw_entities.extend(detector.detect(chunk))

        return self.deduplicate_and_resolve_overlaps(raw_entities)

    def process_chunks(self, chunks: List[TextChunk]) -> List[PIIEntity]:
        """Run all registered detectors across chunks with document-wide co-reference propagation.

        Args:
            chunks: List of TextChunk objects.

        Returns:
            List of non-overlapping PIIEntity objects across all chunks.
        """
        # Pass 1: Collect initial detections per chunk
        chunk_detections: Dict[str, List[PIIEntity]] = {}
        all_initial_entities: List[PIIEntity] = []

        for chunk in chunks:
            raw_chunk_ents: List[PIIEntity] = []
            for detector in self.detectors:
                raw_chunk_ents.extend(detector.detect(chunk))
            
            resolved_chunk_ents = self.deduplicate_and_resolve_overlaps(raw_chunk_ents)
            chunk_detections[chunk.chunk_id] = resolved_chunk_ents
            all_initial_entities.extend(resolved_chunk_ents)

        # Pass 2: Build known high-confidence entity set for document-wide co-reference propagation
        known_entity_map: Dict[str, Tuple[str, float, str]] = {}
        for e in all_initial_entities:
            clean_text = e.original_text.strip()
            # Propagate multi-word PERSON/ORGANIZATION names and distinct PII strings
            if (
                e.entity_type in ("PERSON", "ORGANIZATION", "EMAIL", "PHONE")
                and len(clean_text) >= 3
                and e.confidence >= 0.80
            ):
                # Require at least 2 words for person names to prevent single-word false positive propagation
                if e.entity_type == "PERSON" and len(clean_text.split()) < 2:
                    continue
                if clean_text not in known_entity_map:
                    known_entity_map[clean_text] = (e.entity_type, e.confidence, e.detector)

        # Pass 3: Propagate known entities to chunks missing them
        final_entities: List[PIIEntity] = []
        for chunk in chunks:
            chunk_ents = list(chunk_detections.get(chunk.chunk_id, []))
            
            # Keep track of spans already covered by exact match
            existing_spans = {(e.start, e.end) for e in chunk_ents}

            for entity_text, (etype, conf, det) in known_entity_map.items():
                if entity_text in chunk.text:
                    pattern = re.escape(entity_text)
                    for m in re.finditer(pattern, chunk.text):
                        start, end = m.start(), m.end()
                        # Check if this exact span is already in chunk_ents
                        if (start, end) not in existing_spans:
                            propagated_ent = PIIEntity(
                                entity_type=etype,
                                original_text=entity_text,
                                start=start,
                                end=end,
                                confidence=conf,
                                detector=f"{det}_propagated",
                                source_location=chunk.source_location,
                            )
                            chunk_ents.append(propagated_ent)
                            existing_spans.add((start, end))

            # Resolve any new overlaps created by propagation
            resolved_chunk = self.deduplicate_and_resolve_overlaps(chunk_ents)
            final_entities.extend(resolved_chunk)

        return final_entities


def create_default_pipeline() -> DetectionPipeline:
    """Factory function creating a DetectionPipeline populated with all 8 detectors."""
    pipeline = DetectionPipeline()
    pipeline.register_detector(EmailDetector())
    pipeline.register_detector(PhoneDetector())
    pipeline.register_detector(SSNDetector())
    pipeline.register_detector(CreditCardDetector())
    pipeline.register_detector(IPDetector())
    pipeline.register_detector(DOBDetector())
    pipeline.register_detector(AddressDetector())
    pipeline.register_detector(NERDetector())
    return pipeline
