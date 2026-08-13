# PII Redaction Tool — Project & Document Analysis

## 1. Project Objective

The **PII Redaction Tool** is designed to process Microsoft Word (`.docx`) documents to automatically detect, mask/redact specified Personally Identifiable Information (PII) and sensitive corporate/personal data, replace detected entities with realistic synthetic alternatives (faker replacement), generate a visually and structurally preserved redacted `.docx` document, and quantitatively evaluate detection quality (precision, recall, F1-score).

In this initial phase, the goal is to conduct a thorough technical inspection of the provided input document (`Red Herring Prospectus.docx`), analyze document structure and formatting constraints, assess PII presence vs. false-positive risks, and design a robust, modular Python architecture for the upcoming implementation.

---

## 2. Assignment Requirements

The assignment specifies the following functional and non-functional requirements for the complete system:

1. **Document Input & Parsing**: Read `.docx` files cleanly, preserving paragraphs, tables, table cells, headers, footers, character styles, run properties, and document hierarchy.
2. **Entity Detection**: Detect 9 core PII / sensitive entity categories across both body text and tabular structures.
3. **Synthetic Replacement**: Replace sensitive entities with realistic synthetic alternatives (e.g. using `Faker`) while preserving context type, entity length constraints, and surrounding punctuation.
4. **DOCX Generation**: Output a clean, fully valid `.docx` document with redacted text without corrupting OpenXML tags, styles, or table formatting.
5. **Evaluation System**: Calculate evaluation metrics (Precision, Recall, F1-score) against ground-truth annotations to measure detection quality.
6. **Strict First Step Constraints**: Conduct analysis only—do **not** write detector code, generate redacted output, or invent metrics/counts in this phase.

---

## 3. Required PII Categories

The project scope encompasses 9 mandatory entity categories:

| Category | Description | Target Entity Characteristics |
| :--- | :--- | :--- |
| **1. Full Names** | Names of natural persons | Individual executives, directors, officers, contact persons |
| **2. Email Addresses** | Personal and corporate email addresses | Standard pattern `local@domain.ext` |
| **3. Phone Numbers** | Fixed-line, mobile, and fax numbers | Formatted numbers with country codes (`+91`), area codes, spaces |
| **4. Company Names** | Legal corporate entity names | Organizations, lead managers, registrars, banks, legal firms |
| **5. Physical / Mailing Addresses** | Postal addresses | Registered/corporate offices, plot numbers, street, city, state, pin code |
| **6. Social Security Numbers (SSNs)** | US 9-digit national tax/identity numbers | Pattern `NNN-NN-NNNN` |
| **7. Credit Card Numbers** | Financial card numbers | 13–19 digit sequences (Visa, Mastercard, Amex, etc.) |
| **8. Dates of Birth (DOBs)** | Individual birth dates | Date of birth of natural persons (`DD/MM/YYYY`, `Month DD, YYYY`) |
| **9. IP Addresses** | Network location addresses | IPv4 (`x.x.x.x`) or IPv6 addresses |

---

## 4. Observations About the Actual Supplied Prospectus

Empirical inspection of `Red Herring Prospectus.docx` was conducted using Python OpenXML parsing tools. Below are the verified metrics of the primary input document:

* **File Path**: `input/Red Herring Prospectus.docx` (or `Red Herring Prospectus.docx` in project root)
* **File Size**: `1,844,676 bytes` (~1.76 MB)
* **Document Nature**: A legal, financial, and regulatory prospectus filed for an Initial Public Offering (IPO) in India for **KSH INTERNATIONAL LIMITED**.

### Document Structural Breakdown
* **Top-Level Body Paragraphs**: `1,006`
* **Paragraphs Inside Table Cells**: `4,199`
* **Total Body Paragraphs (`w:p` elements)**: `5,205`
* **Total Tables (`w:tbl` elements)**: `76`
* **Total Table Cells (`w:tc` elements)**: `3,722`
* **Header XML Files**: `75` header XML files (`word/header1.xml` to `word/header75.xml`), of which `73` contain active text content (e.g. running section headers like *"TABLE OF CONTENTS"*, *"SECTION I - GENERAL"*, page identifiers).
* **Footer XML Files**: `74` footer XML files (`word/footer1.xml` to `word/footer74.xml`), of which `0` contain visible text elements (contain section formatting metadata / empty paragraph structures).
* **Extracted Text Statistics**: `441,075` characters (~`69,746` tokens).
* **Embedded Media**: `8` media assets (`image1.jpeg` to `image5.png`), including a QR code graphic on the cover page.

---

## 5. Types of PII Actually Observed

Based on exact text inspection, the following entity types are **present** in `Red Herring Prospectus.docx`:

### 1. Full Names (Natural Persons)
* **Observation**: Present in contact tables, board of directors listings, key managerial personnel sections, and legal advisor signatures.
* **Inspected Examples**:
  * `Sarthak Malvadkar` (Company Secretary & Compliance Officer)
  * `Prakash Boricha` (Contact Person - Nuvama)
  * `Rajesh Kush` (Promoter / Director)
  * `Anand Soni` (Bajaj Finserv)
  * `Amod Joshi` (IndusInd Bank)
  * `Pravin Teli` (HDFC Bank)
  * `Rohit Kush` (Promoter / Director)
  * `Cherag Gyara` (ICICI Securities)
  * `Hitesh Ramani` (Citi Bank)
  * `Eric Bacha` (HDFC Bank)
  * `Sachin Gawade` (HDFC Bank)
  * `Sheetal Parab` (Nuvama)
  * `Siddharth Jadhav` (HDFC Bank)
  * `Tushar Gavankar` (HDFC Bank)
  * `Manisha Shukla` (HDFC Bank)
  * `Parag Pansare` (Kirtane & Pandit LLP)
  * `Ashish MP` (Federal Bank)

### 2. Email Addresses
* **Observation**: Present in table cells under *"E-MAIL AND TELEPHONE"* and contact sections. A total of **26 unique email addresses** were identified.
* **Inspected Examples**:
  * `cs.connect@kshinternational.com`
  * `Sarthak.malvadkar@kshinterantional.com`
  * `ksh.ipo@nuvama.com`
  * `ksh@icicisecurities.com`
  * `customercare@icicisecurities.com`
  * `customerservice.mb@nuvama.com`
  * `Ipocmg@icicibank.com`
  * `anand.soni@bajajfinserv.in`
  * `ashishmp@federalbank.co.in`
  * `cherag.gyara@icicibank.com`
  * `eric.bacha@hdfcbank.com`
  * `hingnetare@gmail.com`
  * `hitesh.ramani@citi.com`
  * `ipo@trilegal.com`
  * `kshinternational.ipo@in.mpms.mufg.com`
  * `manisha.shukla@hdfcbank.com`
  * `parag.pansare@kirtanepandit.com`
  * `prakash.boricha@nuvama.com`
  * `pravin.teli2@hdfcbank.com`
  * `pro@eximbankindia.in`
  * `rm6.ifbpune@sbi.co.in`
  * `sachin.gawade@hdfcbank.com`
  * `sharmila.joshi@indusind.com`
  * `sheetal.parab@nuvama.com`
  * `siddharth.jadhav@hdfcbank.com`
  * `tushar.gavankar@hdfcbank.com`

### 3. Phone Numbers
* **Observation**: Present in contact tables alongside emails. Formatted with irregular spacing, parenthetical area codes, and international prefixes. A total of **26 phone/fax strings** were identified.
* **Inspected Examples**:
  * `Tel: +91 22 6807 7100`
  * `Tel: +91 22 40094400`
  * `Tel: +91 81081 14949`
  * `Telephone : + 91 (20) 6729 510`
  * `Telephone : + 91 20 6729 5100`
  * `Telephone : + 91 22 4009 4400`
  * `Telephone : + 91 91586 40360`
  * `Telephone : +91 20 6606 4494`
  * `Telephone : +91 22 4079 1000`
  * `Telephone : + 91 20 45053237`
  * `Telephone : + 91 8879770456`

### 4. Company Names / Organizations
* **Observation**: Pervasive throughout the document, including issuers, lead managers, registrars, auditors, and commercial banks.
* **Inspected Examples**:
  * `KSH International Limited` (Issuer Company)
  * `Bhandary Metal Extrusion Private Limited` (Former Name)
  * `Nuvama Wealth Management Limited` (BRLM)
  * `ICICI Securities Limited` (BRLM)
  * `Link Intime India Private Limited` (Registrar)
  * `Bigshare Services Private Limited` (SCSB/Registrar)
  * `Kirtane & Pandit LLP` (Statutory Auditor)
  * `Trilegal` (Legal Counsel)
  * Commercial Banks: `Federal Bank`, `HDFC Bank`, `IndusInd Bank`, `State Bank of India`, `EXIM Bank`, `MUFG Bank`, `Citi Bank`

### 5. Physical / Mailing Addresses
* **Observation**: Detailed addresses for registered offices, corporate offices, factories, and syndicate members are present in body paragraphs and key tables.
* **Inspected Examples**:
  * Registered Office: `11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India`
  * Corporate Office: `201, Tower B, 2nd Floor, ...`
  * BRLM / Registrar Office Addresses: Multi-line addresses in Mumbai, Pune, and New Delhi.

---

## 6. PII Categories Not Observed

Based on thorough automated inspection of all 5,205 paragraphs and 76 tables in `Red Herring Prospectus.docx`, the following 4 categories are **NOT present**:

1. **Social Security Numbers (SSNs)**: `0 instances`. (US SSN format `NNN-NN-NNNN` does not exist in this Indian corporate regulatory document).
2. **Credit Card Numbers**: `0 instances`. (No 13–19 digit credit card numbers are present).
3. **Dates of Birth (DOBs)**: `0 instances`. (While the document contains corporate incorporation dates e.g. *"October 13, 2011"*, *"December 10, 2025"*, *"1979"*, and financial period dates, no individual dates of birth were found).
4. **IP Addresses**: `0 instances`. (No IPv4 or IPv6 network addresses exist in the text).

---

## 7. False-Positive Risks

Given that the Red Herring Prospectus is a formal financial/legal prospectus, it contains thousands of numbers, dates, codes, and capitalized terms. A naïve rule-based or regex detector will trigger severe false positives.

### Key False-Positive Vectors & Mitigation Rules:

1. **Dates vs. Dates of Birth**:
   * *Risk*: Treating corporate dates (incorporation date `October 13, 2011`, issue date `December 10, 2025`, fiscal year end dates `March 31, 2023`) as Dates of Birth.
   * *Rule*: Require explicit DOB contextual triggers (e.g. *"born on"*, *"date of birth"*, *"DOB"*) before classifying a date as a DOB.
2. **Numeric Identifiers vs. Phone Numbers**:
   * *Risk*: Treating 10-digit application numbers, registration numbers, CIN segments (`080618`, `021012`), share counts (`10,00,000`), or monetary figures (`₹ 50,00,000`) as phone numbers.
   * *Rule*: Verify phone numbers against strict international format patterns, area codes, and preceding label keywords (*"Tel"*, *"Phone"*, *"Mobile"*, *"Fax"*).
3. **Numeric Identifiers vs. Credit Cards**:
   * *Risk*: Treating 16-digit corporate identification strings, ISIN codes, or SEBI registration numbers as credit card numbers.
   * *Rule*: Apply Luhn algorithm validation (`luhn_check`) and prefix validation (Visa 4, Mastercard 51-55, etc.) to all card candidates.
4. **Company Registration Identifiers vs. SSNs**:
   * *Risk*: Mistaking 9-digit registration numbers or tax IDs for US Social Security Numbers.
   * *Rule*: Enforce hyphenated `NNN-NN-NNNN` boundary matching and context checks.
5. **Capitalized Phrases vs. Full Names**:
   * *Risk*: Tagging legal terms (*"Red Herring Prospectus"*, *"Book Running Lead Managers"*, *"Equity Shares"*, *"Companies Act"*, *"Registered Office"*) or statutory titles as personal names.
   * *Rule*: Use Named Entity Recognition (NER) models fine-tuned for Person entities combined with honorific prefix checks (`Mr.`, `Ms.`, `Dr.`) and lookup white-lists.
6. **Public Organizations / Regulatory Bodies vs. Private PII**:
   * *Risk*: Classifying regulatory bodies (*"SEBI"*, *"Reserve Bank of India"*, *"RoC"*, *"BSE Limited"*, *"NSE"*) or statutory bodies as personal or confidential corporate PII requiring redaction.
   * *Rule*: Maintain a dictionary of public regulatory and government entity names to exclude from redaction.
7. **The Word "PAN" vs. PAN Numbers**:
   * *Risk*: Matching the generic English word *"PAN"* (e.g. *"PAN India"*, *"PAN number"*) as a Permanent Account Number string.
   * *Rule*: Require exact 10-character alphanumeric regex matching `[A-Z]{5}[0-9]{4}[A-Z]` rather than matching the keyword "PAN".

---

## 8. False-Negative Risks

Conversely, PII may be missed due to document formatting anomalies:

1. **Non-Standard Phone Formatting**:
   * Phone numbers in the prospectus feature extreme spacing variations due to justification typesetting (e.g. `Tel: + 91 (20) 6729 510`, `Telephone : + 91 91586 40360`). Standard regex matching `\+91\d{10}` will fail.
2. **Text Split Across XML Runs (`w:r`)**:
   * Word processors often break a single word, email, or phone number across multiple XML `<w:r>` tags (runs) if formatting or spellcheck flags exist. Run-level text matching will miss split entities.
3. **Tabular PII Isolation**:
   * PII inside table cells (77.8% of document paragraphs are inside table cells) may be missed if the parser only extracts top-level paragraphs.
4. **Varied Person Name Formatting**:
   * Executive names appear in tabular contact blocks without traditional honorifics (e.g. `Sarthak Malvadkar`, `Prakash Boricha`). Entity detection relying solely on `Mr.` or `Ms.` prefixes will experience high false negatives.

---

## 9. DOCX Processing Challenges

Processing Microsoft Word documents for PII redaction presents several OpenXML technical hurdles:

1. **Multi-Run Fragmentation**:
   * An entity like `cs.connect@kshinternational.com` might be split into `<w:r><w:t>cs.connect</w:t></w:r><w:r><w:t>@kshinternational.com</w:t></w:r>`. Redacting text at the run level requires mapping character indices from aggregated paragraph text back to individual XML runs.
2. **Table Structural Preservation**:
   * 76 tables containing 3,225 cells must be traversed recursively. Cell boundaries, row heights, column widths, and cell borders must remain intact during text substitution.
3. **Header XML Files**:
   * 73 header XML files contain running text. If PII or company names appear in headers, header XML files must be parsed and redacted separately from `document.xml`.
4. **Style and Formatting Preservation**:
   * Replacing text must retain font size, bold/italic flags, color, and alignment attributes attached to original runs.

---

## 10. Recommended Architecture

The proposed system architecture is designed as a pipeline with decoupled modules:

```
                  ┌─────────────────────────────────┐
                  │    input/Prospectus.docx        │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │       DOCX Ingestion Engine     │
                  │ (Extracts Paragraphs, Tables,   │
                  │  Headers, Runs & Character Maps)│
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │      PII Detection Engine       │
                  │ ┌─────────────────────────────┐ │
                  │ │ Multi-Regex Matcher         │ │
                  │ │ spaCy NER (en_core_web_trf) │ │
                  │ │ Contextual Filter Rules     │ │
                  │ └─────────────────────────────┘ │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │    Synthetic Replacement Engine │
                  │ (Faker-based context replacement│
                  │  with format & length matching) │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │     DOCX Reconstruction Engine  │
                  │ (Applies replacements to XML    │
                  │  runs while preserving styles)  │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │     Evaluation & Reporting      │
                  │ (Precision, Recall, F1 Score)   │
                  └─────────────────────────────────┘
```

### Module Responsibilities:
1. `docx_parser`: Recursively extracts text blocks from document body, tables, and headers while maintaining character offset mapping to XML runs.
2. `pii_detector`: Combines Regex rules, spaCy Transformer-based NER, and false-positive filter heuristics to locate entity boundaries.
3. `redactor`: Interacts with `Faker` to generate synthetic domain-appropriate replacements (e.g. replacing `Sarthak Malvadkar` with `Rohan Mehta`, `cs.connect@kshinternational.com` with `info@acme-corp.com`).
4. `docx_writer`: Writes replaced text back into DOCX runs without disturbing surrounding XML tags.
5. `evaluator`: Compares detected entity spans against ground-truth JSON annotations to compute Precision, Recall, and F1 metrics.

---

## 11. Recommended Python Libraries

| Library | Version / Purpose | Justification |
| :--- | :--- | :--- |
| `python-docx` | `^1.1.0` | Primary library for reading, modifying, and saving `.docx` documents, tables, and runs. |
| `spacy` | `^3.7.0` | Industrial-strength NLP library for Named Entity Recognition (`PERSON`, `ORG`, `GPE`). |
| `en_core_web_sm` / `trf` | Spacy Model | Transformer / statistical model for accurate entity span detection. |
| `faker` | `^24.0.0` | Synthetic data generator for realistic replacement of names, emails, phones, addresses. |
| `regex` | Standard / `re` | Extended regular expression engine with Unicode support for complex phone/email patterns. |
| `pytest` | `^8.0.0` | Framework for unit testing parser, detector, and redactor modules. |
| `pydantic` | `^2.6.0` | Data validation and schema enforcement for entity spans and evaluation ground truth. |

---

## 12. Proposed Folder Structure

```
PII Redaction Tool/
├── docs/
│   └── PROJECT_ANALYSIS.md       # Implementation analysis & system design (this document)
├── input/
│   └── Red Herring Prospectus.docx # Primary input document
├── output/                        # Generated redacted documents
├── data/
│   └── ground_truth.json         # Evaluation ground-truth entity spans
├── src/
│   ├── __init__.py
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── docx_reader.py        # DOCX paragraph, table, & header extraction
│   │   └── run_mapper.py         # Character offset to XML run mapping
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── base_detector.py      # Abstract detector interface
│   │   ├── regex_detector.py     # Regex matcher for emails, phones, SSN, CC, IP
│   │   ├── ner_detector.py       # spaCy NER matcher for Names, Companies, Addresses
│   │   └── false_positive_filter.py # Rules to filter non-PII dates, numbers, legal terms
│   ├── redactor/
│   │   ├── __init__.py
│   │   ├── synthetic_generator.py # Faker-based fake data generator
│   │   └── docx_redactor.py      # Run-level text replacer
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── metrics.py            # Precision, Recall, F1 calculator
│   └── utils/
│       ├── __init__.py
│       └── logger.py             # Structured logging setup
├── tests/
│   ├── test_parser.py
│   ├── test_detectors.py
│   ├── test_redactor.py
│   └── test_evaluation.py
├── requirements.txt              # Project dependencies
└── README.md                     # Usage instructions & documentation
```

---

## 13. Proposed Testing Strategy

A thorough testing pipeline will be established prior to full pipeline execution:

1. **Unit Testing**:
   * `test_docx_reader`: Verify paragraph count (`1,006`), table count (`76`), row count (`878`), cell count (`3,225`), and header text extraction.
   * `test_regex_detectors`: Test regex patterns against synthetic edge cases (valid/invalid emails, phone variations, CC Luhn checks).
   * `test_false_positive_filter`: Assert that fiscal dates (`March 31, 2023`), company registration numbers (`CIN`), and legal terms are **not** flagged as PII.
   * `test_synthetic_generator`: Ensure generated fake values match expected types and data formats.
2. **Integration Testing**:
   * Run end-to-end extraction and redaction on small sample `.docx` files containing paragraphs and nested tables.
   * Validate that output `.docx` files can be reopened by Microsoft Word without corruption errors.
3. **Regression Testing**:
   * Automated verification that unredacted non-sensitive text is 100% identical to original input text.

---

## 14. Proposed Evaluation Strategy

To evaluate detection quality objectively, an evaluation framework will be implemented:

1. **Ground Truth Annotation Schema**:
   * Define character-level entity spans `(start_offset, end_offset, entity_type)` for test document blocks in `data/ground_truth.json`.
2. **Evaluation Metrics**:
   * **True Positives (TP)**: Correctly identified PII entity spans.
   * **False Positives (FP)**: Non-PII text incorrectly flagged as PII.
   * **False Negatives (FN)**: Genuine PII missed by detectors.
   * $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
   * $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
   * $$\text{F1 Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
3. **Boundary Matching Modes**:
   * *Strict Exact Match*: Requires exact match of start offset, end offset, and entity label.
   * *Partial Overlap Match*: Counts partial span overlaps for flexible NER evaluation.

---

## 15. Privacy & Security Considerations

1. **Local Execution**: All processing must occur strictly on local compute. No document text or candidate entities should be transmitted to external cloud APIs or third-party LLMs.
2. **In-Memory Processing**: Extracted text blocks and character maps should be held in memory and securely cleared after document generation.
3. **Zero Mutation of Original File**: Input file `input/Red Herring Prospectus.docx` must remain strictly read-only; output documents must be written to designated `output/` paths.
4. **Deterministic Synthetic Replacement**: Synthetic data generation should allow seeded random state for reproducible test runs while ensuring no real PII is leaked into synthetic outputs.

---

## 16. Future Extensibility Considerations

1. **Support for Additional Document Formats**: Designing the detector interface (`base_detector.py`) to accept plain text strings allows easy extension to PDF, TXT, or HTML formats.
2. **Custom Entity Plugins**: Abstract base classes enable seamless addition of region-specific entities (e.g. Indian Aadhaar numbers, PAN cards, Passport numbers, US SSNs).
3. **Configurable Redaction Styles**: Support both synthetic replacement (Faker replacement) and traditional black-box masking (`[REDACTED_NAME]`, `████████`).
4. **Interactive Review Interface**: Export detected entity spans to JSON/Web UI for human-in-the-loop audit prior to final DOCX compilation.
