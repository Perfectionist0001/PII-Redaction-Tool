# Execution Guide Audit

**Project**: PII Redaction Tool  
**Audit Date**: 2026-08-14  
**Purpose**: READ-ONLY code inspection — determine exact commands for a new user running from a clean environment.

> [!IMPORTANT]
> All commands in this document were verified against the **actual current implementation** in the repository. No commands have been guessed or assumed.

---

## 1. Environment Requirements

| Requirement | Details |
| :--- | :--- |
| **Python Version** | Python 3.11.5 (confirmed running locally). The type annotation `Path \| None` (union pipe syntax) in `src/main.py` and `src/redaction/docx_redactor.py` requires **Python ≥ 3.10** at minimum. |
| **Virtual Environment** | Not required, but strongly recommended. |
| **Operating System** | Windows (PowerShell), Linux, macOS — all supported. |
| **Environment Variables** | **None required.** No `.env` file, `os.getenv()` calls, or secret keys are used by the application. |
| **Internet Connection** | Only required during `pip install -r requirements.txt` to download the spaCy model wheel from GitHub. The running application makes **zero external API or network calls**. |

---

## 2. Installation

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Perfectionist0001/PII-Redaction-Tool.git
cd PII-Redaction-Tool
```

### Step 2 — Create & Activate Virtual Environment

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install All Dependencies (Including spaCy Model)

```bash
pip install -r requirements.txt
```

> [!NOTE]
> `requirements.txt` line 3 directly includes the spaCy `en_core_web_sm-3.7.1` model wheel URL:
> ```
> https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
> ```
> This means `pip install -r requirements.txt` installs both spaCy and the `en_core_web_sm` model in one command. The separate `python -m spacy download en_core_web_sm` step documented in `README.md` is **redundant** when using `requirements.txt` — see Section 10 for details.

---

## 3. Model Dependencies

| Dependency | Version | Source | How Installed |
| :--- | :--- | :--- | :--- |
| `python-docx` | ≥ 1.1.0 | PyPI | `pip install -r requirements.txt` |
| `spacy` | ≥ 3.7.0 | PyPI | `pip install -r requirements.txt` |
| `en_core_web_sm` | 3.7.1 | GitHub wheel URL in `requirements.txt` | `pip install -r requirements.txt` (bundled) |
| `faker` | ≥ 24.0.0 | PyPI | `pip install -r requirements.txt` |
| `pytest` | ≥ 8.0.0 | PyPI | `pip install -r requirements.txt` |
| `pydantic` | ≥ 2.6.0 | PyPI | `pip install -r requirements.txt` |

**Key Finding**: The `en_core_web_sm` model is included directly in `requirements.txt`. A single `pip install -r requirements.txt` is sufficient. No separate `python -m spacy download en_core_web_sm` step is required.

---

## 4. Exact CLI Usage

The application must be invoked as a **module** from the project root directory:

```bash
python -m src.main [OPTIONS]
```

> [!IMPORTANT]
> The entry point is `python -m src.main` (module syntax), **not** `python src/main.py` directly.  
> Running `python src/main.py` will fail with an `ImportError` because `src.config`, `src.detection_pipeline`, etc. use absolute package imports that require the package to be on the Python path, which is guaranteed by module invocation from the project root.

---

## 5. CLI Arguments

The following arguments are supported (verified from `src/main.py` `build_parser()` and confirmed via `python -m src.main --help`):

| Argument | Short | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--input` | `-i` | `str` (path) | **No** | `input/Red Herring Prospectus.docx` | Path to input `.docx` document |
| `--output` | `-o` | `str` (path) | **No** | `output/redacted_prospectus.docx` | Target output path for redacted DOCX |
| `--evaluate` | — | flag | No | `False` | Run evaluation against ground truth |
| `--ground-truth` | — | `str` (path) | No | `evaluation/ground_truth.json` | Ground truth JSON for evaluation |
| `--report` | — | `str` (path) | No | `evaluation/evaluation_report.md` | Target path for evaluation report |
| `--verbose` | `-v` | flag | No | `False` | Enable diagnostic logging |
| `--help` | `-h` | flag | No | — | Show help message and exit |

**Neither `--input` nor `--output` is required.** Both have defaults, but the default `--input` points to `input/Red Herring Prospectus.docx` which is **excluded from the public repository** and must be supplied by the user.

---

## 6. Example Execution

### Basic Redaction (User-Supplied Document)

```bash
python -m src.main --input path/to/your_document.docx --output output/redacted_output.docx
```

### Verbose Redaction

```bash
python -m src.main --input path/to/your_document.docx --output output/redacted_output.docx --verbose
```

### Redaction with Evaluation (Requires Ground Truth)

```bash
python -m src.main \
  --input path/to/your_document.docx \
  --output output/redacted_output.docx \
  --evaluate \
  --ground-truth path/to/ground_truth.json \
  --report evaluation/evaluation_report.md
```

**Windows PowerShell equivalent** (no backslash line continuation):
```powershell
python -m src.main --input path/to/your_document.docx --output output/redacted_output.docx --evaluate --ground-truth path/to/ground_truth.json --report evaluation/evaluation_report.md
```

---

## 7. Output Verification

### Automatic Output Directory Creation

**Finding from `src/redaction/docx_redactor.py` line 161:**
```python
output_file.parent.mkdir(parents=True, exist_ok=True)
```
The `DOCXRedactor.redact_document()` method **automatically creates the output directory** (and any missing parent directories) before writing the output file. The user does **not** need to pre-create the `output/` directory.

### How to Verify the Output File Was Created

After running the tool, verify the output DOCX:

```bash
# Check file exists and size (Windows PowerShell)
Get-Item output/redacted_output.docx

# Check file exists and size (Linux/macOS)
ls -lh output/redacted_output.docx
```

Or use the tool's own verbose summary — on success the final output block explicitly prints:
```
Redacted Output      : D:\path\to\output\redacted_output.docx
Status               : SUCCESS
```

### Manual Content Check (Safe, No Source Prospectus Needed)

```python
from docx import Document
doc = Document("output/redacted_output.docx")
for p in doc.paragraphs[:20]:
    print(p.text)
```

---

## 8. Running Tests

### Run Full Pytest Suite

```bash
pytest -q
```

`pytest.ini` sets `testpaths = tests` — pytest discovers all tests inside the `tests/` directory automatically.

**Verified result**: `83 passed, 0 failed, 0 skipped` (runtime ~67–73 seconds).

### Run Specific Regression Tests Only

```bash
pytest tests/test_regressions.py tests/test_regression_correctness.py -v
```

### Run a Single Test File

```bash
pytest tests/test_email_detector.py -v
```

---

## 9. Common Errors

| Error | Likely Cause | Fix |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'src'` | Running `python src/main.py` instead of `python -m src.main` from project root | Always run from project root: `python -m src.main` |
| `FileNotFoundError: Input file does not exist` | Default `--input` path `input/Red Herring Prospectus.docx` is excluded from repo | Supply `--input path/to/your_document.docx` explicitly |
| `ERROR: Unsupported file format '.pdf'` | Non-`.docx` file passed to `--input` | Only `.docx` files are supported |
| `FileNotFoundError: Input DOCX file not found` | `DOCXRedactor` constructor called with missing path | Ensure `--input` path points to an existing `.docx` file |
| `OSError: [Errno 22]` on Windows with backslash paths | Backslash path separators in certain Windows contexts | Use forward slashes or wrap paths in quotes |
| `ERROR: Ground truth file not found` | `--evaluate` flag used without providing `--ground-truth` path | The raw `ground_truth.json` is excluded from the public repo; either supply your own or omit `--evaluate` |
| `ImportError: Can't find model 'en_core_web_sm'` | `pip install -r requirements.txt` was skipped or incomplete | Re-run `pip install -r requirements.txt` to install the model wheel |
| `ExecutionPolicy` error on PowerShell venv activation | Windows PowerShell restricts `.ps1` scripts by default | Run: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## 10. README Commands That Need Correction

### Issue 1 — Redundant `python -m spacy download` Step (Minor, Not Harmful)

**README Section "Installation" reads:**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Actual behaviour:** `requirements.txt` already includes the direct wheel URL for `en_core_web_sm-3.7.1`. After `pip install -r requirements.txt`, the model is already installed. The `python -m spacy download en_core_web_sm` step is **redundant** (harmless but unnecessary). It may also install a newer version of the model than intended if the spaCy model index has been updated.

**Recommended fix:** Either remove the `python -m spacy download en_core_web_sm` line from the README or add a note that it is not required when using `requirements.txt`.

### Issue 2 — README Usage Shows Bash Line-Continuation Syntax

**README shows:**
```bash
python -m src.main \
  --input path/to/input_document.docx \
  --output output/redacted_document.docx
```

This syntax works correctly on Linux/macOS bash. On **Windows PowerShell**, the backslash line-continuation character is not supported. PowerShell users must write the command on one line, or use PowerShell's backtick `` ` `` continuation character. The README already documents both platforms in the virtual environment section, but should add a note in the Usage section for PowerShell users.

### Issue 3 — No Explicit Warning That Default `--input` Requires Missing File

The README does not prominently warn users running the command without arguments that the default `--input` path (`input/Red Herring Prospectus.docx`) is excluded from the public repository and will immediately produce:
```
ERROR: Input file does not exist at ...
```
A new user cloning the repo and running `python -m src.main` without arguments will see this error with no contextual explanation. The README should prominently state that `--input path/to/your_document.docx` is required for a first run.

### Issue 4 — README Correctly States `python -m src.main` ✅

The README usage section correctly uses `python -m src.main` module syntax throughout. No correction needed.

### Issue 5 — All Test Commands Are Correct ✅

```bash
pytest -q
pytest tests/test_regressions.py tests/test_regression_correctness.py
```
Both commands are valid and consistent with `pytest.ini` configuration (`testpaths = tests`).

---

## Verified Command Summary for README

The following are the **exact, implementation-verified commands** that should appear in `README.md`:

### Setup
```bash
git clone https://github.com/Perfectionist0001/PII-Redaction-Tool.git
cd PII-Redaction-Tool
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
# Note: en_core_web_sm model is included in requirements.txt — no separate spacy download needed.
```

### Run Redaction (Required: --input)
```bash
python -m src.main --input path/to/your_document.docx --output output/redacted_output.docx
```

### Run Redaction with Verbose Logging
```bash
python -m src.main --input path/to/your_document.docx --output output/redacted_output.docx --verbose
```

### Run Full Test Suite
```bash
pytest -q
# Expected: 83 passed, 0 failed, 0 skipped
```

### Run Regression Tests Only
```bash
pytest tests/test_regressions.py tests/test_regression_correctness.py -v
```
