# AI Usage Disclosure

This document records how AI tools were used during the completion of this assignment.

## Tools Used

- **Gemini (Antigravity IDE):** Used as a coding assistant for:
  - Exploring and understanding the starter kit files
  - Drafting an implementation plan and identifying bugs in `fertility.py`
  - Writing and debugging Python scripts (`fertility_corrected.py`, corpus download)
  - Performing arithmetic verification for Part B calculations
  - Drafting memos and analysis documents

## What AI Did vs What I Did

| Task | AI Contribution | My Contribution |
|------|----------------|-----------------|
| Bug identification in fertility.py | Helped identify potential issues by reading code | I verified each claim by running experiments and measuring impact |
| FLORES-200 corpus setup | Suggested FLORES-200 as a source, wrote download script | I chose the languages and validated the data |
| KV-cache math (B1) | Verified arithmetic | I set up the formula and cross-checked against bench_log |
| Throughput analysis (B2-B3) | Helped structure the analysis | I identified the anomaly patterns in the CSV and derived goodput |
| Decision memo (Part C) | Helped draft structure | I made the architectural decision and wrote the reasoning |
| Code corrections | Generated corrected fertility script | I designed the fixes and verified outputs |

## Integrity Statement

All claims in the submission have been verified through actual code execution and data analysis. No evidence has been fabricated. Where AI suggested a bug or finding, I independently validated it before including it.
