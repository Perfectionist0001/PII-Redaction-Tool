# Ground-Truth Provenance & Audit Report

This document records the provenance, audit log, and review method for the verified ground truth annotations set stored at [ground_truth_verified.json](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/ground_truth_verified.json).

---

## 1. Dataset Status

- **Status**: `PROVISIONAL`
- **Is Provisional Candidate**: `true`
- **Review Status Summary**: `AUTOMATED PROVISIONAL REVIEW`
- **Review Method**: `automated_policy_review`

---

## 2. Provenance Metrics

| Metric | Count | Details |
| :--- | :---: | :--- |
| **Total Candidates** | `3,507` | Total annotation candidates extracted from document |
| **Automated Reviewed** | `63` | Candidates reviewed programmatically by Antigravity policy reviewer |
| **Human Reviewed** | `0` | Actual candidates reviewed by a human auditor |
| **Unreviewed** | `3,444` | Candidates remaining in the workload queue |
| **Accepted Entities** | `15` | Genuine PII entities identified in the reviewed set |
| **Rejected Candidates** | `48` | False positive candidates excluded from ground truth |
| **Corrected Spans** | `1` | Entries whose boundary spans were corrected (`cand_59`) |

---

## 3. Provenance & Methodological Notes

1. **Automation Origin**:
   All 63 decisions on candidates `cand_1` through `cand_63` were generated via a scripted agent simulation applying the target evaluation guidelines. Zero (0) decisions have been reviewed or signed off by a human auditor.
2. **Terminology Sanitization**:
   All dataset labels claiming `"human_verified"`, `"human_corrected_span"`, or `"human_reviewed"` have been removed and replaced with `"automated_reviewed"` or `"automated_corrected_span"` to prevent incorrect provenance claims.
