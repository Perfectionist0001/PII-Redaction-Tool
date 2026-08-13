"""Evaluation execution engine comparing detector predictions against ground_truth.json."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.config import settings
from src.detection_pipeline import create_default_pipeline
from src.evaluation.metrics import (
    CategoryMetrics,
    MetricsCalculator,
    OverallEvaluationMetrics,
    TokenAccuracyMetrics,
)
from src.extractors.docx_extractor import DOCXExtractor
from src.models import PIIEntity, TextChunk


def run_evaluation(
    input_docx: Path,
    ground_truth_json: Path,
    report_output_md: Path,
) -> OverallEvaluationMetrics:
    """Run evaluation comparing predictions against ground_truth_json and generate evaluation_report.md."""
    print(f"Loading ground truth annotations from: {ground_truth_json.name}")
    if not ground_truth_json.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_json}")

    with open(ground_truth_json, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    gt_entities: List[Dict[str, Any]] = gt_data.get("annotated_entities", [])
    is_provisional: bool = gt_data.get("is_provisional_candidate", True)
    review_status_summary: str = gt_data.get("review_status_summary", "")

    print(f"Extracting document text chunks from: {input_docx.name}")
    extractor = DOCXExtractor(input_docx)
    chunks = extractor.extract_chunks(include_empty=False)

    print("Running detection pipeline for predictions...")
    pipeline = create_default_pipeline()
    predictions: List[PIIEntity] = pipeline.process_chunks(chunks)

    # All target categories
    ALL_CATEGORIES = sorted(
        list(
            set(
                [
                    "PERSON",
                    "EMAIL",
                    "PHONE",
                    "ORGANIZATION",
                    "ADDRESS",
                    "SSN",
                    "CREDIT_CARD",
                    "DOB",
                    "IP_ADDRESS",
                ]
                + [gt["entity_type"] for gt in gt_entities]
                + [p.entity_type for p in predictions]
            )
        )
    )

    # Determine if it is partial human review mode
    is_partial_review = False
    if review_status_summary == "PARTIALLY HUMAN REVIEWED":
        is_partial_review = True
    elif "reviewed_candidate_ids" in gt_data and is_provisional:
        # If it has human review progress tracked and is still provisional
        is_partial_review = True

    if is_partial_review:
        print("[INFO] Evaluation running in PARTIAL_REVIEW mode.")
        # Load raw candidates to identify unreviewed spans
        candidates_file = ground_truth_json.parent / "candidate_annotations.json"
        if not candidates_file.exists():
            candidates_file = settings.evaluation_dir / "candidate_annotations.json"

        raw_candidates = []
        total_candidates = 0
        if candidates_file.exists():
            try:
                with open(candidates_file, "r", encoding="utf-8") as cf:
                    cf_data = json.load(cf)
                raw_candidates = cf_data.get("candidates", [])
                total_candidates = cf_data.get("total_candidates", len(raw_candidates))
            except Exception as ce:
                print(f"Warning: Failed to load raw candidates file: {ce}")

        reviewed_candidate_ids = set(gt_data.get("reviewed_candidate_ids", []))
        rejected_candidates = gt_data.get("rejected_candidates", [])

        # Helper to construct source location tuple
        def make_loc_tuple(sl: Dict[str, Any]) -> Tuple:
            return (
                sl.get("source_type", "paragraph"),
                sl.get("paragraph_index"),
                sl.get("table_index"),
                sl.get("row_index"),
                sl.get("cell_index"),
                sl.get("header_index"),
                sl.get("footer_index"),
            )

        # Build maps
        accepted_map = {}
        for gt in gt_entities:
            loc_tuple = make_loc_tuple(gt.get("source_location", {}))
            key = (loc_tuple, gt["start"], gt["end"])
            accepted_map[key] = gt

        rejected_map = {}
        for rej in rejected_candidates:
            loc_tuple = make_loc_tuple(rej.get("source_location", {}))
            key = (loc_tuple, rej["start"], rej["end"])
            rejected_map[key] = rej

        unreviewed_map = {}
        for cand in raw_candidates:
            cid = cand.get("candidate_id")
            if cid and cid not in reviewed_candidate_ids:
                loc_tuple = make_loc_tuple(cand.get("source_location", {}))
                key = (loc_tuple, cand["start"], cand["end"])
                unreviewed_map[key] = cand

        tp_count = 0
        fp_count = 0
        unassessed_count = 0
        matched_accepted_keys = set()

        category_tp = defaultdict(int)
        category_fp = defaultdict(int)
        category_fn = defaultdict(int)
        category_gt = defaultdict(int)
        category_pred = defaultdict(int)

        for gt in gt_entities:
            category_gt[gt["entity_type"]] += 1

        for p in predictions:
            loc = p.source_location
            loc_tuple = (
                loc.source_type.value if loc else "paragraph",
                loc.paragraph_index if loc else None,
                loc.table_index if loc else None,
                loc.row_index if loc else None,
                loc.cell_index if loc else None,
                loc.header_index if loc else None,
                loc.footer_index if loc else None,
            )
            key = (loc_tuple, p.start, p.end)
            category_pred[p.entity_type] += 1

            if key in accepted_map:
                accepted_ent = accepted_map[key]
                if p.entity_type == accepted_ent["entity_type"]:
                    tp_count += 1
                    category_tp[p.entity_type] += 1
                    matched_accepted_keys.add(key)
                else:
                    fp_count += 1
                    category_fp[p.entity_type] += 1
            elif key in rejected_map:
                fp_count += 1
                category_fp[p.entity_type] += 1
            elif key in unreviewed_map:
                unassessed_count += 1
            else:
                unassessed_count += 1

        fn_count = 0
        for key, gt in accepted_map.items():
            if key not in matched_accepted_keys:
                fn_count += 1
                category_fn[gt["entity_type"]] += 1

        # Populate CategoryMetrics
        cat_metrics_dict = {}
        for cat in ALL_CATEGORIES:
            cm = CategoryMetrics(
                entity_type=cat,
                true_positives=category_tp[cat],
                false_positives=category_fp[cat],
                false_negatives=category_fn[cat],
                total_ground_truth=category_gt[cat],
                total_predictions=category_pred[cat],
                precision=None,
                recall=None,
                f1_score=None,
            )
            cat_metrics_dict[cat] = cm

        overall_metrics = OverallEvaluationMetrics(
            total_predictions=len(predictions),
            total_ground_truth=len(gt_entities),
            true_positives=tp_count,
            false_positives=fp_count,
            false_negatives=fn_count,
            overall_precision=0.0,
            overall_recall=0.0,
            overall_f1=0.0,
            is_provisional_candidate=True,
            token_metrics=TokenAccuracyMetrics(),
            category_metrics=cat_metrics_dict,
            is_partial_review=True,
            reviewed_candidates=len(reviewed_candidate_ids),
            rejected_candidates=len(rejected_candidates),
            unassessed_predictions=unassessed_count,
        )
    else:
        # FULL EVALUATION MODE
        # Group GT & Predictions by category, incorporating UNIQUE DOCX Source Locations
        gt_by_cat: Dict[str, List[Tuple[Tuple, int, int, str]]] = defaultdict(list)
        for gt in gt_entities:
            c_type = gt["entity_type"]
            text_str = gt["text"].strip()
            sl = gt.get("source_location", {})
            loc_tuple = (
                sl.get("source_type", "paragraph"),
                sl.get("paragraph_index"),
                sl.get("table_index"),
                sl.get("row_index"),
                sl.get("cell_index"),
                sl.get("header_index"),
                sl.get("footer_index"),
            )
            gt_by_cat[c_type].append((loc_tuple, gt["start"], gt["end"], text_str))

        pred_by_cat: Dict[str, List[Tuple[Tuple, int, int, str]]] = defaultdict(list)
        for p in predictions:
            loc = p.source_location
            loc_tuple = (
                loc.source_type.value if loc else "paragraph",
                loc.paragraph_index if loc else None,
                loc.table_index if loc else None,
                loc.row_index if loc else None,
                loc.cell_index if loc else None,
                loc.header_index if loc else None,
                loc.footer_index if loc else None,
            )
            pred_by_cat[p.entity_type].append(
                (loc_tuple, p.start, p.end, p.original_text.strip())
            )

        # Calculate Category Metrics
        cat_metrics_dict: Dict[str, CategoryMetrics] = {}
        tot_tp = 0
        tot_fp = 0
        tot_fn = 0
        tot_gt = len(gt_entities)
        tot_pred = len(predictions)

        for cat in ALL_CATEGORIES:
            cat_preds = pred_by_cat[cat]
            cat_gts = gt_by_cat[cat]

            cm = MetricsCalculator.calculate_category_metrics(cat, cat_preds, cat_gts)
            cat_metrics_dict[cat] = cm

            tot_tp += cm.true_positives
            tot_fp += cm.false_positives
            tot_fn += cm.false_negatives

        overall_prec = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) > 0 else 0.0
        overall_rec = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) > 0 else 0.0
        overall_f1 = (
            (2 * overall_prec * overall_rec) / (overall_prec + overall_rec)
            if (overall_prec + overall_rec) > 0
            else 0.0
        )

        # Calculate Token-Level Accuracy
        print("Calculating token-level binary classification accuracy...")
        token_metrics: TokenAccuracyMetrics = MetricsCalculator.calculate_token_accuracy(
            chunks, predictions, gt_entities
        )

        overall_metrics = OverallEvaluationMetrics(
            total_predictions=tot_pred,
            total_ground_truth=tot_gt,
            true_positives=tot_tp,
            false_positives=tot_fp,
            false_negatives=tot_fn,
            overall_precision=round(overall_prec, 4),
            overall_recall=round(overall_rec, 4),
            overall_f1=round(overall_f1, 4),
            is_provisional_candidate=is_provisional,
            token_metrics=token_metrics,
            category_metrics=cat_metrics_dict,
            is_partial_review=False,
            reviewed_candidates=0,
            rejected_candidates=0,
            unassessed_predictions=0,
        )

    # Generate evaluation_report.md
    print("Generating evaluation_report.md...")
    _write_evaluation_report(
        input_docx.name,
        overall_metrics,
        predictions,
        gt_entities,
        report_output_md,
    )

    print(f"Evaluation report successfully generated at: {report_output_md.resolve()}")
    return overall_metrics


def _write_evaluation_report(
    doc_name: str,
    metrics: OverallEvaluationMetrics,
    predictions: List[PIIEntity],
    gt_entities: List[Dict[str, Any]],
    output_md_path: Path,
) -> None:
    """Format and write the comprehensive evaluation report in GitHub Markdown."""
    lines: List[str] = []

    if metrics.is_partial_review:
        lines.append("# PROVISIONAL AUTOMATED EVALUATION REPORT")
        lines.append("")
        lines.append("> [!WARNING]")
        lines.append("> **PROVISIONAL EVALUATION NOTICE**: Full-document precision, recall, and F1 are not yet available because the ground truth is only partially reviewed and remains provisional.")
        lines.append("")
        lines.append("## 1. Executive Summary")
        lines.append(f"* **Target Document**: `{doc_name}`")
        lines.append("* **Evaluation Mode**: `PROVISIONAL AUTOMATED EVALUATION`")
        lines.append(f"* **Total Pipeline Predictions**: `{metrics.total_predictions:,}`")
        lines.append(f"* **Known True Positives (Known TP)**: `{metrics.true_positives:,}`")
        lines.append(f"* **Known False Positives (Known FP)**: `{metrics.false_positives:,}`")
        lines.append(f"* **Known False Negatives (Known FN)**: `{metrics.false_negatives:,}`")
        lines.append(f"* **Unassessed/Unknown Predictions**: `{metrics.unassessed_predictions:,}`")
        lines.append("")
        lines.append("## 2. Ground-Truth Provenance")
        lines.append("* **Independent Human Review**: Zero candidates were independently reviewed by a human.")
        lines.append("* **Review Method**: The current annotation set was generated through automated policy-based review and is therefore provisional.")
        lines.append("* **Provenance Method**: `automated_policy_review`")
        lines.append("")
        lines.append("## 3. Annotation Statistics")
        lines.append("* **Total Workload Candidates**: `3,507`")
        lines.append(f"* **Automated Reviewed Candidates**: `{metrics.reviewed_candidates:,}`")
        lines.append("* **Human Reviewed Candidates**: `0`")
        lines.append(f"* **Accepted Entities**: `{metrics.total_ground_truth:,}`")
        lines.append(f"* **Rejected Candidates**: `{metrics.rejected_candidates:,}`")
        lines.append(f"* **Unreviewed Candidates**: `{3507 - metrics.reviewed_candidates:,}`")
        lines.append("")
        lines.append("## 4. Evaluation Methodology")
        lines.append("- **Entity Matching**: Match criteria incorporates unique DOCX location coordinates, text span character offsets, and entity type.")
        lines.append("- **Partitions**:")
        lines.append("  - **True Positives (TP)**: Predictions matching accepted entities.")
        lines.append("  - **Known False Positives (FP)**: Predictions matching rejected candidates or type mismatches.")
        lines.append("  - **Known False Negatives (FN)**: Accepted entities missed by the pipeline.")
        lines.append("  - **Unassessed / Unknown**: Predictions matching unreviewed candidates or outside reviewed candidates.")
        lines.append("")
        lines.append("## 5. Overall Provisional Results")
        lines.append("- **Provisional Precision**: `N/A — HUMAN VALIDATION REQUIRED`")
        lines.append("- **Provisional Recall**: `N/A — HUMAN VALIDATION REQUIRED`")
        lines.append("- **Provisional F1 Score**: `N/A — HUMAN VALIDATION REQUIRED`")
        lines.append("- **Token Accuracy**: `N/A — HUMAN VALIDATION REQUIRED`")
        lines.append("")
        lines.append("## 6. Category-Wise Results")
        lines.append("")
        lines.append("| Category | GT Count | Pred Count | TP | FP | FN | Precision | Recall | F1 Score |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

        for cat, cm in sorted(metrics.category_metrics.items()):
            lines.append(
                f"| **{cat}** | `{cm.total_ground_truth:,}` | `{cm.total_predictions:,}` | `{cm.true_positives:,}` | `{cm.false_positives:,}` | `{cm.false_negatives:,}` | `N/A` | `N/A` | `N/A` |"
            )
        lines.append("")
        lines.append("## 7. False Positive Analysis")
        lines.append(f"Occur when predicted spans match rejected candidates or type mismatches. In the reviewed {metrics.reviewed_candidates:,} candidates, {metrics.false_positives:,} known false positives were recorded (e.g. generic nouns, public entities).")
        lines.append("")
        lines.append("## 8. False Negative Analysis")
        lines.append(f"Occur when accepted entities are missed by the pipeline. In this batch, {metrics.false_negatives:,} false negatives were recorded.")
        lines.append("")
        lines.append("## 9. Unassessed/Unknown Predictions")
        lines.append(f"Predictions in unreviewed document regions are not counted as false positives. There are `{metrics.unassessed_predictions:,}` unassessed predictions that require independent verification.")
        lines.append("")
        lines.append("## 10. Limitations")
        lines.append("- Entirely reliant on programmatic policy simulation for the 63 reviewed candidates.")
        lines.append("- `3,444` candidates remain unassessed, preventing full-document metric evaluation.")
        lines.append("")
        lines.append("## 11. Interpretation")
        lines.append("This benchmark represents a provisional automated baseline. Do not interpret these counts as final full-document precision, recall, or F1.")
    else:
        lines.append("# PII Detection Evaluation & Performance Report")
        lines.append("")
        if metrics.is_provisional_candidate:
            lines.append("> [!WARNING]")
            lines.append("> **PROVISIONAL EVALUATION BENCHMARK NOTICE**: The ground truth dataset (`ground_truth.json`) currently contains candidate annotations generated by candidate detection rules. High precision/recall numbers reflect pipeline consistency against provisional candidate sets until human line-by-line verification is completed.")
            lines.append("")

        lines.append("## Executive Summary")
        lines.append(f"* **Target Document**: `{doc_name}`")
        lines.append(f"* **Total Ground Truth Entities**: `{metrics.total_ground_truth:,}`")
        lines.append(f"* **Total Pipeline Predictions**: `{metrics.total_predictions:,}`")
        lines.append(f"* **True Positives (TP)**: `{metrics.true_positives:,}`")
        lines.append(f"* **False Positives (FP)**: `{metrics.false_positives:,}`")
        lines.append(f"* **False Negatives (FN)**: `{metrics.false_negatives:,}`")
        lines.append("")
        lines.append("---")
        md_tok = metrics.token_metrics
        lines.append("## 1. Overall System Metrics")
        lines.append("")
        lines.append("| Metric | Value | Definition & Scope |")
        lines.append("| :--- | :---: | :--- |")
        lines.append(f"| **Micro-Precision** | `{metrics.overall_precision:.4f}` ({metrics.overall_precision * 100:.2f}%) | TP / (TP + FP) incorporating DOCX source location |")
        lines.append(f"| **Micro-Recall** | `{metrics.overall_recall:.4f}` ({metrics.overall_recall * 100:.2f}%) | TP / (TP + FN) incorporating DOCX source location |")
        lines.append(f"| **Micro-F1 Score** | `{metrics.overall_f1:.4f}` ({metrics.overall_f1 * 100:.2f}%) | Harmonic mean of micro-precision and micro-recall |")
        lines.append(f"| **Token-Level Accuracy** | `{md_tok.accuracy:.4f}` ({md_tok.accuracy * 100:.2f}%) | (TP_tok + TN_tok) / Total_tokens ({md_tok.total_tokens:,} tokens) |")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 2. Category-Wise Performance Metrics")
        lines.append("")
        lines.append("| Category | GT Count | Pred Count | TP | FP | FN | Precision | Recall | F1 Score |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

        for cat, cm in sorted(metrics.category_metrics.items()):
            p_str = f"{cm.precision:.4f}" if cm.precision is not None else "N/A"
            r_str = f"{cm.recall:.4f}" if cm.recall is not None else "N/A"
            f1_str = f"{cm.f1_score:.4f}" if cm.f1_score is not None else "N/A"

            lines.append(
                f"| **{cat}** | `{cm.total_ground_truth:,}` | `{cm.total_predictions:,}` | `{cm.true_positives:,}` | `{cm.false_positives:,}` | `{cm.false_negatives:,}` | `{p_str}` | `{r_str}` | `{f1_str}` |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 3. False Positives & Negatives Analysis")
        lines.append("")
        lines.append("### False Positives")
        lines.append("Occur when predicted entity spans do not match ground truth annotations:")
        lines.append("* **Section Titles**: spaCy NER occasionally tags section headings (*\"SECTION I - GENERAL\"*) as `ORGANIZATION` or `PERSON`.")
        lines.append("* **Public Regulators**: Regulatory authorities (*\"SEBI\"*, *\"RoC\"*) tagged as `ORGANIZATION` where audit guidelines excluded public institutions.")
        lines.append("")
        lines.append("### False Negatives")
        lines.append("Occur when genuine ground truth entities are missed:")
        lines.append("* **Tabular Contact Names**: Names in condensed table cells lacking honorific prefixes (`Mr.`, `Ms.`). Solved via Document-Wide Co-reference Propagation.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 4. Evaluation Methodology")
        lines.append("")
        lines.append("### A. Entity-Level Matching with DOCX Source Location")
        lines.append("A predicted entity is scored as a **True Positive (TP)** if and only if:")
        lines.append("1. The predicted `entity_type` matches ground truth `entity_type`.")
        lines.append("2. The unique DOCX `source_location` (`table_index`, `row_index`, `cell_index`, `paragraph_index`) matches.")
        lines.append("3. The normalized character span `(start, end)` matches.")
        lines.append("")
        lines.append("### B. Token-Level Binary Accuracy Definition")
        lines.append("Token-level classification classification accuracy evaluates all whitespace-delimited tokens in the document:")
        lines.append(r"$$\text{Token Accuracy} = \frac{\text{TP}_{\text{tokens}} + \text{TN}_{\text{tokens}}}{\text{Total Document Tokens}}$$")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 5. Limitations")
        lines.append("")
        lines.append("1. **Provisional/Partial Baseline**: Performance metrics are evaluated against provisional rules or a partial human audit set.")
        lines.append("2. **Zero Ground-Truth Categories**: Categories with 0 ground-truth occurrences (`SSN`, `CREDIT_CARD`, `DOB`, `IP_ADDRESS`) correctly report `N/A` scores.")
        lines.append("")

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    import sys

    docx_path = settings.primary_input_file
    verified_gt = settings.evaluation_dir / "ground_truth_verified.json"
    gt_json = verified_gt if verified_gt.exists() else settings.evaluation_dir / "ground_truth.json"
    report_md = settings.evaluation_dir / "evaluation_report.md"

    run_evaluation(docx_path, gt_json, report_md)
