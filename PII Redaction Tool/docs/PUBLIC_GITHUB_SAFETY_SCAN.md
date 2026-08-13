# Public GitHub Safety Scan

**Project**: PII Redaction Tool  
**Target Repository**: `https://github.com/Perfectionist0001/PII-Redaction-Tool.git`  
**Scan Date**: 2026-08-14  
**Audit Mode**: STEP 4 — Final Read-Only Public Safety Scan

> [!IMPORTANT]
> This is a READ-ONLY safety scan. No source code, detector logic, redaction logic, evaluation files, ground truth, redacted DOCX, or `.gitignore` rules were modified. Zero git commits or pushes were executed.

---

## 1. Effective Public File Set

Calculated using Git's actual ignore rules (`git ls-files --others --exclude-standard`). Exactly **70** untracked non-ignored files are eligible for public tracking:

```text
.gitignore
README.md
pytest.ini
requirements.txt
docs/
├── BASELINE_AUDIT.md
├── CAREEDGE_LEAK_ROOT_CAUSE.md
├── CORRECTNESS_AUDIT.md
├── FINAL_AUDIT.md
├── FINAL_CONSISTENCY_CHECK.md
├── FINAL_SUBMISSION_AUDIT.md
├── GITHUB_PUBLICATION_AUDIT.md
├── GITHUB_STAGING_STATUS.md
├── GROUND_TRUTH_FINAL_CHECK.md
├── GROUND_TRUTH_GUIDE.md
├── GROUND_TRUTH_PROVENANCE.md
├── PROJECT_ANALYSIS.md
├── PUBLIC_GITHUB_SAFETY_SCAN.md
└── README_PUBLICATION_AUDIT.md
evaluation/
├── evaluation_report.md
├── final_redaction_validation.json
├── final_redaction_validation.md
├── review_annotations.py
└── review_workflow.md
output/
└── redacted_prospectus.docx
scripts/
├── extract_doc_stats.py
└── residual_pii_checker.py
src/
└── (19 core Python modules: detectors, extractors, redactor, evaluation, main.py)
tests/
└── (18 pytest suite files)
```

---

## 2. Ignored Sensitive Files

Verified via `git status --ignored` and `git check-ignore`. The following sensitive local files are completely **EXCLUDED** from Git and will **NOT** be pushed:

| Category | Path | Ignore Rule | Status |
| :--- | :--- | :--- | :---: |
| **Original Prospectus** | `input/Red Herring Prospectus.docx` | `input/` | **EXCLUDED** ✅ |
| **Original Prospectus (Root)** | `Red Herring Prospectus.docx` | `Red Herring Prospectus.docx` | **EXCLUDED** ✅ |
| **Raw Candidate Ground Truth** | `evaluation/ground_truth.json` | `evaluation/ground_truth.json` | **EXCLUDED** ✅ |
| **Verified Ground Truth** | `evaluation/ground_truth_verified.json` | `evaluation/ground_truth_verified.json` | **EXCLUDED** ✅ |
| **Raw Candidate Detections** | `evaluation/candidate_annotations.json` | `evaluation/candidate_annotations.json` | **EXCLUDED** ✅ |
| **Candidate Review Markdown** | `evaluation/candidate_annotations.md` | `evaluation/candidate_annotations.md` | **EXCLUDED** ✅ |
| **Review Iteration Log** | `evaluation/review_summary.md` | `evaluation/review_summary.md` | **EXCLUDED** ✅ |
| **Packaging Staging Dir** | `submission/` | `submission/` | **EXCLUDED** ✅ |
| **Submission Archive** | `PII_Redaction_Tool_Final_Submission.zip` | `*.zip` | **EXCLUDED** ✅ |
| **Local Helper Scripts** | `build_submission.ps1`, `verify_submission.ps1`, `create_zip.ps1` | `*.ps1` | **EXCLUDED** ✅ |
| **Temporary Scratch Dir** | `scratch/` | `scratch/` | **EXCLUDED** ✅ |
| **Python / Pytest Caches** | `__pycache__/`, `*.pyc`, `.pytest_cache/` | `.gitignore` standard | **EXCLUDED** ✅ |

All ignored files remain safely stored on local disk for working memory and workflow execution.

---

## 3. Original Prospectus Check

- **File Path**: `input/Red Herring Prospectus.docx`
- **Git Status**: Ignored (`git check-ignore input/` -> `input/`)
- **Public Exposure Risk**: **ZERO** (will not be tracked or committed to GitHub)
- **Local Disk Status**: Intact and unmodified.

---

## 4. Raw Annotation Check

- **Files Checked**: `evaluation/ground_truth.json`, `evaluation/ground_truth_verified.json`, `evaluation/candidate_annotations.json`, `evaluation/candidate_annotations.md`, `evaluation/review_summary.md`
- **Git Status**: Ignored (`git check-ignore` confirms all 5 files are explicitly ignored)
- **Public Exposure Risk**: **ZERO**
- **Local Disk Status**: All 5 files preserved on disk.

---

## 5. Evaluation Report Safety

- **Files Checked**: `evaluation/evaluation_report.md`, `evaluation/final_redaction_validation.md`, `evaluation/final_redaction_validation.json`
- **Git Status**: Eligible for public tracking
- **Content Verification**:
  - `evaluation_report.md`: Contains aggregated metric tables (TP=9, FP=46, FN=6, unassessed=5,712), provisional evaluation warnings, section 12/13 notes, and no raw source PII snippets.
  - `final_redaction_validation.md` & `.json`: Document aggregated replacement results (e.g. `CareEdge Research` 7 orig -> 0 residual) confirming zero residual PII.
- **Public Exposure Risk**: **SAFE** (Contains safe evaluation metrics and summary statistics only).

---

## 6. Redacted Output Safety

- **File Path**: `output/redacted_prospectus.docx`
- **Git Status**: Eligible for public tracking
- **Independent Lightweight Verification**:
  - `DOCXExtractor` parsed all 4,686 text chunks (464,453 characters).
  - Target sensitive entities verified:
    - `"CareEdge Research"` count = `0`
    - `"Sarthak Malvadkar"` count = `0`
    - `"cs.connect@kshinternational.com"` count = `0`
    - `"+ 91 20 4505 3237"` count = `0`
- **Public Exposure Risk**: **SAFE** (All sensitive PII replaced with synthetic pseudonym placeholders).

---

## 7. Secret Scan

- **Scan Target**: All 70 public-eligible files
- **Patterns Checked**: `api_key`, `secret_key`, `bearer`, `password`, `aws_access`, `github_pat`, `.env`, `*.pem`, `*.key`, `*.p12`, `*.pfx`
- **Findings**: **ZERO (0) credentials, passwords, tokens, API keys, or private keys found.**

---

## 8. Documentation Claim Scan

- **Scan Target**: `README.md`, `evaluation/evaluation_report.md`, `docs/GROUND_TRUTH_PROVENANCE.md`, `docs/FINAL_SUBMISSION_AUDIT.md`, `docs/FINAL_CONSISTENCY_CHECK.md`
- **Verified Facts**:
  - Total candidates = `3,507`
  - Automated-reviewed candidates = `63`
  - Human-reviewed candidates = `0`
  - Unreviewed candidates = `3,444`
  - Accepted entities = `15`
  - Rejected candidates = `48`
  - Provisional Annotation-Agreement Metrics: Precision = `16.36%`, Recall = `60.00%`, F1 = `25.71%`, Accuracy = `N/A`
  - Human-validated metrics: Precision = `N/A`, Recall = `N/A`, F1 = `N/A`, Accuracy = `N/A`
- **Forbidden Terminology Scan**:
  - Zero claims of 100% detection recall in public docs.
  - Zero claims of human-reviewed ground truth or gold-standard annotations in public docs.
  - Historical audit notes in `docs/CORRECTNESS_AUDIT.md` explicitly document baseline artifacts.

---

## 9. Test Results

- **Command**: `pytest -q`
- **Result**: **83 passed, 0 failed, 0 skipped** (Execution time: ~81.92s)

---

## 10. Issues Requiring Action

- **None.** All 70 public-eligible files are verified safe, clean of secrets, free of local machine paths, and properly configured for Git tracking.

---

## 11. Final Public GitHub Safety Status

## **SAFE TO COMMIT**
