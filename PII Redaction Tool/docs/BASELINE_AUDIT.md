# Baseline Audit Report

**Project**: PII Redaction Tool  
**Audit Date**: August 13, 2026  
**Status**: Establishing Baseline (Unmodified Repository)

---

## 1. Files Inspected
The following files were inspected to establish the project baseline:
- **Source Code**:
  - [`src/models.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/src/models.py)
  - [`src/detection_pipeline.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/src/detection_pipeline.py)
  - [`src/detectors/ner_detector.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/src/detectors/ner_detector.py)
  - [`src/redaction/docx_redactor.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/src/redaction/docx_redactor.py)
- **Tests**:
  - [`tests/test_docx_extractor.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/tests/test_docx_extractor.py)
  - [`tests/test_docx_redactor.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/tests/test_docx_redactor.py)
  - [`tests/test_regression_correctness.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/tests/test_regression_correctness.py)
  - [`tests/test_regressions.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/tests/test_regressions.py)
  - [`tests/test_cli.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/tests/test_cli.py)
  - [`tests/test_smoke.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/tests/test_smoke.py)
- **Evaluation Assets**:
  - [`evaluation/ground_truth.json`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/ground_truth.json)
  - [`evaluation/candidate_annotations.json`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/candidate_annotations.json)
  - [`evaluation/review_annotations.py`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/review_annotations.py)
  - [`evaluation/evaluation_report.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/evaluation_report.md)
- **Documentation**:
  - [`docs/GROUND_TRUTH_GUIDE.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/docs/GROUND_TRUTH_GUIDE.md)
  - [`docs/CORRECTNESS_AUDIT.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/docs/CORRECTNESS_AUDIT.md)
  - [`docs/FINAL_AUDIT.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/docs/FINAL_AUDIT.md)
  - [`README.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/README.md)
- **Dependencies**:
  - [`requirements.txt`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/requirements.txt)

---

## 2. Baseline Test Results
The current automated test suite was executed using:
```bash
pytest -q
```
- **Passed**: 80
- **Failed**: 0
- **Skipped**: 0

---

## 3. Baseline Evaluation Results (CURRENT/UNVERIFIED)
The following metrics are extracted from `evaluation/evaluation_report.md` but are explicitly flagged as **CURRENT/UNVERIFIED** until the ground truth, matching logic, and evaluation methodologies are fully audited:

- **Total Ground Truth Entities**: 3,428
- **Total Pipeline Predictions**: 5,607
- **True Positives (TP)**: 3,228
- **False Positives (FP)**: 2,379
- **False Negatives (FN)**: 200
- **Micro-Precision**: 0.5757 (57.57%)
- **Micro-Recall**: 0.9417 (94.17%)
- **Micro-F1 Score**: 0.7146 (71.46%)
- **Token-Level Accuracy**: 0.9543 (95.43%)

### Category-Wise Metric Breakdown

| Category | GT Count | Pred Count | TP | FP | FN | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ADDRESS** | 26 | 26 | 26 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **CREDIT_CARD** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A |
| **DOB** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A |
| **EMAIL** | 70 | 70 | 70 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **IP_ADDRESS** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A |
| **ORGANIZATION** | 2,537 | 4,809 | 2,489 | 2,320 | 48 | 0.5176 | 0.9811 | 0.6776 |
| **PERSON** | 746 | 653 | 594 | 59 | 152 | 0.9096 | 0.7962 | 0.8492 |
| **PHONE** | 49 | 49 | 49 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **SSN** | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A |

---

## 4. Current Project Status
- The automated detection and redaction pipeline compiles and executes.
- The codebase already contains various custom detectors (address, DOB, email, IP, NER, phone, SSN, credit card).
- Ground truth (`ground_truth.json`) is currently flagged as `is_provisional_candidate: true`, meaning it contains rule-filtered pipeline outputs rather than human-verified annotations.

---

## 5. Known Problems & Areas to Audit
- **Ground Truth Authenticity**: The ground truth is provisional, generated via candidate rules. There is a need to verify how it is managed and relabeled, and clearly state that no full human validation has yet taken place.
- **Stable Source Identity**: Entities are being identified by local offsets (`start`, `end`, `text`). We need to ensure that every entity carries a globally unique stable source identity (paragraph, table cell, row, column, section, headers/footers) so that matching and deduplication do not collapse different occurrences across the document.
- **Evaluation Matching & Deduplication**: Need to verify if the matching policy is strict and if duplicate local offsets in different tables/cells are correctly counted.
- **Redaction Completeness**: We must check if redaction functions successfully on multi-run split PII, paragraphs, tables, and headers/footers. We will build a validation check utility (`src/redaction/validation.py`) to verify original values do not remain in the output.
- **False Positives/Negatives**: We need to investigate why there are so many False Positives (e.g. 2,379 FPs) and False Negatives, particularly looking at dates, registration numbers, page numbers, and names split across runs or missing honorifics.
- **Security & Logging**: Ensure no raw PII is written to the console or log files.
