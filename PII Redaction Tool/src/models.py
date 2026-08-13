"""Data models for text chunks, PII entities, run information, and source locations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class SourceType(str, Enum):
    """Types of source document elements."""

    PARAGRAPH = "paragraph"
    TABLE_CELL = "table_cell"
    HEADER = "header"
    FOOTER = "footer"


@dataclass
class SourceLocation:
    """Detailed source location mapping back to paragraph, table cell, or header/footer."""

    source_type: SourceType
    paragraph_index: Optional[int] = None
    table_index: Optional[int] = None
    row_index: Optional[int] = None
    cell_index: Optional[int] = None
    header_index: Optional[int] = None
    footer_index: Optional[int] = None
    run_index: Optional[int] = None


@dataclass
class RunInfo:
    """Information about an individual XML run inside a paragraph."""

    run_index: int
    text: str
    start_pos: int
    end_pos: int
    docx_run: Any = None  # Reference to underlying python-docx Run object


@dataclass
class TextChunk:
    """Container for an extracted text unit with source metadata and run-level details."""

    chunk_id: str
    text: str
    source_location: SourceLocation
    runs: List[RunInfo] = field(default_factory=list)
    docx_element: Any = None  # Reference to underlying python-docx Paragraph or Cell object
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PIIEntity:
    """Representation of a detected PII entity with source mapping and replacement."""

    entity_type: str
    original_text: str
    start: int
    end: int
    confidence: float = 1.0
    detector: str = ""
    replacement: Optional[str] = None
    source_location: Optional[SourceLocation] = None

    @property
    def source_identity(self) -> Dict[str, Any]:
        """Return a stable dictionary identity containing only applicable source location fields and span offsets."""
        identity: Dict[str, Any] = {
            "entity_type": self.entity_type,
            "start": self.start,
            "end": self.end,
        }
        if self.source_location:
            loc = self.source_location
            identity["source_type"] = loc.source_type.value if isinstance(loc.source_type, SourceType) else str(loc.source_type)
            if loc.paragraph_index is not None:
                identity["paragraph_index"] = loc.paragraph_index
            if loc.table_index is not None:
                identity["table_index"] = loc.table_index
            if loc.row_index is not None:
                identity["row_index"] = loc.row_index
            if loc.cell_index is not None:
                identity["cell_index"] = loc.cell_index
            if loc.header_index is not None:
                identity["header_index"] = loc.header_index
            if loc.footer_index is not None:
                identity["footer_index"] = loc.footer_index
        return identity

    @property
    def identity_key(self) -> Tuple:
        """Return a hashable tuple representing the unique entity identity across the document."""
        loc_tuple = (
            self.source_location.source_type.value if self.source_location and isinstance(self.source_location.source_type, SourceType) else (str(self.source_location.source_type) if self.source_location else None),
            self.source_location.paragraph_index if self.source_location else None,
            self.source_location.table_index if self.source_location else None,
            self.source_location.row_index if self.source_location else None,
            self.source_location.cell_index if self.source_location else None,
            self.source_location.header_index if self.source_location else None,
            self.source_location.footer_index if self.source_location else None,
        )
        return (self.entity_type, self.start, self.end, loc_tuple)

