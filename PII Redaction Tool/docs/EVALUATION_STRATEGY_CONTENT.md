# PII Redaction Tool
# Evaluation Strategy & Metrics

**Project Name**: PII Redaction Tool  
**Target Document Format**: Microsoft Word (`.docx`) OpenXML Documents  
**Target Benchmark Dataset**: Indian Financial Prospectus (`Red Herring Prospectus.docx`)  
**Document Status**: Formal Evaluation Strategy & Benchmark Metrics Reference  

---

## 1. Objective

The primary objective of the **PII Redaction Tool** evaluation framework is to quantitatively measure the detection accuracy, structural preservation, pseudonymization integrity, and residual leakage of sensitive Personally Identifiable Information (PII) within complex OpenXML `.docx` financial prospectuses.

Financial prospectuses (e.g. Red Herring Prospectuses filed with regulatory bodies like SEBI) contain dense combinations of personal executive names, residential/registered addresses, contact email addresses, mobile/landline telephone numbers, and institutional banking details interleaved with corporate financial tables, share capital listings, and statutory disclosures.

The PII Redaction Tool parses document OpenXML structures across body paragraphs, table cells, running headers, and footers, detects candidate PII entities across 9 supported categories, deterministically maps sensitive entities to synthetic pseudonym replacements, applies run-level XML text substitution without corrupting document layout or formatting, and validates output documents for zero residual PII leakage.

---

## 2. Supported PII Categories

The evaluation framework covers 9 distinct PII categories:

| PII Category | Inclusion Scope & Description | Detection Logic |
| :--- | :--- | :--- |
| **`PERSON`** | Names of natural persons (directors, promoters, officers, key managerial personnel) | Local spaCy NER (`en_core_web_sm`) + Honorific/Title prefix rules |
| **`EMAIL`** | Personal and corporate contact email addresses | Compiled regular expressions (`local@domain.ext`) |
| **`PHONE`** | Indian mobile (+91 9x/8x/7x), landline, and formatted telephone numbers | Compiled regular expressions + STD area code triggers |
| **`ORGANIZATION`** | Private corporate entity names (issuers, corporate promoters, lead managers, legal counsel, auditors) | Local spaCy NER + Legal corporate suffix matching (`Limited`, `Private Limited`, `LLP`) |
| **`ADDRESS`** | Multi-component physical premises, registered offices, locality, and postal PIN code addresses | Multi-signal premises, street, city, state, and 6-digit Indian PIN scoring rules |
| **`SSN`** | US Social Security Numbers (`NNN-NN-NNNN`) | Area/Group/Serial structured regex with valid range checks |
| **`CREDIT_CARD`** | Financial credit, debit, and payment card numbers | 13–19 digit candidate extraction + Luhn checksum validation (`_validate_luhn`) |
| **`DOB`** | Dates of birth of natural persons | Contextual birth prefix triggers (`"Date of Birth:"`, `"DOB:"`, `"Born on"`) |
| **`IP_ADDRESS`** | IPv4 network addresses (`192.168.1.1`) | Negative lookaround bounds + Python `ipaddress.ip_address()` validation |

---

## 3. Detection Approach

The detection engine combines statistical Natural Language Processing (NLP) with deterministic rule-based algorithms to balance coverage and precision:

1. **Local spaCy Statistical NER**:
   - Uses `en_core_web_sm` locally (zero external network or cloud API dependencies) for `PERSON` and `ORGANIZATION` entity candidate extraction across extracted text chunks.
2. **Compiled Regular Expressions with Boundary Assertions**:
   - Structured patterns (`EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`, `IP_ADDRESS`) use compiled regexes with negative lookbehind and lookahead assertions (e.g. `(?<![\d.])`) to prevent partial string matches on financial tables or transaction numbers.
3. **Contextual Trigger Verification**:
   - `DOBDetector` requires explicit contextual birth prefixes (`"DOB:"`, `"Date of Birth:"`, `"Born on"`) before classifying a date string, preventing incorporation dates, filing dates, or agreement dates from being misclassified as personal birth dates.
4. **Algorithmic Validation Filters**:
   - `CreditCardDetector` validates candidate 16-digit strings against the Luhn checksum algorithm (`_validate_luhn`).
   - `IPDetector` validates candidate strings using Python's native `ipaddress.ip_address()` module.
   - `SSNDetector` validates area codes (`000`, `666`, `900-999` rejected) and group/serial numbers.
5. **Conflict & Overlap Resolution**:
   - Overlapping detection spans are resolved using a strict category priority hierarchy:
     $$\text{EMAIL / PHONE / SSN / CC / IP} > \text{DOB} > \text{ADDRESS} > \text{ORGANIZATION} > \text{PERSON}$$
   - When categories have equal priority, longer character spans are selected over shorter sub-spans. Sub-span containment rules enforce preferring full person names over partial organizational suffix matches.

---

## 4. Redaction Approach

Redaction is executed through a multi-pass pipeline to preserve OpenXML document layout while ensuring complete PII elimination:

1. **DOCX OpenXML Extraction**:
   - `DOCXExtractor` iterates over body paragraphs (`doc.paragraphs`), table cells (`table.cell.paragraphs`), running headers (`header.paragraphs`), and footers (`footer.paragraphs`).
   - Each extracted chunk is assigned a coordinate `SourceLocation` tuple:
     $$\text{location\_key} = (\text{source\_type}, \text{table\_idx}, \text{row\_idx}, \text{cell\_idx}, \text{para\_idx}, \text{header\_idx}, \text{footer\_idx})$$
2. **Entity Detection & Multi-Pass Propagation**:
   - Extracted text chunks pass through the detection pipeline.
   - To handle repeated entity occurrences across different paragraphs or table cells, the engine performs span-aware co-reference propagation, re-scanning text chunks for known entity texts to capture all repeated instances throughout the document.
3. **Deterministic Pseudonymization**:
   - `Pseudonymizer` maps each detected entity to a synthetic placeholder using MD5 hash seeds computed from `(entity_type, original_text.strip().lower())`.
   - Recurring entity names (e.g. `"Rashi Patil"` appearing 20 times) receive the exact same synthetic replacement across all occurrences to maintain document legibility and legal co-reference.
4. **Run-Level Text Substitution**:
   - `DOCXRedactor` groups entity replacements by physical OpenXML paragraph elements (`p._p`) to prevent corruption in merged table cells or linked headers.
   - Text substitution operates at the run level (`<w:r>`):
     - **Single-Run Match**: Replaces text inside `run.text` directly, preserving font size, color, bold, and italic attributes.
     - **Multi-Run Match**: Replaces the prefix in the starting run, clears intermediate runs (`run.text = ""`), and updates the trailing run text.
5. **CareEdge Research Bug Fix & Regression Test**:
   - An early investigation revealed a co-reference propagation flaw where repeated occurrences of `"CareEdge Research"` in Paragraph 114 were missed because text-based tracking checked text presence rather than span coverage.
   - The propagation logic was refactored to be span-aware (`test_careedge_leak_regression`), increasing detection from 2/3 to 3/3 occurrences and bringing CareEdge Research residual occurrences to `0`.

---

## 5. Ground-Truth / Annotation Methodology

The evaluation dataset was constructed using an automated candidate generation and policy-based review workflow (`evaluation/review_annotations.py`):

### Provenance Statistics
* **Total Workload Candidates**: `3,507`
* **Automated Provisional Reviewed**: `63`
* **Independent Human Reviewed**: `0`
* **Unreviewed Candidates**: `3,444`
* **Accepted Provisional Entities**: `15`
* **Rejected Provisional Candidates**: `48`
* **Corrected Provisional Spans**: `1` (`cand_59`)

> [!IMPORTANT]
> **Provenance Disclaimer**: Zero (0) candidates were independently reviewed by a human auditor. The 63 reviewed decisions were generated programmatically via automated policy-based simulation and constitute a **provisional automated annotation benchmark**. They must NOT be cited as human-verified or human-audited gold-standard ground truth.

---

## 6. Entity-Level Matching

Entity matching incorporates both entity metadata and document spatial coordinates to ensure precise span evaluation:

1. **Entity Type**: Candidate `entity_type` must match ground-truth `entity_type`.
2. **Spatial Coordinate Key**: The unique `SourceLocation` coordinate key must match exactly:
   $$\text{location\_key} = (\text{source\_type}, \text{table\_idx}, \text{row\_idx}, \text{cell\_idx}, \text{para\_idx}, \text{header\_idx}, \text{footer\_idx})$$
3. **Character Span**: Normalized character offsets `(start_offset, end_offset)` within the source text chunk must match.

### Why Coordinate Keys Are Required
In complex Word documents, identical text snippets (e.g. `"Auditor"`, `"Mumbai"`, `"Page 1"`) frequently recur in different table cells, headers, or paragraphs. Without spatial coordinate matching, a prediction in Table 0 Cell (1,2) could falsely match an entity in Table 5 Cell (3,4) purely due to matching character offsets, distorting precision and recall calculations.

---

## 7. TP / FP / FN Definitions

The evaluation partition incorporates four distinct candidate classes:

* **True Positive (TP)**: A pipeline prediction that matches an accepted provisional annotation in entity type, spatial coordinate key, and character span.
* **Known False Positive (FP)**: A pipeline prediction that matches a candidate explicitly marked as rejected in the reviewed annotation set (e.g. generic legal terms or statutory authority names).
* **Known False Negative (FN)**: An accepted provisional entity that the pipeline failed to detect at that specific location span.
* **Unassessed / Unknown**: Pipeline predictions occurring in unreviewed document regions (`3,444` unreviewed candidates, `5,712` unassessed predictions). These are tracked separately and are **NOT** counted as false positives because their ground-truth status is unverified.

---

## 8. Provisional Annotation-Agreement Metrics

The provisional annotation-agreement metrics evaluate agreement between pipeline predictions and the 63-candidate automated-reviewed subset:

### Verified Subset Partition Counts
- **True Positives (TP)**: `9`
- **Known False Positives (FP)**: `46`
- **Known False Negatives (FN)**: `6`

### Formulae & Verification
$$\text{Precision}_{\text{prov}} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{9}{9 + 46} = \frac{9}{55} \approx \mathbf{16.36\%}$$

$$\text{Recall}_{\text{prov}} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{9}{9 + 6} = \frac{9}{15} = \mathbf{60.00\%}$$

$$\text{F1}_{\text{prov}} = \frac{2 \times \text{TP}}{2 \times \text{TP} + \text{FP} + \text{FN}} = \frac{18}{18 + 46 + 6} = \frac{18}{70} \approx \mathbf{25.71\%}$$

| Metric | Provisional Benchmark Value | Evaluated Scope |
| :--- | :---: | :--- |
| **Precision** | **16.36%** | 63 automated-reviewed candidates only |
| **Recall** | **60.00%** | 63 automated-reviewed candidates only |
| **F1 Score** | **25.71%** | 63 automated-reviewed candidates only |

> [!WARNING]
> These metrics measure agreement with the current automated provisional annotation subset (63 candidates). They are NOT independently human-validated model performance metrics.

---

## 9. Accuracy

Entity-level accuracy is reported as **N/A**:

$$\text{Accuracy}_{\text{entity}} = \mathbf{\text{N/A}}$$

### Justification
Entity-level accuracy requires a well-defined, independently validated true-negative population (i.e. a complete, verified count of non-PII spans across the entire document). Because `3,444` of `3,507` candidates remain unassessed, no true-negative denominator can be established without fabricating data. Attempting to compute entity accuracy under these conditions would introduce arbitrary assumptions.

---

## 10. Final / Human-Validated Metrics

| Metric | Final Value | Reason |
| :--- | :---: | :--- |
| **Precision** | `N/A` | No candidates were independently human-reviewed |
| **Recall** | `N/A` | No candidates were independently human-reviewed |
| **F1 Score** | `N/A` | No candidates were independently human-reviewed |
| **Accuracy** | `N/A` | No candidates were independently human-reviewed |

Final independently validated metrics remain unavailable until a qualified human auditor conducts a complete line-by-line review of the document candidate workload.

---

## 11. Redaction Validation

Document-wide residual PII validation was conducted using the location-based validator (`scripts/residual_pii_checker.py`), searching the original and redacted `.docx` files across paragraphs, tables, headers, and footers:

### Summary Results
* **Provisional Annotation Slots Checked (source-chunk scope)**: `19`
* **Successfully Replaced (source-chunk scope)**: `19`
* **Residual Candidate Occurrences**: `0`
* **Actual Residual PII**: `0`
* **Provisional False Positives**: `0`

### Key Entity Leak Checks (Full-Document Scope)
- `"CareEdge Research"`: 7 original occurrences $\rightarrow$ 0 redacted occurrences (**0 residual**)
- `"Sarthak Malvadkar"`: 7 original occurrences $\rightarrow$ 0 redacted occurrences (**0 residual**)
- `"KSH INTERNATIONAL LIMITED"`: 10 original occurrences $\rightarrow$ 0 redacted occurrences (**0 residual**)
- `"cs.connect@kshinternational.com"`: 3 original occurrences $\rightarrow$ 0 redacted occurrences (**0 residual**)
- `"+ 91 20 4505 3237"`: 1 original occurrence $\rightarrow$ 0 redacted occurrence (**0 residual**)

> [!NOTE]
> **Validation Scope Note**: The "19 / 19 successfully replaced" figure represents the replacement of currently checked candidate occurrences in their source annotated chunks. It measures redaction replacement efficacy on checked candidates and must NOT be cited as "100% detector recall" across all possible unannotated PII in arbitrary documents.

---

## 12. Regression Testing

The automated test suite verifies pipeline stability and bug fixes:

- **Command**: `pytest -q`
- **Result**: **83 passed, 0 failed, 0 skipped**
- **Test Coverage**: Includes 18 test modules covering detector unit tests, OpenXML table extractor logic, run-level redactor behavior, pseudonymizer seeding, evaluation metrics, and regression tests (`test_careedge_leak_regression`, `test_regression_correctness.py`).

---

## 13. Limitations

1. **Provisional Ground Truth**: Ground truth was generated via policy simulation; 0 candidates were independently human-reviewed.
2. **Partial Workload Assessment**: Only 63 of 3,507 candidates (1.8%) have been assessed, leaving 3,444 unreviewed.
3. **Statistical NER Model Constraints**: `en_core_web_sm` is optimized for execution speed. Multi-word corporate legal titles in dense table cells may produce false positives or false negatives.
4. **Single-Document Benchmark**: Quantitative evaluation was performed on `Red Herring Prospectus.docx`; results should not be generalized as universal performance across arbitrary document domains.
5. **Public Repository Exclusion**: To prevent raw PII exposure, the original prospectus (`input/Red Herring Prospectus.docx`) and raw annotation datasets (`evaluation/ground_truth.json`, `ground_truth_verified.json`) are intentionally excluded from the public GitHub repository.

---

## 14. Conclusion

The **PII Redaction Tool** implementation has been fully constructed, tested, and validated:
- The 7-stage OpenXML redaction engine successfully detects PII across 9 supported categories and performs run-level text substitution.
- All 83 automated unit, integration, and regression tests pass cleanly (`83 passed`).
- Document-wide residual PII validation confirmed **0 actual residual PII** among checked candidate occurrences, successfully resolving the CareEdge Research co-reference propagation issue.
- Provisional annotation-agreement metrics against the 63-candidate reviewed subset are documented at **16.36% Precision**, **60.00% Recall**, and **25.71% F1**.
- Final independently validated benchmark metrics remain `N/A` because zero candidates were independently human-reviewed.
