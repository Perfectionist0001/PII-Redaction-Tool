"""Evaluation metrics calculation module for entity-level and token-level accuracy."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.models import PIIEntity, TextChunk


@dataclass
class CategoryMetrics:
    """Quantitative performance metrics for a single PII category."""

    entity_type: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_ground_truth: int = 0
    total_predictions: int = 0
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None


@dataclass
class TokenAccuracyMetrics:
    """Token-level binary classification metrics."""

    total_tokens: int = 0
    tp_tokens: int = 0
    tn_tokens: int = 0
    fp_tokens: int = 0
    fn_tokens: int = 0
    accuracy: float = 0.0


@dataclass
class OverallEvaluationMetrics:
    """Overall document evaluation summary."""

    total_predictions: int = 0
    total_ground_truth: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    overall_precision: float = 0.0
    overall_recall: float = 0.0
    overall_f1: float = 0.0
    is_provisional_candidate: bool = True
    token_metrics: TokenAccuracyMetrics = field(default_factory=TokenAccuracyMetrics)
    category_metrics: Dict[str, CategoryMetrics] = field(default_factory=dict)
    is_partial_review: bool = False
    reviewed_candidates: int = 0
    rejected_candidates: int = 0
    unassessed_predictions: int = 0


class MetricsCalculator:
    """Calculates entity-level Precision, Recall, F1 and token-level Accuracy using unique source locations."""

    @staticmethod
    def calculate_category_metrics(
        entity_type: str,
        predictions: List[Tuple[Tuple, int, int, str]],
        ground_truth: List[Tuple[Tuple, int, int, str]],
    ) -> CategoryMetrics:
        """Calculate entity-level metrics incorporating unique DOCX source locations.

        Matches by (source_location_tuple, start, end, text_string).
        """
        pred_set: Set[Tuple[Tuple, int, int, str]] = set(predictions)
        gt_set: Set[Tuple[Tuple, int, int, str]] = set(ground_truth)

        tp_set = pred_set & gt_set
        fp_set = pred_set - gt_set
        fn_set = gt_set - pred_set

        tp = len(tp_set)
        fp = len(fp_set)
        fn = len(fn_set)

        total_gt = len(gt_set)
        total_pred = len(pred_set)

        precision: Optional[float] = None
        recall: Optional[float] = None
        f1: Optional[float] = None

        if total_pred > 0:
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        if total_gt > 0:
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        if precision is not None and recall is not None and (precision + recall) > 0:
            f1 = (2 * precision * recall) / (precision + recall)
        elif precision == 0.0 and recall == 0.0:
            f1 = 0.0

        return CategoryMetrics(
            entity_type=entity_type,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            total_ground_truth=total_gt,
            total_predictions=total_pred,
            precision=precision,
            recall=recall,
            f1_score=f1,
        )

    @staticmethod
    def calculate_token_accuracy(
        chunks: List[TextChunk],
        predictions: List[PIIEntity],
        ground_truth: List[Dict[str, Any]],
    ) -> TokenAccuracyMetrics:
        """Calculate token-level binary classification accuracy across document text chunks.

        Ground truth PII tokens = Positive
        Ground truth Non-PII tokens = Negative
        """
        tp_tokens = 0
        tn_tokens = 0
        fp_tokens = 0
        fn_tokens = 0
        total_tokens = 0

        # Group GT entity spans by chunk key
        gt_spans_by_chunk: Dict[Tuple, List[Tuple[int, int]]] = {}
        for gt in ground_truth:
            sl = gt.get("source_location", {})
            key = (
                sl.get("source_type", "paragraph"),
                sl.get("paragraph_index"),
                sl.get("table_index"),
                sl.get("row_index"),
                sl.get("cell_index"),
                sl.get("header_index"),
                sl.get("footer_index"),
            )
            if key not in gt_spans_by_chunk:
                gt_spans_by_chunk[key] = []
            gt_spans_by_chunk[key].append((gt["start"], gt["end"]))

        # Group predicted entity spans by chunk key
        pred_spans_by_chunk: Dict[Tuple, List[Tuple[int, int]]] = {}
        for p in predictions:
            if not p.source_location:
                continue
            loc = p.source_location
            key = (
                loc.source_type.value,
                loc.paragraph_index,
                loc.table_index,
                loc.row_index,
                loc.cell_index,
                loc.header_index,
                loc.footer_index,
            )
            if key not in pred_spans_by_chunk:
                pred_spans_by_chunk[key] = []
            pred_spans_by_chunk[key].append((p.start, p.end))

        word_pattern = re.compile(r"\S+")

        for chunk in chunks:
            if not chunk.source_location or not chunk.text:
                continue

            loc = chunk.source_location
            ckey = (
                loc.source_type.value,
                loc.paragraph_index,
                loc.table_index,
                loc.row_index,
                loc.cell_index,
                loc.header_index,
                loc.footer_index,
            )

            c_gt_spans = gt_spans_by_chunk.get(ckey, [])
            c_pred_spans = pred_spans_by_chunk.get(ckey, [])

            for match in word_pattern.finditer(chunk.text):
                w_start = match.start()
                w_end = match.end()
                total_tokens += 1

                is_gt_pii = any(gs <= w_start and w_end <= ge for gs, ge in c_gt_spans)
                is_pred_pii = any(ps <= w_start and w_end <= pe for ps, pe in c_pred_spans)

                if is_gt_pii and is_pred_pii:
                    tp_tokens += 1
                elif not is_gt_pii and not is_pred_pii:
                    tn_tokens += 1
                elif not is_gt_pii and is_pred_pii:
                    fp_tokens += 1
                elif is_gt_pii and not is_pred_pii:
                    fn_tokens += 1

        accuracy = (tp_tokens + tn_tokens) / total_tokens if total_tokens > 0 else 0.0

        return TokenAccuracyMetrics(
            total_tokens=total_tokens,
            tp_tokens=tp_tokens,
            tn_tokens=tn_tokens,
            fp_tokens=fp_tokens,
            fn_tokens=fn_tokens,
            accuracy=round(accuracy, 4),
        )
