# Final Consistency Check

**Project**: PII Redaction Tool  
**Document Under Test**: `input/Red Herring Prospectus.docx`  
**Check Date**: 2026-08-14  
**Auditor**: Antigravity read-only consistency pass

> [!IMPORTANT]
> This is a READ-ONLY audit. No code, detector logic, ground truth, redaction engine, evaluation methodology, or tests were modified.

---

## 1. Files Checked

| File | Checked |
| :--- | :---: |
| [`README.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/README.md) | ✅ |
| [`evaluation/evaluation_report.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/evaluation_report.md) | ✅ |
| [`evaluation/final_redaction_validation.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/final_redaction_validation.md) | ✅ |
| [`evaluation/final_redaction_validation.json`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/final_redaction_validation.json) | ✅ |
| [`evaluation/ground_truth_verified.json`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/ground_truth_verified.json) | ✅ |
| [`docs/GROUND_TRUTH_PROVENANCE.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/docs/GROUND_TRUTH_PROVENANCE.md) | ✅ |
| [`docs/CORRECTNESS_AUDIT.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/docs/CORRECTNESS_AUDIT.md) | ✅ |
| [`docs/CAREEDGE_LEAK_ROOT_CAUSE.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/docs/CAREEDGE_LEAK_ROOT_CAUSE.md) | ✅ |
| [`docs/FINAL_SUBMISSION_AUDIT.md`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/docs/FINAL_SUBMISSION_AUDIT.md) | ✅ |

**Additional source inspected** (to resolve the 3,428 question):

| File | Purpose |
| :--- | :--- |
| [`evaluation/ground_truth.json`](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/evaluation/ground_truth.json) | Verified actual entity count = 3,428; distinct from `ground_truth_verified.json` |

---

## 2. Counts Verified

### 2.1 Primary Provenance Counts (ground_truth_verified.json)

| Fact | Expected | README | evaluation_report.md | GROUND_TRUTH_PROVENANCE.md | ground_truth_verified.json | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Total workload candidates | 3,507 | ✅ (implied via verified.json) | ✅ 3,507 | ✅ 3,507 | ✅ 3,507 | ✅ |
| Automated-reviewed | 63 | ✅ | ✅ 63 | ✅ 63 | ✅ 63 | ✅ |
| Human-reviewed | 0 | ✅ | ✅ 0 | ✅ 0 | ✅ 0 | ✅ |
| Unreviewed | 3,444 | ✅ | ✅ 3,444 | ✅ 3,444 | ✅ 3,444 | ✅ |
| Accepted entities | 15 | ✅ | ✅ 15 | ✅ 15 | ✅ 15 | ✅ |
| Rejected candidates | 48 | ✅ | ✅ 48 | ✅ 48 | ✅ 48 | ✅ |
| Corrected spans | 1 (`cand_59`) | not listed | not listed | ✅ 1 | ✅ (implied by automated_corrected_span) | ✅ |

### 2.2 The "3,428" Number — Resolved

> [!NOTE]
> The number **3,428** appears in `README.md`, `docs/CORRECTNESS_AUDIT.md`, and `docs/FINAL_AUDIT.md`. It is **not** a contradiction of the 3,507 total candidates figure. These are two separate files with two separate populations.

| File | Entity count | Population |
| :--- | :---: | :--- |
| `evaluation/ground_truth.json` | **3,428** annotated entities | Full-document original NER/rule output, all accepted without human review. Used for the full-document provisional evaluation run. |
| `evaluation/ground_truth_verified.json` | 3,507 total *candidates*; 15 accepted | The workload review queue. Only 63 were assessed; 15 accepted, 48 rejected, 3,444 unreviewed. |

**Conclusion**: `3,428 ≠ 3,507` is **not a contradiction**. They are different files tracking different populations. README correctly labels the full-document run section as "against `evaluation/ground_truth.json` (3,428 provisional annotations)". ✅

---

## 3. Metric Values Verified

### 3.1 Provisional Annotation-Agreement Metrics (verified subset, 63 candidates)

| Metric | Expected | evaluation_report.md §12 | README Verified Subset table | Status |
| :--- | :---: | :---: | :---: | :---: |
| TP | 9 | ✅ 9 | ✅ 9 | ✅ |
| FP | 46 | ✅ 46 | ✅ 46 | ✅ |
| FN | 6 | ✅ 6 | ✅ 6 | ✅ |
| Precision | 16.36% | ✅ 16.36% | ✅ 16.36% | ✅ |
| Recall | 60.00% | ✅ 60.00% | ✅ 60.00% | ✅ |
| F1 | 25.71% | ✅ 25.71% | ✅ 25.71% | ✅ |
| Accuracy (entity-level) | N/A | ✅ N/A | ✅ N/A | ✅ |

### 3.2 Final / Human-Validated Metrics

| Metric | Expected | evaluation_report.md §13 | README | Status |
| :--- | :---: | :---: | :---: | :---: |
| Precision | N/A | ✅ N/A | ✅ N/A | ✅ |
| Recall | N/A | ✅ N/A | ✅ N/A | ✅ |
| F1 | N/A | ✅ N/A | ✅ N/A | ✅ |
| Accuracy | N/A | ✅ N/A | ✅ N/A | ✅ |

### 3.3 Mathematical Verification

| Formula | Calculation | Result | Matches docs |
| :--- | :--- | :---: | :---: |
| Precision = TP / (TP + FP) | 9 / (9 + 46) = 9 / 55 | 0.16364 = **16.36%** | ✅ |
| Recall = TP / (TP + FN) | 9 / (9 + 6) = 9 / 15 | 0.60000 = **60.00%** | ✅ |
| F1 = 2TP / (2TP + FP + FN) | 18 / (18 + 46 + 6) = 18 / 70 | 0.25714 = **25.71%** | ✅ |

---

## 4. Provenance Verified

| Claim | File | Value | Correct |
| :--- | :--- | :---: | :---: |
| `is_provisional_candidate` | ground_truth_verified.json | `true` | ✅ |
| `review_status_summary` | ground_truth_verified.json | `"AUTOMATED PROVISIONAL REVIEW"` | ✅ |
| `review_method` | ground_truth_verified.json | `"automated_policy_review"` | ✅ |
| `human_reviewed_candidates` | ground_truth_verified.json | `0` | ✅ |
| `automated_reviewed_candidates` | ground_truth_verified.json | `63` | ✅ |
| `unreviewed_candidates` | ground_truth_verified.json | `3444` | ✅ |
| Human reviewed = 0 | GROUND_TRUTH_PROVENANCE.md | ✅ stated | ✅ |
| Automated reviewed = 63 | GROUND_TRUTH_PROVENANCE.md | ✅ stated | ✅ |
| All 63 review_status values | ground_truth_verified.json | `"automated_reviewed"` or `"automated_corrected_span"` | ✅ |

**Forbidden terminology search** (across all `.md` and `.json` files):

| Term searched | Occurrences in current review-status fields | Status |
| :--- | :---: | :---: |
| `human_verified` | 0 | ✅ |
| `human_reviewed` | 0 | ✅ |
| `human_corrected_span` | 0 | ✅ |
| `human-audited` (in any active claim) | 0 | ✅ |
| `gold standard` | 0 | ✅ |
| `100% recall` / `100% detection recall` | 0 | ✅ |

---

## 5. Redaction Validation Verified

Source: `evaluation/final_redaction_validation.json` (programmatically generated by `scripts/residual_pii_checker.py`).

| Fact | Expected | JSON value | MD value | Status |
| :--- | :---: | :---: | :---: | :---: |
| `actual_residual_pii` | 0 | ✅ `0` | ✅ `0` | ✅ |
| `residual_candidate_occurrences` | 0 | ✅ `0` | ✅ `0` | ✅ |
| Conclusion field | PASS | ✅ `"PASS — NO ACTUAL RESIDUAL PII FOUND"` | ✅ stated | ✅ |
| CareEdge Research — orig count | 7 | ✅ `7` (repeated-entity table) | ✅ `7` | ✅ |
| CareEdge Research — red count | 0 | ✅ `0` | ✅ `0` | ✅ |
| CareEdge Research — residual | 0 | ✅ `0` | ✅ `0` | ✅ |
| CAREEDGE_LEAK_ROOT_CAUSE.md | "0 leaks remain" | n/a | ✅ consistent | ✅ |

**Important distinction confirmed**: The "19 / 19 successfully replaced" figure in the validation report refers to **provisional annotation-slot occurrences checked within source chunks** — not to total full-document occurrence counts, and NOT to detection recall. The validation report contains an explicit explanatory note making this distinction clear. ✅

---

## 6. Inconsistencies Found

### 6.1 CORRECTNESS_AUDIT.md — Historical Test Count (Informational, Not Corrected)

| Location | Says | Current actual | Nature |
| :--- | :---: | :---: | :--- |
| `docs/CORRECTNESS_AUDIT.md` line 73 | `80 passed` | `83 passed` | **Historical record** — captured before CareEdge regression test was added. Document title and body clearly state this is a snapshot from the correctness audit phase. Not a current claim. |

**Action**: No correction. Historical records must preserve the state they documented. The discrepancy is explained by the subsequent addition of 3 regression tests. The CAREEDGE_LEAK_ROOT_CAUSE.md correctly states "83 passed (including the new regression test)".

### 6.2 CORRECTNESS_AUDIT.md — "100%" Redaction Claim (Informational, Not Corrected)

| Location | Says | Nature |
| :--- | :--- | :--- |
| `docs/CORRECTNESS_AUDIT.md` line 85 | "100% of natural person names, physical addresses, personal email addresses, and phone numbers are completely redacted." | **Historical record** written before the CareEdge leak was discovered. At the time of writing it was factually incorrect (CareEdge had 1 residual occurrence). The CareEdge fix was subsequently applied and the leak eliminated. The current validated state (PASS, 0 residual) supersedes this historical claim. |

**Action**: No correction to the historical document. The CAREEDGE_LEAK_ROOT_CAUSE.md provides the authoritative post-fix validation result. The FINAL_SUBMISSION_AUDIT.md and final_redaction_validation.md are the current canonical redaction status documents.

### 6.3 README "3,428" — Confirmed Not a Contradiction

| Claim | Verdict |
| :--- | :---: |
| README references "3,428 provisional annotations" in the Full Provisional Run section | ✅ **Correct** — `ground_truth.json` contains exactly 3,428 annotated entities (programmatically verified). This is a different file from `ground_truth_verified.json` (3,507 candidates). Both numbers are accurate for their respective populations. |

**No correction needed.**

---

## 7. Corrections Made

**None.** This is a read-only audit pass. All findings in Section 6 are either:

- Historical records (pre-CareEdge state), which must not be retroactively altered
- Resolved population distinctions (3,428 vs 3,507), which are correctly documented in the current files

No source code, ground truth, evaluation data, report content, or test was modified during this check.

---

## 8. Final Status

### Test Results (run during this audit)

```
pytest -q
83 passed in 86.43s
0 failed
0 skipped
```

### Consistency Summary

| Domain | Result |
| :--- | :---: |
| Candidate counts (3,507 / 63 / 0 / 3,444 / 15 / 48 / 1) | ✅ Consistent across all current docs |
| "3,428" references | ✅ Correctly refer to `ground_truth.json` entity count (different file, different population) |
| Provisional P/R/F1 (16.36% / 60.00% / 25.71%) | ✅ Consistent and mathematically verified |
| Human-validated metrics (all N/A) | ✅ Consistent |
| Accuracy = N/A with written justification | ✅ Consistent |
| No forbidden terminology in active claims | ✅ Clean |
| Actual residual PII = 0 | ✅ Consistent (JSON + MD + CAREEDGE doc) |
| CareEdge Research residual = 0 | ✅ Consistent |
| "19/19 replaced" not misrepresented as 100% recall | ✅ Correctly scoped with explanatory note |
| 83 tests passing | ✅ Confirmed by this audit run |
| Historical docs (CORRECTNESS_AUDIT, FINAL_AUDIT) | ⚠️ Contain pre-fix state (80 tests, pre-CareEdge) — **expected divergence** for historical records; current state correctly captured in CAREEDGE_LEAK_ROOT_CAUSE.md and FINAL_SUBMISSION_AUDIT.md |

---

## READY FOR PACKAGING
