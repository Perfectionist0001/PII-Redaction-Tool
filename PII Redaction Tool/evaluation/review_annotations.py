"""Human-review workflow CLI and manager for ground-truth annotations."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings


class GroundTruthReviewer:
    """Manages human review of candidate annotations to produce evaluation/ground_truth.json."""

    def __init__(self, candidates_json_path: Path | str, output_path: Optional[Path | str] = None) -> None:
        self.candidates_json_path = Path(candidates_json_path)
        if not self.candidates_json_path.exists():
            raise FileNotFoundError(
                f"Candidates file not found at {self.candidates_json_path}. "
                "Run candidate_generator first."
            )

        with open(self.candidates_json_path, "r", encoding="utf-8") as f:
            self.candidate_data = json.load(f)

        self.document_name: str = self.candidate_data.get(
            "document_name", "Red Herring Prospectus.docx"
        )
        self.raw_candidates: List[Dict[str, Any]] = self.candidate_data.get(
            "candidates", []
        )

        self.ground_truth_entities: List[Dict[str, Any]] = []
        self.rejected_candidates: List[Dict[str, Any]] = []
        self.reviewed_candidate_ids = set()
        self.is_provisional: bool = True
        self.output_path = Path(output_path) if output_path else None

        # Load existing progress if verified file exists
        if self.output_path and self.output_path.exists():
            try:
                with open(self.output_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                self.ground_truth_entities = old_data.get("annotated_entities", [])
                self.rejected_candidates = old_data.get("rejected_candidates", [])
                self.reviewed_candidate_ids = set(old_data.get("reviewed_candidate_ids", []))
                self.is_provisional = old_data.get("is_provisional_candidate", True)
                print(f"Loaded existing progress from {self.output_path}:")
                print(f"  Verified entities   : {len(self.ground_truth_entities)}")
                print(f"  Rejected candidates : {len(self.rejected_candidates)}")
                print(f"  Reviewed candidates : {len(self.reviewed_candidate_ids)}/{len(self.raw_candidates)}")
            except Exception as e:
                print(f"Warning: Could not load progress from {self.output_path}: {e}")

    def accept_candidate(
        self, candidate: Dict[str, Any], notes: Optional[str] = None, is_human: bool = False
    ) -> Dict[str, Any]:
        """Accept a candidate entity into the ground-truth set."""
        status = "human_verified" if is_human else "provisional_candidate"
        gt_entry = {
            "entity_id": f"gt_{len(self.ground_truth_entities) + 1}",
            "entity_type": candidate["entity_type"],
            "text": candidate["original_text"],
            "start": candidate["start"],
            "end": candidate["end"],
            "source_location": candidate.get("source_location"),
            "review_status": status,
            "detector_source": candidate.get("detector", ""),
            "auditor_notes": notes or ("Human verified" if is_human else "Provisional candidate annotation"),
        }
        self.ground_truth_entities.append(gt_entry)
        return gt_entry

    def reject_candidate(
        self, candidate: Dict[str, Any], reason: str = "False positive"
    ) -> None:
        """Reject a candidate entity as a false positive."""
        rej_entry = dict(candidate)
        rej_entry["rejection_reason"] = reason
        self.rejected_candidates.append(rej_entry)

    def change_entity_type(
        self, candidate: Dict[str, Any], new_entity_type: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Change the category of a candidate entity and accept it."""
        gt_entry = {
            "entity_id": f"gt_{len(self.ground_truth_entities) + 1}",
            "entity_type": new_entity_type.upper(),
            "text": candidate["original_text"],
            "start": candidate["start"],
            "end": candidate["end"],
            "source_location": candidate.get("source_location"),
            "review_status": "human_modified_type",
            "detector_source": candidate.get("detector", ""),
            "auditor_notes": notes or f"Reclassified from {candidate['entity_type']} to {new_entity_type}",
        }
        self.ground_truth_entities.append(gt_entry)
        return gt_entry

    def correct_entity_span(
        self,
        candidate: Dict[str, Any],
        new_text: str,
        new_start: int,
        new_end: int,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Correct the text or character offsets of a candidate entity and accept it."""
        gt_entry = {
            "entity_id": f"gt_{len(self.ground_truth_entities) + 1}",
            "entity_type": candidate["entity_type"],
            "text": new_text,
            "start": new_start,
            "end": new_end,
            "source_location": candidate.get("source_location"),
            "review_status": "human_corrected_span",
            "detector_source": candidate.get("detector", ""),
            "auditor_notes": notes or f"Corrected text span from '{candidate['original_text']}' to '{new_text}'",
        }
        self.ground_truth_entities.append(gt_entry)
        return gt_entry

    def add_missing_annotation(
        self,
        entity_type: str,
        text: str,
        start: int,
        end: int,
        source_location: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Manually add a missing entity annotation not caught by automated detectors."""
        gt_entry = {
            "entity_id": f"gt_{len(self.ground_truth_entities) + 1}",
            "entity_type": entity_type.upper(),
            "text": text,
            "start": start,
            "end": end,
            "source_location": source_location or {},
            "review_status": "human_added_manually",
            "detector_source": "manual_annotation",
            "auditor_notes": notes or "Manually added during human review",
        }
        self.ground_truth_entities.append(gt_entry)
        return gt_entry

    def interactive_review(self) -> None:
        """Run an interactive console session for human review of candidates."""
        print("==================================================================")
        print("         HUMAN REVIEW GROUND TRUTH ANNOTATION REVIEWER            ")
        print("==================================================================")
        print("Instructions:")
        print("  [a] Accept candidate as genuine PII (human_verified)")
        print("  [r] Reject candidate as a false positive (exclude)")
        print("  [c] Change entity category type (human_modified_type)")
        print("  [e] Edit the text span or offsets (human_corrected_span)")
        print("  [m] Manually add a missing annotation (human_added_manually)")
        print("  [s] Skip candidate (present again next session)")
        print("  [q] Save current progress and quit")
        print("==================================================================")

        total = len(self.raw_candidates)
        i = 0
        while i < total:
            cand = self.raw_candidates[i]
            cid = cand.get("candidate_id")

            # Skip already reviewed candidates
            if cid in self.reviewed_candidate_ids:
                i += 1
                continue

            print(f"\n[{i+1}/{total}] Candidate ID: {cid}")
            print(f"  Category            : {cand['entity_type']}")
            print(f"  Text                : {cand['original_text']!r}")

            loc = cand.get("source_location", {})
            loc_str = loc.get("source_type", "unknown")
            if loc.get("paragraph_index") is not None:
                loc_str += f" index {loc['paragraph_index']}"
            if loc.get("table_index") is not None:
                loc_str += f" (Table {loc['table_index']}, Row {loc['row_index']}, Cell {loc['cell_index']})"
            
            print(f"  Source Location     : {loc_str}")
            print(f"  Context             : ...{cand.get('surrounding_context', '').strip()}...")
            print(f"  Detector (Confidence): {cand.get('detector', 'unknown')} (conf: {cand.get('confidence', 1.0)})")
            print("-" * 66)

            action = input("Action [a/r/c/e/m/s/q]: ").strip().lower()
            if action == "a":
                self.accept_candidate(cand, is_human=True)
                self.reviewed_candidate_ids.add(cid)
                i += 1
            elif action == "r":
                reason = input("Rejection reason (optional): ").strip()
                self.reject_candidate(cand, reason=reason or "False positive")
                self.reviewed_candidate_ids.add(cid)
                i += 1
            elif action == "c":
                new_type = input("Enter new entity type (e.g. PERSON, ORGANIZATION): ").strip().upper()
                if new_type:
                    self.change_entity_type(cand, new_type, notes="Reclassified during human review")
                    self.reviewed_candidate_ids.add(cid)
                    i += 1
                else:
                    print("Invalid type, candidate skipped.")
            elif action == "e":
                new_text = input(f"Enter corrected text (default: {cand['original_text']}): ").strip() or cand['original_text']
                try:
                    new_start = int(input(f"Enter start offset (default: {cand['start']}): ").strip() or str(cand['start']))
                    new_end = int(input(f"Enter end offset (default: {cand['end']}): ").strip() or str(cand['end']))
                    self.correct_entity_span(cand, new_text, new_start, new_end, notes="Corrected span during human review")
                    self.reviewed_candidate_ids.add(cid)
                    i += 1
                except ValueError:
                    print("Invalid offset values, candidate skipped.")
            elif action == "m":
                print("\n--- Manually Add Missing Entity ---")
                m_type = input("Category: ").strip().upper()
                m_text = input("Text: ").strip()
                try:
                    m_start = int(input("Start offset: ").strip())
                    m_end = int(input("End offset: ").strip())
                    s_type = input("Source type (paragraph/table_cell/header/footer): ").strip().lower()
                    m_loc = {"source_type": s_type}
                    if s_type == "paragraph":
                        m_loc["paragraph_index"] = int(input("Paragraph index: ").strip())
                    elif s_type == "table_cell":
                        m_loc["table_index"] = int(input("Table index: ").strip())
                        m_loc["row_index"] = int(input("Row index: ").strip())
                        m_loc["cell_index"] = int(input("Cell index: ").strip())
                        m_loc["paragraph_index"] = int(input("Paragraph index in cell: ").strip())
                    elif s_type == "header":
                        m_loc["header_index"] = int(input("Header index: ").strip())
                        m_loc["paragraph_index"] = int(input("Paragraph index: ").strip())
                    elif s_type == "footer":
                        m_loc["footer_index"] = int(input("Footer index: ").strip())
                        m_loc["paragraph_index"] = int(input("Paragraph index: ").strip())
                    
                    self.add_missing_annotation(m_type, m_text, m_start, m_end, source_location=m_loc, notes="Manually added by auditor")
                    print("Missing entity successfully added! Returning to current candidate.")
                except ValueError:
                    print("Invalid numeric values, entity not added.")
            elif action == "s":
                print("Skipping candidate for now.")
                i += 1
            elif action == "q":
                print("Quitting human review. Saving progress...")
                break
            else:
                print("Unknown action. Please enter a valid action choice.")

        # Determine provisional status
        if len(self.reviewed_candidate_ids) >= total:
            self.is_provisional = False
        else:
            self.is_provisional = True

    def apply_provisional_rules(self) -> None:
        """Apply project-specific candidate rules from GROUND_TRUTH_GUIDE.md to generate provisional ground truth."""
        self.is_provisional = True
        PUBLIC_REGULATORS = {
            "SEBI",
            "SECURITIES AND EXCHANGE BOARD OF INDIA",
            "ROC",
            "REGISTRAR OF COMPANIES",
            "RESERVE BANK OF INDIA",
            "RBI",
            "BSE",
            "BSE LIMITED",
            "NSE",
            "NATIONAL STOCK EXCHANGE OF INDIA LIMITED",
            "RED HERRING PROSPECTUS",
            "SECTION I - GENERAL",
            "TABLE OF CONTENTS",
            "COMPANIES ACT",
        }

        for cand in self.raw_candidates:
            etype = cand["entity_type"]
            otext = cand["original_text"].strip()

            if otext.upper() in PUBLIC_REGULATORS:
                self.reject_candidate(cand, reason="Public regulator or section heading (Rule 8)")
                continue

            if etype in ("SSN", "CREDIT_CARD", "DOB", "IP_ADDRESS") and cand.get("confidence", 0) < 0.90:
                self.reject_candidate(cand, reason="Low confidence non-verified candidate")
                continue

            if etype in ("EMAIL", "PHONE", "ADDRESS", "PERSON", "ORGANIZATION"):
                self.accept_candidate(
                    cand,
                    notes="Provisional candidate rule match against GROUND_TRUTH_GUIDE.md",
                    is_human=False,
                )
            else:
                self.reject_candidate(cand, reason="Unverified entity category")

    def save_ground_truth(self, output_path: Path | str) -> Path:
        """Save ground truth entities to JSON format."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        cat_counts: Dict[str, int] = {}
        for gt in self.ground_truth_entities:
            cat_counts[gt["entity_type"]] = cat_counts.get(gt["entity_type"], 0) + 1

        if not self.reviewed_candidate_ids:
            status_msg = "PROVISIONAL CANDIDATE ANNOTATIONS (Requires line-by-line human review)"
            self.is_provisional = True
        else:
            if len(self.reviewed_candidate_ids) >= len(self.raw_candidates):
                status_msg = "HUMAN VERIFIED GROUND TRUTH"
                self.is_provisional = False
            else:
                status_msg = "PARTIALLY HUMAN REVIEWED"
                self.is_provisional = True

        gt_data = {
            "document_name": self.document_name,
            "schema_version": "1.1",
            "is_provisional_candidate": self.is_provisional,
            "review_status_summary": status_msg,
            "total_ground_truth_entities": len(self.ground_truth_entities),
            "summary_by_category": cat_counts,
            "annotated_entities": self.ground_truth_entities,
            "reviewed_candidate_ids": list(self.reviewed_candidate_ids),
            "rejected_candidates": self.rejected_candidates,
        }

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(gt_data, f, indent=2, ensure_ascii=False)

        print(f"Ground Truth successfully saved to: {out_file.resolve()}")
        print(f"Status: {status_msg}")
        print(f"Total Ground Truth Entities: {len(self.ground_truth_entities)}")
        print(f"Summary by Category: {cat_counts}")
        return out_file


def main() -> None:
    """CLI entrypoint for ground-truth review workflow."""
    parser = argparse.ArgumentParser(description="Human-Review Ground Truth Annotation Utility")
    parser.add_argument(
        "--candidates",
        type=str,
        default=str(settings.evaluation_dir / "candidate_annotations.json"),
        help="Path to candidate_annotations.json",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Target path for ground_truth.json or ground_truth_verified.json",
    )
    parser.add_argument(
        "--provisional-rules",
        action="store_true",
        help="Apply provisional candidate rules from GROUND_TRUTH_GUIDE.md",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run an interactive console-based human review session",
    )

    args = parser.parse_args()

    # Determine default output path based on mode if not provided
    if args.output is None:
        if args.interactive:
            output_path = settings.evaluation_dir / "ground_truth_verified.json"
        else:
            output_path = settings.evaluation_dir / "ground_truth.json"
    else:
        output_path = Path(args.output)

    reviewer = GroundTruthReviewer(args.candidates, output_path=output_path)

    if args.interactive:
        reviewer.interactive_review()
    elif args.provisional_rules:
        reviewer.apply_provisional_rules()
    else:
        print(
            "[INFO] Neither --interactive nor --provisional-rules specified. "
            "Applying provisional rules (not human review). "
            "Run with --interactive for genuine human-reviewed ground truth."
        )
        reviewer.apply_provisional_rules()

    reviewer.save_ground_truth(output_path)


if __name__ == "__main__":
    main()
