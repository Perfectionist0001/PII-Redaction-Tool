# Final Redaction Validation

## Source Documents
* **Original** : `input\Red Herring Prospectus.docx`
* **Redacted** : `output\redacted_prospectus.docx`
* **GT Source**: `evaluation\ground_truth_verified.json`

---

## Summary

* **Total Candidate PII Occurrences Checked** : `19`
* **Successfully Replaced**                   : `19`
* **Residual Candidate Occurrences**          : `0`
* **Actual Residual PII**                     : `0`
* **Provisional False Positives**             : `0`

---

## Category Results

| Category | Original Candidate Occ. | Successfully Replaced | Residual Occ. | Status |
| :--- | :---: | :---: | :---: | :--- |
| **PERSON** | `1` | `1` | `0` | ✅ OK |
| **EMAIL** | `1` | `1` | `0` | ✅ OK |
| **PHONE** | `1` | `1` | `0` | ✅ OK |
| **ORGANIZATION** | `13` | `13` | `0` | ✅ OK |
| **ADDRESS** | `3` | `3` | `0` | ✅ OK |
| **SSN** | `0` | `0` | `0` | ✅ OK |
| **CREDIT_CARD** | `0` | `0` | `0` | ✅ OK |
| **DOB** | `0` | `0` | `0` | ✅ OK |
| **IP_ADDRESS** | `0` | `0` | `0` | ✅ OK |

---

## Repeated Entity Validation

Occurrence counts measured across the entire document (all paragraphs + tables + headers + footers).

| Label | Entity Text | Orig Count | Red Count | Replaced | Residual | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| ORGANIZATION (explicit) | `CareEdge Research` | `7` | `0` | `7` | `0` | ✅ OK |
| PERSON | `Sarthak Malvadkar` | `7` | `0` | `7` | `0` | ✅ OK |
| ORGANIZATION | `KSH INTERNATIONAL LIMITED` | `10` | `0` | `10` | `0` | ✅ OK |
| ORGANIZATION | `Bhandary Metal Extrusion Private Limited` | `3` | `0` | `3` | `0` | ✅ OK |
| ORGANIZATION | `KSH International Private Limited` | `3` | `0` | `3` | `0` | ✅ OK |
| ORGANIZATION | `Registrar of Companies Maharashtra` | `1` | `0` | `1` | `0` | ✅ OK |
| ORGANIZATION | `KSH International Limited` | `5` | `0` | `5` | `0` | ✅ OK |
| ORGANIZATION | `CARE Analytics and Advisory Private Limited` | `4` | `0` | `4` | `0` | ✅ OK |
| ORGANIZATION | `CareEdge Research` | `7` | `0` | `7` | `0` | ✅ OK |
| ADDRESS | `11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India;` | `1` | `0` | `1` | `0` | ✅ OK |
| ADDRESS | `201, Tower 2, Montreal Business Centre, Off Pallod Farms, Baner, Pune – 411 045, Maharashtra, India;` | `1` | `0` | `1` | `0` | ✅ OK |
| ADDRESS | `at 11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India and its Corporate Office at 201, Tower 2, Montreal Business Centre, Off Pallod Farms, Baner, Pune – 411 045, Maharashtra, India.` | `1` | `0` | `1` | `0` | ✅ OK |
| EMAIL | `cs.connect@kshinternational.com` | `3` | `0` | `3` | `0` | ✅ OK |
| PHONE | `+ 91 20 4505 3237` | `1` | `0` | `1` | `0` | ✅ OK |

---

## Residual Findings

**No actual residual PII found.**

---

## Conclusion

* **Total candidate PII occurrences checked** : `19`
* **Successfully replaced**                   : `19` (100.00%)
* **Residual candidate occurrences**          : `0`
* **Actual residual PII**                     : `0`
* **Provisional false positives (residual)**  : `0`

## **PASS — NO ACTUAL RESIDUAL PII FOUND**