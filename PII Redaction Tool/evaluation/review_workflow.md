# Ground Truth Review Workflow

## Purpose

This document establishes the honest distinction between:

1. **Candidate Annotations** — automated detector outputs, filtered by heuristic rules.
2. **Human-Reviewed Ground Truth** — annotations that a human reviewer has individually accepted, rejected, reclassified, or corrected.

> [!IMPORTANT]
> The current `evaluation/ground_truth.json` contains **PROVISIONAL CANDIDATE ANNOTATIONS** — NOT human-reviewed ground truth. All metrics computed against this file are provisional self-consistency measurements.

---

## Current State

| File | Status | Description |
| :--- | :---: | :--- |
| `evaluation/candidate_annotations.json` | Automated | Raw detector output with surrounding context |
| `evaluation/ground_truth.json` | **Provisional** | Filtered candidates via `apply_provisional_rules()` — NOT human reviewed |
| `evaluation/ground_truth_verified.json` | Does not exist yet | Will contain genuine human-reviewed ground truth |

---

## How to Produce Genuine Ground Truth

### Step 1: Generate Candidate Annotations

```bash
python -m src.evaluation.candidate_generator
```

This runs all 8 detectors on the input DOCX and writes:
- `evaluation/candidate_annotations.json` (structured)
- `evaluation/candidate_annotations.md` (human-readable audit checklist)

### Step 2: Interactive Human Review

```bash
python evaluation/review_annotations.py --interactive --candidates evaluation/candidate_annotations.json --output evaluation/ground_truth_verified.json
```

The interactive CLI presents each candidate entity and allows:
- **[a]ccept** — Mark as genuine PII (sets `review_status: human_verified`)
- **[r]eject** — Mark as false positive with a reason
- **[s]kip** — Leave unreviewed (excluded from ground truth)

### Step 3: Provisional Rules (Non-Interactive Fallback)

If interactive review is not feasible:

```bash
python evaluation/review_annotations.py --provisional-rules --candidates evaluation/candidate_annotations.json --output evaluation/ground_truth.json
```

This applies GROUND_TRUTH_GUIDE.md filtering rules automatically. The output is clearly marked:
- `is_provisional_candidate: true`
- `review_status_summary: "PROVISIONAL CANDIDATE ANNOTATIONS (Requires line-by-line human review)"`
- Each entity has `review_status: "provisional_candidate"`

### Step 4: Run Evaluation

```bash
python -m src.evaluation.evaluate
```

If `ground_truth_verified.json` exists, prefer it. Otherwise the evaluation will run against the provisional file and the report will carry a **PROVISIONAL EVALUATION** warning banner.

---

## Rules Applied by `apply_provisional_rules()`

These automated rules from `docs/GROUND_TRUTH_GUIDE.md` are applied during provisional generation:

1. Public regulatory bodies (SEBI, RBI, BSE, NSE, etc.) → **Rejected**
2. Low-confidence SSN/CREDIT_CARD/DOB/IP_ADDRESS candidates (<0.90) → **Rejected**
3. EMAIL, PHONE, ADDRESS, PERSON, ORGANIZATION candidates → **Accepted as provisional**
4. All other entity types → **Rejected**

> [!WARNING]
> These rules are NOT equivalent to human review. They reduce obvious false positives but cannot:
> - Detect missed entities (false negatives)
> - Correct misclassified entity types
> - Fix incorrect text span boundaries
> - Evaluate contextual appropriateness

---

## File Schema

Both `ground_truth.json` and `ground_truth_verified.json` follow this schema:

```json
{
  "document_name": "Red Herring Prospectus.docx",
  "schema_version": "1.1",
  "is_provisional_candidate": true | false,
  "review_status_summary": "PROVISIONAL CANDIDATE ANNOTATIONS ..." | "HUMAN VERIFIED GROUND TRUTH",
  "total_ground_truth_entities": <int>,
  "summary_by_category": { "PERSON": <int>, "EMAIL": <int>, ... },
  "annotated_entities": [
    {
      "entity_id": "gt_1",
      "entity_type": "PERSON",
      "text": "Sarthak Malvadkar",
      "start": 16,
      "end": 33,
      "source_location": {
        "source_type": "paragraph",
        "paragraph_index": 28,
        "table_index": null,
        "row_index": null,
        "cell_index": null,
        "header_index": null,
        "footer_index": null
      },
      "review_status": "human_verified" | "provisional_candidate" | "human_modified_type" | "human_corrected_span" | "human_added_manually",
      "detector_source": "spaCy_NER",
      "auditor_notes": "..."
    }
  ]
}
```

---

## Key Integrity Rules

1. **Never call provisional annotations "verified"** — the `is_provisional_candidate` flag and each entity's `review_status` must honestly reflect whether a human reviewed it.
2. **Do not fabricate metrics** — evaluation reports based on provisional annotations must carry the PROVISIONAL warning.
3. **100% recall is not meaningful** against provisional ground truth — it just means the pipeline is consistent with its own filtered output.
