# PII Redaction Tool

A Microsoft Word (`.docx`) PII detection and pseudonymization engine. Accepts a Word document as input, detects supported PII categories using a hybrid regex + NLP pipeline, replaces each detected entity with a deterministic synthetic substitute, and writes a redacted DOCX without corrupting document structure or formatting.

> **⚠️ Provisional Evaluation Notice**: All evaluation metrics in this README are computed against a **provisional automated annotation benchmark** (not independently human-reviewed ground truth). See [Section 11](#11-evaluation-methodology) and [`evaluation/review_workflow.md`](evaluation/review_workflow.md) for full provenance details.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Supported PII Types](#2-supported-pii-types)
3. [How It Works](#3-how-it-works)
4. [Project Structure](#4-project-structure)
5. [Requirements](#5-requirements)
6. [Installation](#6-installation)
7. [Running the Tool](#7-running-the-tool)
8. [Example Workflow](#8-example-workflow)
9. [Verifying the Output](#9-verifying-the-output)
10. [Running Tests](#10-running-tests)
11. [Evaluation Methodology](#11-evaluation-methodology)
12. [Redaction Validation](#12-redaction-validation)
13. [Ground Truth Provenance](#13-ground-truth-provenance)
14. [Limitations](#14-limitations)
15. [Privacy and Security](#15-privacy-and-security)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Overview

The **PII Redaction Tool** is a local Python pipeline designed to:

1. **Accept** any Microsoft Word `.docx` file as input.
2. **Parse** the full document OpenXML structure — body paragraphs, table cells, running headers, and footers — while tracking exact source locations for each extracted text chunk.
3. **Detect** candidate PII entities across 9 supported categories using a hybrid rule-based + statistical NLP approach.
4. **Pseudonymize** each detected entity by mapping it to a deterministic synthetic replacement (e.g., real name → `"John Doe"`, real email → `"jane.doe@example.com"`).
5. **Redact** the original DOCX by applying run-level XML text substitution that preserves fonts, table borders, paragraph alignment, and other formatting.
6. **Write** the redacted DOCX to a specified output path.
7. **Validate** that selected candidate PII occurrences were successfully replaced.

The tool operates fully **offline** — no cloud APIs, no internet connections, and no external services are used at runtime.

**What it does not claim:**
- It does not guarantee detection of every possible PII occurrence in an arbitrary document.
- It has not been evaluated against independently human-reviewed ground truth annotations.
- Final human-validated precision, recall, and F1 metrics are not yet available.

---

## 2. Supported PII Types

The pipeline natively supports detection and pseudonymization of 9 PII categories:

| PII Category | Detected Entities | Detection Method |
| :--- | :--- | :--- |
| **`PERSON`** | Names of natural persons (directors, promoters, officers) | Local spaCy NER + Title/Honorific prefix rules |
| **`EMAIL`** | Personal and corporate contact email addresses | Compiled regex (`local@domain.ext`) |
| **`PHONE`** | Indian mobile (+91), landline, and formatted phone numbers | Compiled regex + STD area code triggers |
| **`ORGANIZATION`** | Private corporate entity names (issuers, auditors, banks, etc.) | Local spaCy NER + Legal suffix matching |
| **`ADDRESS`** | Multi-component physical premises and mailing addresses | Multi-signal premises, locality, and PIN-code scoring |
| **`SSN`** | US Social Security Numbers (`NNN-NN-NNNN`) | Area/Group/Serial structured regex with range validation |
| **`CREDIT_CARD`** | Financial credit/debit card numbers (13–19 digits) | Digit extraction + Luhn checksum validation |
| **`DOB`** | Dates of birth of natural persons | Contextual prefix triggers (`DOB:`, `Date of Birth:`, `Born on`) |
| **`IP_ADDRESS`** | IPv4 network addresses (`192.168.1.1`) | Negative lookaround bounds + Python `ipaddress` validation |

---

## 3. How It Works

The pipeline is a strict 7-stage sequential architecture:

```
Input DOCX
    │
    ▼
[Stage 1] DOCX Extraction (DOCXExtractor)
    │  Parses body paragraphs, table cells, headers, and footers.
    │  Each chunk is tagged with its exact SourceLocation coordinate
    │  (source_type, table_idx, row_idx, cell_idx, paragraph_idx, header_idx, footer_idx).
    │
    ▼
[Stage 2] PII Detection (8 specialized detectors)
    │  Runs regex, contextual rules, and local spaCy NER in parallel
    │  over every extracted text chunk.
    │
    ▼
[Stage 3] Aggregation and Deduplication
    │  Normalizes detection metadata and removes exact duplicate spans.
    │
    ▼
[Stage 4] Overlap Resolution
    │  Resolves overlapping spans using a priority hierarchy:
    │  EMAIL/PHONE/SSN/CREDIT_CARD/IP_ADDRESS > DOB > ADDRESS > ORGANIZATION > PERSON
    │  Longer spans are preferred over shorter sub-spans at equal priority.
    │
    ▼
[Stage 5] Pseudonymization (Pseudonymizer)
    │  Generates deterministic synthetic replacements using MD5 hash seeds
    │  keyed on (entity_type, original_text). Recurring names always receive
    │  the same replacement to preserve document co-reference.
    │
    ▼
[Stage 6] DOCX Redaction (DOCXRedactor)
    │  Applies run-level (<w:r>) XML text substitution across paragraphs
    │  and table cells, preserving font styles, cell borders, and alignments.
    │
    ▼
Output Redacted DOCX
```

**Pseudonymization examples:**
- `PERSON` → `"John Doe"` (deterministic per-name seed)
- `EMAIL` → `"jane.doe@example.com"` (RFC-safe documentation domain)
- `PHONE` → `"+91 9900000000"` (synthetic Indian mobile format)
- `IP_ADDRESS` → `"192.0.2.1"` (RFC 5737 documentation range)
- `SSN` → `"000-00-0001"` (synthetic test SSN pattern)

---

## 4. Project Structure

```text
PII-Redaction-Tool/
├── .gitignore                       # Excludes sensitive source files and local artifacts
├── README.md                        # This file
├── pytest.ini                       # Pytest configuration (testpaths = tests)
├── requirements.txt                 # Python dependencies including pinned spaCy model
│
├── docs/                            # Technical audit and architecture documentation
│   ├── CAREEDGE_LEAK_ROOT_CAUSE.md  # Post-mortem & fix for repeated-entity propagation bug
│   ├── CORRECTNESS_AUDIT.md         # Quality control audit report
│   ├── GROUND_TRUTH_PROVENANCE.md   # Annotation provenance and review method disclosure
│   ├── GROUND_TRUTH_GUIDE.md        # Annotation policy and acceptance criteria
│   └── ...                          # Additional audit and publication records
│
├── evaluation/
│   ├── evaluation_report.md         # Full evaluation metrics report (Sections 12 & 13)
│   ├── final_redaction_validation.json  # JSON structured residual PII validation results
│   ├── final_redaction_validation.md    # Residual PII validation narrative report
│   ├── review_annotations.py        # Ground truth candidate review utility
│   └── review_workflow.md           # Annotation workflow documentation
│
├── output/
│   └── redacted_prospectus.docx     # Pre-generated redacted output (synthetic data only)
│
├── scripts/
│   ├── extract_doc_stats.py         # OpenXML document statistics extraction utility
│   └── residual_pii_checker.py      # Post-redaction residual PII validation script
│
├── src/
│   ├── config.py                    # Project directory configuration (Settings dataclass)
│   ├── detection_pipeline.py        # Detection pipeline orchestration and overlap resolution
│   ├── main.py                      # CLI entry point (use: python -m src.main)
│   ├── models.py                    # PIIEntity, TextChunk, SourceLocation models
│   ├── detectors/                   # 8 specialized PII detectors
│   │   ├── address_detector.py
│   │   ├── credit_card_detector.py
│   │   ├── dob_detector.py
│   │   ├── email_detector.py
│   │   ├── ip_detector.py
│   │   ├── ner_detector.py          # spaCy NER for PERSON and ORGANIZATION
│   │   ├── phone_detector.py
│   │   └── ssn_detector.py
│   ├── evaluation/                  # Evaluation engine and metrics computation
│   ├── extractors/                  # DOCX paragraph and table extractor (DOCXExtractor)
│   ├── redaction/                   # Pseudonymizer and DOCXRedactor
│   └── validation/                  # Post-redaction validation utilities
│
└── tests/                           # 18 test modules — 83 unit and regression tests
```

> **Note on Excluded Files**: The following files are intentionally **NOT included** in this public GitHub repository to protect sensitive and private data:
> - `input/Red Herring Prospectus.docx` — the original source document containing real PII.
> - `evaluation/ground_truth.json` and `evaluation/ground_truth_verified.json` — raw annotation datasets.
> - `evaluation/candidate_annotations.json`, `evaluation/candidate_annotations.md`, `evaluation/review_summary.md` — intermediate annotation working files.
>
> To use the tool, supply your own `.docx` file using `--input path/to/your_document.docx`.

---

## 5. Requirements

| Requirement | Details |
| :--- | :--- |
| **Python** | **≥ 3.10** (required for `X \| Y` union type annotation syntax in source code) |
| **pip** | Latest version recommended (`python -m pip install --upgrade pip`) |
| **Virtual environment** | Strongly recommended (`.venv`) |
| **Internet** | Required only during `pip install -r requirements.txt` to download dependencies |
| **Runtime internet** | **None** — the application operates fully offline after installation |
| **Environment variables** | **None** — no `.env` file, API keys, or external credentials required |

### Python Dependencies (`requirements.txt`)

```
python-docx>=1.1.0
spacy>=3.7.0
https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
faker>=24.0.0
pytest>=8.0.0
pydantic>=2.6.0
```

> **spaCy Model Note**: The `en_core_web_sm-3.7.1` spaCy language model wheel is included directly in `requirements.txt`. Running `pip install -r requirements.txt` installs both spaCy and the model in a single step. **No separate `python -m spacy download` command is needed.**

---

## 6. Installation

### Windows (PowerShell)

```powershell
git clone https://github.com/Perfectionist0001/PII-Redaction-Tool.git
cd PII-Redaction-Tool
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **PowerShell Execution Policy**: If `.\.venv\Scripts\Activate.ps1` is blocked, run once:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### Linux / macOS

```bash
git clone https://github.com/Perfectionist0001/PII-Redaction-Tool.git
cd PII-Redaction-Tool
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

After installation, verify the environment:

```bash
python -m src.main --help
```

---

## 7. Running the Tool

> **Critical**: Always use the module syntax `python -m src.main` from the project root directory.  
> Running `python src/main.py` directly **will fail** with an `ImportError` because the application uses package-relative imports that require the `src` package to be on the Python path, which is guaranteed only by module invocation.

### CLI Syntax

```
python -m src.main [--input INPUT] [--output OUTPUT] [--evaluate] [--ground-truth PATH] [--report PATH] [--verbose]
```

### All Supported Arguments

| Argument | Short | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--input` | `-i` | **No** (but practically required — see below) | `input/Red Herring Prospectus.docx` | Path to the input `.docx` document |
| `--output` | `-o` | No | `output/redacted_prospectus.docx` | Output path for the redacted DOCX |
| `--evaluate` | — | No | `False` | Run evaluation against ground truth after redaction |
| `--ground-truth` | — | No | `evaluation/ground_truth.json` | Path to ground truth JSON for evaluation |
| `--report` | — | No | `evaluation/evaluation_report.md` | Path to write the evaluation report |
| `--verbose` | `-v` | No | `False` | Enable detailed diagnostic logging |
| `--help` | `-h` | No | — | Show help and exit |

> **Important**: The default `--input` path (`input/Red Herring Prospectus.docx`) is **excluded from the public repository**. Always supply `--input` explicitly:
> ```bash
> python -m src.main --input path/to/your_document.docx
> ```

> **Output directory**: The output directory is **created automatically** by the application if it does not exist. You do not need to pre-create `output/` or any other output directory.

### Basic Redaction

```bash
python -m src.main --input input/sample.docx --output output/redacted.docx
```

### Verbose Redaction

```bash
python -m src.main --input input/sample.docx --output output/redacted.docx --verbose
```

### Redaction with Evaluation (Requires a Ground Truth JSON)

```bash
python -m src.main \
  --input input/sample.docx \
  --output output/redacted.docx \
  --evaluate \
  --ground-truth evaluation/ground_truth.json \
  --report evaluation/evaluation_report.md
```

**Windows PowerShell** (single line — no backslash continuation):
```powershell
python -m src.main --input input/sample.docx --output output/redacted.docx --evaluate --ground-truth evaluation/ground_truth.json --report evaluation/evaluation_report.md
```

---

## 8. Example Workflow

The following step-by-step workflow is recommended for new users testing the tool with a synthetic document:

**Step 1 — Clone and install:**
```bash
git clone https://github.com/Perfectionist0001/PII-Redaction-Tool.git
cd PII-Redaction-Tool
python -m venv .venv && source .venv/bin/activate   # or Activate.ps1 on Windows
pip install -r requirements.txt
```

**Step 2 — Prepare a test DOCX** containing synthetic (fake) PII, such as:
- A paragraph with a fictional name and email address.
- A table row with a fake phone number.
- Use a tool like Microsoft Word, LibreOffice, or python-docx to create `input/sample.docx`.

> **Important**: Use only synthetic/fake PII for testing. Do not commit real documents with sensitive personal data to public repositories.

**Step 3 — Run the redaction pipeline:**
```bash
python -m src.main --input input/sample.docx --output output/redacted.docx --verbose
```

**Step 4 — Inspect the output:**
Open `output/redacted.docx` in Microsoft Word or LibreOffice.

**Step 5 — Compare:**
Side-by-side compare `input/sample.docx` and `output/redacted.docx`. Detected PII values should be replaced with synthetic alternatives. Surrounding non-PII text, table structure, and paragraph formatting should remain intact.

**Step 6 — Run tests:**
```bash
pytest -q
```

---

## 9. Verifying the Output

### Check Output File Exists

**Windows PowerShell:**
```powershell
Get-Item output/redacted.docx
```

**Linux / macOS:**
```bash
ls -lh output/redacted.docx
```

### Check Output Document Is Readable

```python
from docx import Document
doc = Document("output/redacted.docx")
for p in doc.paragraphs[:20]:
    print(p.text)
```

### What a Successful Redaction Looks Like

The tool prints a summary on completion:

```
Status               : SUCCESS
Total Detections     : 42
Total Replaced Spans : 38

Replaced Entities by Category:
  - PERSON              : 12
  - EMAIL               : 3
  - ORGANIZATION        : 20
  - PHONE               : 3
```

### Detection vs. Replacement Validation

Two distinct concepts apply here:

| Concept | What It Measures | Limitation |
| :--- | :--- | :--- |
| **Detection evaluation** | Whether the pipeline correctly identified PII entities relative to a ground-truth benchmark | Requires a validated ground-truth annotation set |
| **Redaction replacement validation** | Whether the entities that were detected and selected for replacement were actually overwritten in the output DOCX | Does **not** prove that all PII in the document was detected |

Confirming that a replacement occurred in the output DOCX **does not imply complete detector recall**. There may be PII in the document that was not detected, depending on document structure, entity format, and model limitations.

---

## 10. Running Tests

Run the full automated test suite from the project root:

```bash
pytest -q
```

The `pytest.ini` configuration sets `testpaths = tests`. All 18 test modules in `tests/` are discovered automatically.

**Verified test result:**
```
83 passed, 0 failed, 0 skipped
```

Run specific regression tests:

```bash
pytest tests/test_regressions.py tests/test_regression_correctness.py -v
```

Run a single test module:

```bash
pytest tests/test_email_detector.py -v
```

---

## 11. Evaluation Methodology

> **⚠️ Critical Framing**: All evaluation metrics in this section are **provisional annotation-agreement metrics** measured against an automated annotation subset. They are **NOT** independently human-validated model performance metrics.

### How Evaluation Works

1. **Candidate Generation**: An automated pipeline scans the document and generates candidate PII annotation candidates (`3,507` total for the benchmark prospectus).
2. **Provisional Review**: A policy-based automated review process accepts or rejects candidates based on configurable rules.
3. **Ground Truth**: Accepted provisional annotations become the evaluation ground truth.
4. **Source-Location-Aware Matching**: A prediction is a **True Positive (TP)** only if it matches the ground-truth annotation in all three dimensions:
   - Entity type (e.g. `PERSON`, `EMAIL`)
   - Spatial coordinate key (source type, table index, row index, cell index, paragraph index)
   - Character span (start offset, end offset)

   Spatial coordinates are required because identical text appears in multiple table cells throughout the document; without them, predictions would falsely match across locations.

5. **Known FP / FN / Unassessed**: Predictions in unreviewed document regions (3,444 unreviewed candidates) are tracked as "unassessed" and are **not** counted as false positives.

### Provisional Annotation-Agreement Metrics (Verified Subset Only)

> **⚠️ These metrics measure agreement with the current automated provisional annotation subset (63 candidates). They are NOT independently human-validated model performance metrics. Zero candidates were reviewed by a human auditor.**

| Metric | Provisional Value | Scope |
| :--- | :---: | :--- |
| **Precision** | **16.36%** | 63 automated-reviewed candidates only |
| **Recall** | **60.00%** | 63 automated-reviewed candidates only |
| **F1 Score** | **25.71%** | 63 automated-reviewed candidates only |
| **Accuracy (entity-level)** | **N/A** | Insufficient validated negative population |

Formulae:
```
TP = 9,  FP = 46,  FN = 6

Precision = TP / (TP + FP) = 9 / 55  = 16.36%
Recall    = TP / (TP + FN) = 9 / 15  = 60.00%
F1        = 2×TP / (2×TP + FP + FN)  = 18 / 70 = 25.71%
```

### Final / Human-Validated Metrics

| Metric | Final Value | Reason |
| :--- | :---: | :--- |
| **Precision** | **N/A** | No candidates were independently human-reviewed |
| **Recall** | **N/A** | No candidates were independently human-reviewed |
| **F1 Score** | **N/A** | No candidates were independently human-reviewed |
| **Accuracy** | **N/A** | No candidates were independently human-reviewed |

See [`evaluation/evaluation_report.md`](evaluation/evaluation_report.md) Sections 12 and 13 for the full breakdown, and [`evaluation/review_workflow.md`](evaluation/review_workflow.md) for annotation methodology details.

---

## 12. Redaction Validation

After generating the redacted DOCX, a document-wide residual PII validation check was performed using `scripts/residual_pii_checker.py`:

| Validation Metric | Result |
| :--- | :---: |
| Candidate annotation slots checked | 19 |
| Successfully replaced | 19 |
| Residual candidate occurrences | 0 |
| Actual residual PII | 0 |
| CareEdge Research residual occurrences | 0 (7 original → 0 remaining) |

> **⚠️ Scope Disclaimer**: The "19/19 successfully replaced" result measures redaction replacement efficacy for the currently checked candidate annotation set. This result **must NOT be interpreted as 100% detector recall** or complete PII elimination across the entire document. There may be PII occurrences in the document that were not selected as candidates and therefore not checked.

See [`evaluation/final_redaction_validation.md`](evaluation/final_redaction_validation.md) for the full validation report.

---

## 13. Ground Truth Provenance

| Metric | Value |
| :--- | :---: |
| Total workload candidates | 3,507 |
| Automated provisional reviewed | 63 |
| **Independent human reviewed** | **0** |
| **Human-reviewed candidates = 0** | (no independent review performed) |
| Unreviewed candidates | 3,444 |
| Accepted provisional entities | 15 |
| Rejected provisional candidates | 48 |
| Corrected spans | 1 (`cand_59`) |

> **Provenance Classification: PROVISIONAL AUTOMATED ANNOTATION BENCHMARK**

> **⚠️ Important**: Zero (0) candidates were independently reviewed by a human auditor. All 63 reviewed decisions were generated programmatically via automated policy simulation. This annotation set **must not** be described as human-verified, human-audited, or gold-standard ground truth.

See [`docs/GROUND_TRUTH_PROVENANCE.md`](docs/GROUND_TRUTH_PROVENANCE.md) and [`docs/GROUND_TRUTH_GUIDE.md`](docs/GROUND_TRUTH_GUIDE.md) for full provenance documentation.

---

## 14. Limitations

1. **Provisional Ground Truth**: The annotation benchmark was generated via automated policy rules; no candidates were independently reviewed by a human annotator. Final human-validated precision, recall, F1, and accuracy are unavailable.

2. **Partial Workload Assessment**: Only 63 of 3,507 candidate annotations (1.8%) have been reviewed; 3,444 remain unassessed.

3. **spaCy Small Model Constraints**: `en_core_web_sm` is a small, speed-optimized model. Dense table cells, hyphenated multi-word legal corporate names, and context-lacking text snippets may produce false positives or false negatives.

4. **False Positives**: The `ORGANIZATION` detector can tag regulatory authority names (`SEBI`, `Registrar of Companies`), all-caps section headings, and generic financial terms as organizational entities when they appear in document headers or standalone cells.

5. **False Negatives**: Names lacking honorific prefixes (`Mr.`, `Ms.`, `Dr.`) in condensed table cells may be missed by statistical NER. Highly formatted or hyphenated multi-line addresses may not score above the address detection threshold.

6. **Single-Document Scope**: Benchmarking was performed on a single Indian corporate financial prospectus. Performance on other document types (legal agreements, HR records, medical notes, etc.) has not been evaluated.

7. **Excluded Source Files**: The original source prospectus document and raw annotation datasets are intentionally excluded from the public repository to protect sensitive personal data and prevent exposure of real PII strings.

---

## 15. Privacy and Security

To maintain the privacy guarantees of this tool and to avoid exposing sensitive data publicly:

- **Do not commit** real DOCX documents containing actual personal data to this repository or any public fork.
- **Do not commit** raw PII annotation datasets, ground truth JSON files, or candidate annotation files to public repositories.
- **Do not commit** `.env` files, API keys, credentials, private keys (`.pem`, `.key`, `.p12`, `.pfx`), or authentication tokens.
- **Use only synthetic/fake data** when running public demonstrations or adding test fixtures to the `tests/` directory.

The `.gitignore` in this repository is pre-configured to exclude:
- `input/` (original source documents)
- `evaluation/ground_truth.json`, `evaluation/ground_truth_verified.json`
- `evaluation/candidate_annotations.json`, `evaluation/candidate_annotations.md`
- `.env`, `*.pem`, `*.key`, `*.p12`, `*.pfx`

---

## 16. Troubleshooting

### `python src/main.py` fails with `ModuleNotFoundError`

**Symptom:**
```
ModuleNotFoundError: No module named 'src'
```

**Cause**: Running `python src/main.py` directly does not place the `src` package on the Python path.

**Fix**: Always use module syntax from the project root:
```bash
python -m src.main --input path/to/your.docx --output output/redacted.docx
```

---

### Input file not found

**Symptom:**
```
ERROR: Input file does not exist at .../input/Red Herring Prospectus.docx
```

**Cause**: The default `--input` path points to the original prospectus file which is excluded from the public repository.

**Fix**: Supply your own DOCX explicitly:
```bash
python -m src.main --input path/to/your_document.docx --output output/redacted.docx
```

---

### spaCy model not found

**Symptom:**
```
OSError: [E050] Can't find model 'en_core_web_sm'
```

**Cause**: Dependencies were not fully installed.

**Fix**: Re-run the full dependency installation (the model wheel is included in `requirements.txt`):
```bash
pip install -r requirements.txt
```

Do **not** run `python -m spacy download en_core_web_sm` separately — it is not required when using `requirements.txt`, and may install a different model version than the pinned `3.7.1` wheel.

---

### PowerShell execution policy blocks `.ps1` scripts

**Symptom:**
```
.\.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
```

**Fix** (run once, current user only):
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

### Ground truth file not found during `--evaluate`

**Symptom:**
```
ERROR: Ground truth file not found at .../evaluation/ground_truth.json
```

**Cause**: Raw annotation files are excluded from the public repository. The `--evaluate` flag requires a ground truth JSON file that you must supply.

**Fix**: Either omit `--evaluate` for a standard redaction run, or provide a valid ground truth JSON:
```bash
python -m src.main --input input/sample.docx --output output/redacted.docx --evaluate --ground-truth path/to/your_ground_truth.json
```
