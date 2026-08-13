# Ground Truth Verification Report

This document provides a final programmatic verification checklist for the verified ground truth annotation dataset.

## 1. Workload Verification Stats

- **Total Candidates in Workload**: `3507`
- **Number of Reviewed Candidates**: `13`
- **Number of Unreviewed Candidates**: `3494`
- **Number of Accepted Entities**: `7`
- **Number of Rejected Candidates**: `6`
- **Number of Modified Entities**: `0`
- **Number of Corrected Entities**: `0`
- **Number of Manually Added Entities**: `0`

## 2. Integrity Verification Check

| Check | Status | Description |
| :--- | :---: | :--- |
| Every candidate has a decision | **PARTIAL** | 13 reviewed, 3494 remaining unreviewed |
| No candidate remains silently unreviewed | **PASS** | Verified sum matches total workload candidate count |
| Accepted entities have human-review status | **PASS** | All accepted entities contain a non-empty `review_status` |
| Rejected candidates are excluded | **PASS** | Overlap check confirmed 0 candidate IDs are in both lists |
| Modified types recorded correctly | **PASS** | Checked `0` modifications in schema |
| Corrected spans recorded correctly | **PASS** | Checked `0` corrected spans in schema |
| Manually added entities have source locations | **PASS** | Verified all manual additions contain valid paragraph/table coordinates |
| No duplicate entity identities created | **PASS** | Checked distinct start/end span coordinates; detected `0` duplicates |
| Marking logic check | **PASS** | File correctly marked: `PARTIALLY HUMAN REVIEWED` (Provisional: `True`) |

## 3. Ground Truth Final Status

> [!WARNING]
> **Ground truth remains provisional.** Only a subset of the candidate annotations has been human-reviewed. Final pipeline evaluation metrics must be explicitly labeled as provisional benchmarks.