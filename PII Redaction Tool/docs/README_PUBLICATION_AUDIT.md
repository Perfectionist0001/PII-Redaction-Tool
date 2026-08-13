# README Publication Audit

**Project**: PII Redaction Tool  
**Target Repository**: `https://github.com/Perfectionist0001/PII-Redaction-Tool.git`  
**Audit Date**: 2026-08-14  
**Step**: STEP 3 — README Cleanup and Link Validation

---

## 1. Local Paths Removed

All 5 non-portable absolute Windows `file:///d:/SCALER%20AI%20LABS...` links previously identified in `README.md` have been completely removed:

| Line | Original Non-Portable Link | Replaced With |
| :--- | :--- | :--- |
| Line 22 | `file:///d:/SCALER%20AI%20LABS.../input/Red%20Herring%20Prospectus.docx` | Plain text reference with explicit privacy notice |
| Line 122 | `file:///d:/SCALER%20AI%20LABS.../evaluation/ground_truth.json` | Relative reference with exclusion disclaimer |
| Line 124 | `file:///d:/SCALER%20AI%20LABS.../evaluation/review_workflow.md` | `[evaluation/review_workflow.md](evaluation/review_workflow.md)` |
| Line 145 | `file:///d:/.../evaluation/review_workflow.md` & `docs/GROUND_TRUTH_GUIDE.md` | Relative links `[evaluation/review_workflow.md](evaluation/review_workflow.md)` and `[docs/GROUND_TRUTH_GUIDE.md](docs/GROUND_TRUTH_GUIDE.md)` |
| Line 168 | `file:///d:/SCALER%20AI%20LABS.../evaluation/evaluation_report.md` | `[evaluation/evaluation_report.md](evaluation/evaluation_report.md)` |

Zero `file:///` protocols or local Windows machine paths remain in `README.md`.

---

## 2. Relative Links Verified

Every relative Markdown link in `README.md` was inspected for target existence, public eligibility, non-ignored status in `.gitignore`, and confidentiality:

| Relative Link in README | Target Exists | Git Eligible | Public Safe | Status |
| :--- | :---: | :---: | :---: | :---: |
| `[evaluation/review_workflow.md](evaluation/review_workflow.md)` | ✅ Yes | ✅ Yes | ✅ Yes | **VALID** |
| `[docs/GROUND_TRUTH_PROVENANCE.md](docs/GROUND_TRUTH_PROVENANCE.md)` | ✅ Yes | ✅ Yes | ✅ Yes | **VALID** |
| `[docs/GROUND_TRUTH_GUIDE.md](docs/GROUND_TRUTH_GUIDE.md)` | ✅ Yes | ✅ Yes | ✅ Yes | **VALID** |
| `[evaluation/evaluation_report.md](evaluation/evaluation_report.md)` | ✅ Yes | ✅ Yes | ✅ Yes | **VALID** |

---

## 3. Sensitive References Handled

The following original files are intentionally excluded from public Git by `.gitignore` to protect raw PII data confidentiality:
- `input/Red Herring Prospectus.docx`
- `evaluation/ground_truth.json`
- `evaluation/ground_truth_verified.json`
- `evaluation/candidate_annotations.json`
- `evaluation/candidate_annotations.md`
- `evaluation/review_summary.md`

`README.md` now explicitly informs readers in the **Input Document** section:

> **Note**: The original source prospectus document (`input/Red Herring Prospectus.docx`) and raw evaluation annotation datasets (`evaluation/ground_truth.json`, `evaluation/ground_truth_verified.json`, etc.) are intentionally excluded from the public repository to prevent exposing raw PII and sensitive candidate strings. Users can process any target `.docx` file by placing it in `input/` or specifying `--input path/to/document.docx`.

No dead/broken links exist for these excluded files.

---

## 4. Installation Instructions

The installation instructions in `README.md` are completely portable and cross-platform:

```bash
# Clone & Navigate
git clone https://github.com/Perfectionist0001/PII-Redaction-Tool.git
cd PII-Redaction-Tool

# Create & Activate Virtual Environment
python -m venv .venv
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install Dependencies & Model
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

No hardcoded local Windows paths or specific user profiles are referenced.

---

## 5. Usage Instructions

Usage instructions demonstrate generic, portable CLI commands adhering strictly to `src/main.py` CLI parser options (`--input`, `--output`, `--evaluate`, `--ground-truth`, `--report`, `--verbose`):

```bash
# Standard Redaction Pipeline
python -m src.main \
  --input path/to/input_document.docx \
  --output output/redacted_document.docx

# Pipeline with Evaluation
python -m src.main \
  --input path/to/input_document.docx \
  --output output/redacted_document.docx \
  --evaluate \
  --ground-truth path/to/ground_truth.json \
  --report evaluation/evaluation_report.md \
  --verbose
```

---

## 6. Evaluation / Metrics Wording

All metric figures in `README.md` maintain honest terminology:

1. **Provisional Annotation-Agreement Metrics (Verified Subset)**:
   - Precision = **16.36%**
   - Recall = **60.00%**
   - F1 = **25.71%**
   - Accuracy = **N/A**
   - Explicitly labelled: *"These metrics are provisional annotation-agreement metrics measured against the 63-candidate automated-reviewed subset. They are NOT independently human-validated model performance metrics. Zero candidates were reviewed by a human. Do NOT interpret these as final model precision, recall, or F1."*

2. **Full Provisional Run (3,428 Candidate Baseline)**:
   - Explicitly labelled: *"The metrics in this subsection are computed against the full unreviewed candidate baseline (3,428 annotations, zero human-reviewed). Treat as indicative only."*

3. **No Unjustified Claims**:
   - Zero claims of 100% detection recall.
   - Zero claims of human-reviewed ground truth or gold-standard annotations.

---

## 7. Remaining Limitations

All system limitations are clearly documented in `README.md`:
1. **Single-Document Scope**: Benchmarking performed on target prospectus documents.
2. **spaCy Small Model Constraints**: `en_core_web_sm` is optimized for speed; complex legal names may benefit from transformer models (`en_core_web_trf`).
3. **Zero Ground-Truth Categories**: Categories with 0 occurrences (`SSN`, `CREDIT_CARD`, `DOB`, `IP_ADDRESS`) report `N/A` rather than artificial 100% scores.

---

## 8. Test Result

Command: `pytest -q`  
Result: **83 passed, 0 failed, 0 skipped**

---

## 9. README Publication Status

## **READY FOR PUBLIC GITHUB**
