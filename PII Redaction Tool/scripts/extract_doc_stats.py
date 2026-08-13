"""Single source-of-truth document statistics extractor.

Run this to regenerate authoritative document statistics that should be used
in PROJECT_ANALYSIS.md, README.md, and any other documentation.

Usage:
    python scripts/extract_doc_stats.py
    python scripts/extract_doc_stats.py --output docs/doc_stats.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Make src importable from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.docx_extractor import DOCXExtractor


def count_tokens(text: str) -> int:
    """Count whitespace-delimited tokens in text."""
    return len(re.findall(r"\S+", text))


def extract_doc_stats(docx_path: Path) -> dict:
    """Extract authoritative document statistics from a DOCX file.

    Returns a dict with the following keys:
        file_name                  : str
        top_level_paragraphs       : int  (doc.paragraphs — body only)
        tables_count               : int
        table_cells_count          : int  (raw cell count, may include merged duplicates)
        table_paragraphs_count     : int  (total paragraphs inside all table cells)
        header_footer_chunks_count : int  (non-empty header/footer paragraph chunks)
        total_non_empty_chunks     : int  (all non-empty text chunks extracted)
        total_extracted_chars      : int  (sum of len(chunk.text) for all non-empty chunks)
        total_extracted_tokens     : int  (whitespace-delimited token count across all chunks)
    """
    extractor = DOCXExtractor(docx_path)
    summary = extractor.get_summary()

    # Get non-empty chunks for token counting
    chunks = extractor.extract_chunks(include_empty=False)
    total_chars = sum(len(c.text) for c in chunks)
    total_tokens = sum(count_tokens(c.text) for c in chunks)

    return {
        "file_name": summary["file_name"],
        "top_level_paragraphs": summary["top_paragraphs_count"],
        "tables_count": summary["tables_count"],
        "table_cells_count": summary["table_cells_count"],
        "table_paragraphs_count": summary["table_paragraphs_count"],
        "header_footer_chunks_count": summary["header_footer_chunks_count"],
        "total_non_empty_chunks": len(chunks),
        "total_extracted_chars": total_chars,
        "total_extracted_tokens": total_tokens,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract authoritative DOCX statistics")
    parser.add_argument(
        "--input",
        default='input/Red Herring Prospectus.docx',
        help="Path to input DOCX file (relative to project root)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write stats JSON (prints to stdout if omitted)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    docx_path = project_root / args.input

    if not docx_path.exists():
        print(f"ERROR: File not found: {docx_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting statistics from: {docx_path.name} ...", file=sys.stderr)
    stats = extract_doc_stats(docx_path)

    output = json.dumps(stats, indent=2)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"Stats written to: {out_path.resolve()}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
