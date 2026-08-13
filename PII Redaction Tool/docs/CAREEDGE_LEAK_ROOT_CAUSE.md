# CareEdge Research Residual Leak Root Cause

This report details the root-cause analysis of the residual PII leak of `"CareEdge Research"` in paragraph 114 of the redacted prospectus document.

---

## 1. Confirmed Facts

- **Entity Text**: `"CareEdge Research"`
- **Category**: `ORGANIZATION`
- **Source Location**: Paragraph index `114`
- **Total Occurrences in Original Text**: `3`
  - Occurrence 1: Character span `[304:321]`
  - Occurrence 2: Character span `[700:717]`
  - Occurrence 3: Character span `[855:872]`
- **Redaction Outcome**:
  - Occurrence 2 and Occurrence 3 were successfully replaced with synthetic pseudonym placeholders (e.g., `"Scott Group"` / `"Vargas-Bowman"`).
  - Occurrence 1 remained unchanged in the output document, resulting in a single residual PII leak.

---

## 2. Original DOCX Structure

Paragraph 114 contains 105 runs in the original document:
- **Run 10**: `'CareEdge Research'` (bold=True, italic=None) representing Occurrence 1. It is enclosed in parentheses and curly quotes: `(“CareEdge Research”)`.
- **Run 18**: `". Further, CareEdge Research, pursuant to their consent letter..."` containing Occurrence 2.
- **Run 30**: `'CareEdge'` and **Run 32**: `'Research,'` split across two runs containing Occurrence 3.

Because Occurrence 1 is isolated in its own run (`Run 10`), it is a clean text run and was not split.

---

## 3. Detection Stage

During candidate generation and detection:
- The statistical spaCy model (`NERDetector`) successfully detected:
  - Occurrence 2: `CareEdge Research` at `[700:717]` (Candidate `cand_62`)
  - Occurrence 3: `CareEdge Research` at `[855:872]` (Candidate `cand_64`)
- It **failed** to detect Occurrence 1 (span `[304:321]`) in the initial NER pass. This was likely due to the surrounding syntactic structure/parentheses `(“CareEdge Research”)` which interfered with the statistical model's boundary decisions.

---

## 4. Entity Aggregation Stage

Inside `DetectionPipeline.process_chunks` (in `src/detection_pipeline.py`):
1. **Pass 1**: The pipeline collected the two initial detections for `"CareEdge Research"` in paragraph 114 (at spans `[700:717]` and `[855:872]`).
2. **Pass 2**: `"CareEdge Research"` qualified as a high-confidence entity and was added to the document-wide `known_entity_map`.
3. **Pass 3 (Co-reference Propagation)**: The pipeline iterated over chunks to propagate the known entities. For paragraph 114, it evaluated:
   ```python
   for entity_text, (etype, conf, det) in known_entity_map.items():
       if entity_text in chunk.text and entity_text not in existing_texts:
   ```
   Since `"CareEdge Research"` was already in `existing_texts` (due to Occurrences 2 and 3 being detected in Pass 1), the check `entity_text not in existing_texts` evaluated to `False`.
   As a result, propagation was **bypassed** for paragraph 114, and the pipeline did not run `re.finditer` to locate the missing Occurrence 1.

---

## 5. Redaction Planning Stage

Because Occurrence 1 was never detected as a `PIIEntity` object in the finalized entity list, it never received a synthetic replacement mapping. Only Occurrences 2 and 3 were assigned placeholders.

---

## 6. DOCX Mutation Stage

`DOCXRedactor` successfully matched the entities to their paragraph coordinates and replaced them. Since Occurrence 1 was absent from the entity list, it was skipped and remained unmodified.

---

## 7. Exact Root Cause

The root cause is a flaw in the document-wide co-reference propagation condition in [**`src/detection_pipeline.py`**](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS%20(1)/PII%20Redaction%20Tool/src/detection_pipeline.py) (line 263):
```python
if entity_text in chunk.text and entity_text not in existing_texts:
```
This condition assumes that if a string is detected once in a paragraph, all occurrences of that string in the paragraph must have been successfully detected. When statistical NER detects some occurrences in a paragraph but misses others, this check blocks propagation, preventing the system from identifying and redacting the remaining instances.

---

## 8. Recommended Minimal Fix

To resolve this issue, the co-reference propagation logic should be modified to scan the text chunk even if the string exists in `existing_texts`, provided we only add a new propagated entity if its specific span `(start, end)` does not overlap with any existing detections in that chunk.

### Proposed Code Diff
```diff
-            for entity_text, (etype, conf, det) in known_entity_map.items():
-                if entity_text in chunk.text and entity_text not in existing_texts:
+            for entity_text, (etype, conf, det) in known_entity_map.items():
+                if entity_text in chunk.text:
+                    # Check if there is any occurrence of entity_text in this chunk that is NOT covered
+                    # by existing detections.
```
Then, during `re.finditer(pattern, chunk.text)` iteration, we check if the candidate span `(start, end)` overlaps with any entity in `chunk_ents`. If it does not overlap, we append the new `propagated_ent` to the chunk's entity list.

---

## 9. Fix Implemented

### What Changed
The co-reference propagation phase in `DetectionPipeline.process_chunks` (in [**`src/detection_pipeline.py`**](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/src/detection_pipeline.py)) was rewritten to use span-aware propagation rather than checking `entity_text not in existing_texts`.
Specifically:
1. `existing_spans` is computed as a set of exact character spans `(e.start, e.end)` already detected for the chunk.
2. For every known high-confidence entity text, we check if it is present in the chunk.
3. If it is present, `re.finditer` is run to locate all occurrences within the chunk.
4. Each occurrence is processed: if its start/end span does not match an existing detection in `existing_spans`, a new `PIIEntity` is generated and added to the chunk's detections.
5. The pipeline's standard overlap/conflict resolution is then run to resolve boundaries and deduplicate.

### Why it Fixes the Bug
This fixes the bug by removing the faulty assumption that if a text string is already present in `existing_texts`, all occurrences of that text have been captured. Under the new logic, the pipeline correctly scans the entire chunk and recovers any occurrences of the name that were missed by initial detectors.

### Regression Test Added
A new regression test `test_careedge_leak_regression` was added to [**`tests/test_regressions.py`**](file:///D:/SCALER%20AI%20LABS%20ASSIGNMENTS/PII%20Redaction%20Tool/tests/test_regressions.py). It:
1. Simulates a paragraph containing three identical occurrences of `"CareEdge Research"`.
2. Emulates the statistical NER model detecting only occurrences 2 and 3, and missing occurrence 1.
3. Asserts that co-reference propagation successfully recovers occurrence 1, raising the overall occurrence count to `3` without generating any duplicate spans.

This regression test fails under the previous implementation and passes successfully under the new implementation.

### Validation Result
After regenerating the redacted document using the updated logic, the final redaction validation was run:
- **CareEdge Research Occurrences Detected**: `3`
- **CareEdge Research Occurrences Replaced**: `3`
- **CareEdge Research Residual Occurrences**: `0` (100% redacted, no leaks remain).
- **All tests passed**: `83 passed` (including the new regression test).

