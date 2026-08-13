"""Full-document residual-PII validation utility.

Compares original vs redacted DOCX using the provisional annotation dataset as
a candidate source.  Produces evaluation/final_redaction_validation.json and
evaluation/final_redaction_validation.md.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.docx_extractor import DOCXExtractor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chunk_key_from_model(loc) -> Tuple:
    if not loc:
        return ("paragraph", None, None, None, None, None, None)
    return (
        loc.source_type.value,
        loc.paragraph_index,
        loc.table_index,
        loc.row_index,
        loc.cell_index,
        loc.header_index,
        loc.footer_index,
    )


def chunk_key_from_dict(sl: Dict[str, Any]) -> Tuple:
    return (
        sl.get("source_type", "paragraph"),
        sl.get("paragraph_index"),
        sl.get("table_index"),
        sl.get("row_index"),
        sl.get("cell_index"),
        sl.get("header_index"),
        sl.get("footer_index"),
    )


# Generic / provisional false-positive term list (lower-cased).
GENERIC_TERMS = {
    "company", "our company", "the company", "board", "offer",
    "promoters", "bidders", "directors", "mutual funds", "shareholders",
    "capital structure", "bid", "anchor investors", "scra", "goi",
    "government of india", "eu", "european union", "care report",
    "general information document", "financial data", "key financial",
    "restated financial statements", "pune", "mumbai", "india",
    "prospectus", "red herring prospectus",
    "conventional and general terms and abbreviations",
    "definitions", "definitions and abbreviations", "currency",
    "bid/offer closing day",
}


def is_generic(text: str) -> bool:
    lo = text.lower().strip()
    if lo in GENERIC_TERMS:
        return True
    if any(k in lo for k in ("directors", "promoters", "shareholders")):
        return True
    return False


# ---------------------------------------------------------------------------
# Repeated-entity check
# ---------------------------------------------------------------------------

REPEAT_TARGETS = [
    "CareEdge Research",
    # person names from annotated_entities (populated dynamically below)
]


def count_in_text(needle: str, haystack: str) -> int:
    """Count non-overlapping occurrences of needle in haystack."""
    return len(re.findall(re.escape(needle), haystack))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    original_docx = Path("input/Red Herring Prospectus.docx")
    redacted_docx = Path("output/redacted_prospectus.docx")
    gt_file = Path("evaluation/ground_truth_verified.json")

    for p in (original_docx, redacted_docx, gt_file):
        if not p.exists():
            print(f"ERROR: {p} not found.")
            sys.exit(1)

    print(f"Original  : {original_docx}")
    print(f"Redacted  : {redacted_docx}")
    print(f"GT source : {gt_file}")

    # ── Load ground truth ──────────────────────────────────────────────────
    with open(gt_file, "r", encoding="utf-8") as fh:
        gt_data = json.load(fh)
    annotated_entities: List[Dict] = gt_data.get("annotated_entities", [])

    # ── Extract chunks ─────────────────────────────────────────────────────
    print("Extracting original document chunks …")
    orig_chunks = DOCXExtractor(original_docx).extract_chunks(include_empty=False)
    print("Extracting redacted document chunks …")
    red_chunks  = DOCXExtractor(redacted_docx).extract_chunks(include_empty=False)

    # Index by coordinate key
    orig_map: Dict[Tuple, str] = {chunk_key_from_model(c.source_location): c.text for c in orig_chunks}
    red_map:  Dict[Tuple, str] = {chunk_key_from_model(c.source_location): c.text for c in red_chunks}

    # Full document text (for repeated-entity counts)
    orig_full = "\n".join(orig_map.values())
    red_full  = "\n".join(red_map.values())

    # ── Per-entity validation ──────────────────────────────────────────────
    ALL_CATS = ["PERSON", "EMAIL", "PHONE", "ORGANIZATION",
                "ADDRESS", "SSN", "CREDIT_CARD", "DOB", "IP_ADDRESS"]

    cat_stats: Dict[str, Dict[str, int]] = {
        c: {"checked": 0, "replaced": 0, "residual": 0} for c in ALL_CATS
    }

    total_checked = total_replaced = total_residual = 0
    actual_leak_count = 0
    provisional_fp_count = 0
    residual_records: List[Dict] = []

    person_names: List[str] = []
    org_names:    List[str] = []
    address_vals: List[str] = []
    email_vals:   List[str] = []
    phone_vals:   List[str] = []

    for ent in annotated_entities:
        cat  = ent["entity_type"]
        text = ent["text"]
        sl   = ent.get("source_location", {})
        key  = chunk_key_from_dict(sl)

        # Collect repeat targets by category
        if cat == "PERSON"  and text not in person_names: person_names.append(text)
        if cat == "ORGANIZATION" and text not in org_names:  org_names.append(text)
        if cat == "ADDRESS" and text not in address_vals: address_vals.append(text)
        if cat == "EMAIL"   and text not in email_vals:   email_vals.append(text)
        if cat == "PHONE"   and text not in phone_vals:   phone_vals.append(text)

        # Count occurrences in the chunk where the entity was annotated
        orig_text = orig_map.get(key, "")
        red_text  = red_map.get(key, "")

        orig_occ = count_in_text(text, orig_text) if orig_text else 1
        if orig_occ == 0:
            orig_occ = 1          # fallback: annotated, so existed at least once
        red_occ = count_in_text(text, red_text)

        total_checked  += orig_occ
        cat_stats[cat]["checked"] += orig_occ

        if red_occ > 0:
            # Some occurrences remain in the redacted version
            total_residual += red_occ
            cat_stats[cat]["residual"] += red_occ

            replaced_here = max(0, orig_occ - red_occ)
            total_replaced += replaced_here
            cat_stats[cat]["replaced"] += replaced_here

            classification = (
                "PROVISIONAL_FALSE_POSITIVE" if is_generic(text)
                else "ACTUAL_RESIDUAL_PII"
            )
            if classification == "ACTUAL_RESIDUAL_PII":
                actual_leak_count += red_occ
            else:
                provisional_fp_count += red_occ

            loc_str = ""
            if sl.get("paragraph_index") is not None:
                loc_str = f"paragraph:{sl['paragraph_index']}"
            elif sl.get("table_index") is not None:
                loc_str = f"table:{sl['table_index']} row:{sl.get('row_index')} cell:{sl.get('cell_index')}"

            residual_records.append({
                "entity_id":                ent.get("entity_id"),
                "category":                 cat,
                "text":                     text,
                "original_occurrence_count": orig_occ,
                "redacted_occurrence_count": red_occ,
                "source_location":          sl,
                "location_str":             loc_str,
                "classification":           classification,
            })
        else:
            total_replaced += orig_occ
            cat_stats[cat]["replaced"] += orig_occ

    # ── Repeated-entity counts (full-document) ─────────────────────────────
    repeat_rows: List[Dict] = []

    def _repeat_row(label: str, entity_text: str) -> Dict:
        orig_cnt = count_in_text(entity_text, orig_full)
        red_cnt  = count_in_text(entity_text, red_full)
        return {
            "label":        label,
            "text":         entity_text,
            "orig_count":   orig_cnt,
            "red_count":    red_cnt,
            "replaced":     max(0, orig_cnt - red_cnt),
            "residual":     red_cnt,
            "status":       "✅ OK" if red_cnt == 0 else "⚠️ RESIDUAL",
        }

    # CareEdge Research (explicit requirement)
    repeat_rows.append(_repeat_row("ORGANIZATION (explicit)", "CareEdge Research"))

    for name in person_names:
        repeat_rows.append(_repeat_row("PERSON", name))
    for name in org_names:
        repeat_rows.append(_repeat_row("ORGANIZATION", name))
    for val in address_vals:
        repeat_rows.append(_repeat_row("ADDRESS", val))
    for val in email_vals:
        repeat_rows.append(_repeat_row("EMAIL", val))
    for val in phone_vals:
        repeat_rows.append(_repeat_row("PHONE", val))

    # ── Determine PASS / FAIL ─────────────────────────────────────────────
    conclusion = (
        "PASS — NO ACTUAL RESIDUAL PII FOUND"
        if actual_leak_count == 0
        else "FAIL — ACTUAL RESIDUAL PII FOUND"
    )

    # ── JSON output ────────────────────────────────────────────────────────
    json_out = {
        "meta": {
            "original":            str(original_docx),
            "redacted":            str(redacted_docx),
            "ground_truth_source": str(gt_file),
        },
        "summary": {
            "total_candidate_pii_occurrences_checked": total_checked,
            "successfully_replaced_occurrences":       total_replaced,
            "residual_candidate_occurrences":          total_residual,
            "actual_residual_pii":                     actual_leak_count,
            "provisional_false_positives":             provisional_fp_count,
            "conclusion":                              conclusion,
        },
        "category_stats":         cat_stats,
        "residuals":              residual_records,
        "repeated_entity_checks": repeat_rows,
    }

    out_json = Path("evaluation/final_redaction_validation.json")
    out_md   = Path("evaluation/final_redaction_validation.md")

    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(json_out, fh, indent=2, ensure_ascii=False)
    print(f"JSON -> {out_json.resolve()}")

    # ── Markdown report ────────────────────────────────────────────────────
    L: List[str] = []

    L += [
        "# Final Redaction Validation",
        "",
        "## Source Documents",
        f"* **Original** : `{original_docx}`",
        f"* **Redacted** : `{redacted_docx}`",
        f"* **GT Source**: `{gt_file}`",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"* **Total Candidate PII Occurrences Checked** : `{total_checked}`",
        f"* **Successfully Replaced**                   : `{total_replaced}`",
        f"* **Residual Candidate Occurrences**          : `{total_residual}`",
        f"* **Actual Residual PII**                     : `{actual_leak_count}`",
        f"* **Provisional False Positives**             : `{provisional_fp_count}`",
        "",
        "---",
        "",
        "## Category Results",
        "",
        "| Category | Original Candidate Occ. | Successfully Replaced | Residual Occ. | Status |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]

    for cat in ALL_CATS:
        s = cat_stats[cat]
        cat_leaks = sum(
            r["redacted_occurrence_count"]
            for r in residual_records
            if r["category"] == cat and r["classification"] == "ACTUAL_RESIDUAL_PII"
        )
        status = "✅ OK" if cat_leaks == 0 else f"⚠️ {cat_leaks} LEAK(S)"
        L.append(
            f"| **{cat}** | `{s['checked']}` | `{s['replaced']}` | `{s['residual']}` | {status} |"
        )

    L += [
        "",
        "---",
        "",
        "## Repeated Entity Validation",
        "",
        "Occurrence counts measured across the entire document (all paragraphs + tables + headers + footers).",
        "",
        "| Label | Entity Text | Orig Count | Red Count | Replaced | Residual | Status |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |",
    ]

    for row in repeat_rows:
        L.append(
            f"| {row['label']} | `{row['text']}` | `{row['orig_count']}` | `{row['red_count']}` "
            f"| `{row['replaced']}` | `{row['residual']}` | {row['status']} |"
        )

    L += [
        "",
        "---",
        "",
        "## Residual Findings",
        "",
    ]

    actual_residuals = [r for r in residual_records if r["classification"] == "ACTUAL_RESIDUAL_PII"]
    prov_residuals   = [r for r in residual_records if r["classification"] == "PROVISIONAL_FALSE_POSITIVE"]

    if not actual_residuals:
        L.append("**No actual residual PII found.**")
    else:
        L.append("### Actual Residual PII")
        L.append("")
        L.append("| Entity ID | Category | Text | Orig Occ | Red Occ | Location |")
        L.append("| :--- | :--- | :--- | :---: | :---: | :--- |")
        for r in actual_residuals:
            L.append(
                f"| `{r['entity_id']}` | **{r['category']}** | `{r['text']}` "
                f"| `{r['original_occurrence_count']}` | `{r['redacted_occurrence_count']}` "
                f"| {r['location_str']} |"
            )

    if prov_residuals:
        L += ["", "### Provisional False Positives (not classified as actual PII)", ""]
        L.append("| Entity ID | Category | Text | Orig Occ | Red Occ | Location |")
        L.append("| :--- | :--- | :--- | :---: | :---: | :--- |")
        for r in prov_residuals:
            L.append(
                f"| `{r['entity_id']}` | **{r['category']}** | `{r['text']}` "
                f"| `{r['original_occurrence_count']}` | `{r['redacted_occurrence_count']}` "
                f"| {r['location_str']} |"
            )

    replace_pct = (total_replaced / total_checked * 100) if total_checked else 0.0
    L += [
        "",
        "---",
        "",
        "## Conclusion",
        "",
        f"* **Total candidate PII occurrences checked** : `{total_checked}`",
        f"* **Successfully replaced**                   : `{total_replaced}` ({replace_pct:.2f}%)",
        f"* **Residual candidate occurrences**          : `{total_residual}`",
        f"* **Actual residual PII**                     : `{actual_leak_count}`",
        f"* **Provisional false positives (residual)**  : `{provisional_fp_count}`",
        "",
        f"## **{conclusion}**",
    ]

    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"MD   -> {out_md.resolve()}")

    # ── Console summary ────────────────────────────────────────────────────
    print("\n" + "=" * 54)
    print("FINAL REDACTION VALIDATION SUMMARY")
    print("=" * 54)
    print(f"Candidate Occurrences Checked : {total_checked}")
    print(f"Successfully Replaced         : {total_replaced}")
    print(f"Residual Candidate Occurrences: {total_residual}")
    print(f"Actual Residual PII           : {actual_leak_count}")
    print(f"Provisional False Positives   : {provisional_fp_count}")
    print("-" * 54)
    print(f"CONCLUSION : {conclusion}")
    print("=" * 54)

    # Repeated-entity spotlight
    care_row = next((r for r in repeat_rows if r["text"] == "CareEdge Research"), None)
    if care_row:
        print(
            f"\nCareEdge Research -> orig:{care_row['orig_count']}  "
            f"red:{care_row['red_count']}  "
            f"replaced:{care_row['replaced']}  "
            f"residual:{care_row['residual']}"
        )


if __name__ == "__main__":
    main()
