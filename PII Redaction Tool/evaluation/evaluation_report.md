# PROVISIONAL AUTOMATED EVALUATION REPORT

> [!WARNING]
> **PROVISIONAL EVALUATION NOTICE**: These metrics are computed against automated provisional annotations, not independently human-reviewed ground truth. See **Section 12** for provisional annotation-agreement metrics (Precision: 16.36%, Recall: 60.00%, F1: 25.71%) and **Section 13** for final human-validated metrics (all N/A).

## 1. Executive Summary
* **Target Document**: `Red Herring Prospectus.docx`
* **Evaluation Mode**: `PROVISIONAL AUTOMATED EVALUATION`
* **Total Pipeline Predictions**: `5,767`
* **Known True Positives (Known TP)**: `9`
* **Known False Positives (Known FP)**: `46`
* **Known False Negatives (Known FN)**: `6`
* **Unassessed/Unknown Predictions**: `5,712`

## 2. Ground-Truth Provenance
* **Independent Human Review**: Zero candidates were independently reviewed by a human.
* **Review Method**: The current annotation set was generated through automated policy-based review and is therefore provisional.
* **Provenance Method**: `automated_policy_review`

## 3. Annotation Statistics
* **Total Workload Candidates**: `3,507`
* **Automated Reviewed Candidates**: `63`
* **Human Reviewed Candidates**: `0`
* **Accepted Entities**: `15`
* **Rejected Candidates**: `48`
* **Unreviewed Candidates**: `3,444`

## 4. Evaluation Methodology
- **Entity Matching**: Match criteria incorporates unique DOCX location coordinates, text span character offsets, and entity type.
- **Partitions**:
  - **True Positives (TP)**: Predictions matching accepted entities.
  - **Known False Positives (FP)**: Predictions matching rejected candidates or type mismatches.
  - **Known False Negatives (FN)**: Accepted entities missed by the pipeline.
  - **Unassessed / Unknown**: Predictions matching unreviewed candidates or outside reviewed candidates.

## 5. Overall Provisional Results
- **Provisional Annotation-Agreement Precision**: `16.36%` (see Section 12 — provisional scope only; NOT final model precision)
- **Provisional Annotation-Agreement Recall**: `60.00%` (see Section 12 — provisional scope only; NOT final model recall)
- **Provisional Annotation-Agreement F1**: `25.71%` (see Section 12 — provisional scope only; NOT final benchmark F1)
- **Final / Human-Validated Precision**: `N/A — HUMAN VALIDATION REQUIRED`
- **Final / Human-Validated Recall**: `N/A — HUMAN VALIDATION REQUIRED`
- **Final / Human-Validated F1**: `N/A — HUMAN VALIDATION REQUIRED`
- **Accuracy (entity-level)**: `N/A — insufficient independently validated negative population`

## 6. Category-Wise Results

| Category | GT Count | Pred Count | TP | FP | FN | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ADDRESS** | `3` | `26` | `3` | `1` | `0` | `N/A` | `N/A` | `N/A` |
| **CREDIT_CARD** | `0` | `0` | `0` | `0` | `0` | `N/A` | `N/A` | `N/A` |
| **DOB** | `0` | `0` | `0` | `0` | `0` | `N/A` | `N/A` | `N/A` |
| **EMAIL** | `1` | `69` | `1` | `0` | `0` | `N/A` | `N/A` | `N/A` |
| **IP_ADDRESS** | `0` | `0` | `0` | `0` | `0` | `N/A` | `N/A` | `N/A` |
| **ORGANIZATION** | `9` | `4,812` | `3` | `43` | `6` | `N/A` | `N/A` | `N/A` |
| **PERSON** | `1` | `811` | `1` | `2` | `0` | `N/A` | `N/A` | `N/A` |
| **PHONE** | `1` | `49` | `1` | `0` | `0` | `N/A` | `N/A` | `N/A` |
| **SSN** | `0` | `0` | `0` | `0` | `0` | `N/A` | `N/A` | `N/A` |

## 7. False Positive Analysis
Occur when predicted spans match rejected candidates or type mismatches. In the reviewed 63 candidates, 46 known false positives were recorded (e.g. generic nouns, public entities).

## 8. False Negative Analysis
Occur when accepted entities are missed by the pipeline. In this batch, 6 false negatives were recorded.

## 9. Unassessed/Unknown Predictions
Predictions in unreviewed document regions are not counted as false positives. There are `5,712` unassessed predictions that require independent verification.

## 10. Limitations
- Entirely reliant on programmatic policy simulation for the 63 reviewed candidates.
- `3,444` candidates remain unassessed, preventing full-document metric evaluation.

## 11. Interpretation
This benchmark represents a provisional automated baseline. Do not interpret these counts as final full-document precision, recall, or F1.

---

## 12. Provisional Annotation-Agreement Metrics

> [!WARNING]
> **These metrics measure agreement with the current automated provisional annotation subset (63 automated-reviewed candidates). They are NOT independently human-validated model performance metrics. Zero candidates were reviewed by a human auditor. These numbers must NOT be interpreted as the model's true precision, recall, F1, or accuracy on unseen data.**

Computed from the verified reviewed subset only:

| Input | Value |
| :--- | :---: |
| True Positives (TP) — predictions matching accepted provisional entities | `9` |
| False Positives (FP) — predictions matching rejected candidates | `46` |
| False Negatives (FN) — accepted entities missed by the pipeline | `6` |

**Formulae and Results** (programmatically verified):

$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{9}{9 + 46} = \frac{9}{55} \approx \mathbf{16.36\%}$$

$$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{9}{9 + 6} = \frac{9}{15} = \mathbf{60.00\%}$$

$$\text{F1} = \frac{2 \times \text{TP}}{2 \times \text{TP} + \text{FP} + \text{FN}} = \frac{18}{18 + 46 + 6} = \frac{18}{70} \approx \mathbf{25.71\%}$$

| Metric | Provisional Value | Scope |
| :--- | :---: | :--- |
| **Precision** | **16.36%** | 63 automated-reviewed candidates only |
| **Recall** | **60.00%** | 63 automated-reviewed candidates only |
| **F1 Score** | **25.71%** | 63 automated-reviewed candidates only |
| **Accuracy (entity-level)** | **N/A** | See note below |

**Why Precision is low (16.36%)**: The pipeline generated 5,767 total predictions across the full document; the reviewed slice contains 55 assessed predictions (TP+FP), of which 46 are false positives. The large FP count reflects that the detector correctly fires on many legitimate names in unreviewed regions, but those regions have not been assessed yet.

**Why Recall is relatively higher (60.00%)**: Of the 15 accepted provisional entities, the pipeline detected 9 (TP) and missed 6 (FN). The 6 FN are all `ORGANIZATION` entities confirmed in the reviewed batch but not produced as predictions by the pipeline in those exact spans.

**Accuracy — N/A**: Entity-level accuracy requires a well-defined true-negative population (i.e., a complete list of document spans that are confirmed non-PII). The current provisional partial benchmark covers only 63 of 3,507 candidates; the remaining 3,444 are unassessed and cannot be treated as confirmed negatives. Reporting an accuracy figure under these conditions would require inventing a true-negative denominator, which would fabricate a metric. Therefore:

> **Accuracy: N/A — insufficient independently validated negative population.**

---

## 13. Final / Human-Validated Metrics

> [!IMPORTANT]
> No candidates were independently reviewed by a human auditor. The figures in Section 12 are provisional annotation-agreement metrics only and must not be re-labelled as independently validated performance metrics.

| Metric | Final Value |
| :--- | :---: |
| **Precision** | `N/A` |
| **Recall** | `N/A` |
| **F1 Score** | `N/A` |
| **Accuracy** | `N/A` |

**Reason**: Final benchmark metrics require a human-reviewed ground truth. Zero candidates have been independently human-reviewed. These figures will remain N/A until a qualified human auditor reviews the full candidate set.