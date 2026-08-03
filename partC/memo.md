# Part C — Decision Memo: Making Indic Assistant Replies Conversational

## Recommendation

Choose **path (a): LoRA SFT on synthetic formal→casual response pairs**, with prompt-only as the fallback. This is a style/register problem more than a knowledge problem, so baking the style into the main model is better than serving a second rewriter or maintaining six fragile prompts.

## Assumptions

- The base model already answers reasonably; the failure is that replies sound too formal/textbook.
- Synthetic rewrites are acceptable for style learning if Hindi/Kannada reviewer checks prevent obvious unnatural data.
- Reviewer coverage is only Hindi/Kannada, so other Indic languages need automated checks plus small spot checks if possible.

## Back-of-envelope arithmetic

- **Data:** Generate 2,000 pairs/language × 6 languages = **12,000 pairs**. At ~200 tokens/pair, that is **2.4M training tokens**.
- **Reviewer budget:** 10 h/week × 3 weeks = **30 h**. At ~100 binary reviews/hour, reviewer capacity is **3,000 judgments**. Use 600 for synthetic-data quality gate, 1,200 for held-out Hindi/Kannada evals across iterations, and keep 1,200 for edge cases/regression checks.
- **Training:** 2.4M tokens / 4096 ≈ **586 packed sequences/epoch**. A 4B model with LoRA rank 32 on one A100-80GB should finish several epochs comfortably within the 2-week GPU window, leaving time for one or two data/model iterations.
- **Serving cost:** SFT adds no second model at inference. A ≤1B rewriter would add latency, infrastructure, and another source of errors after every main-model response.

## Success metric with numeric threshold

On a held-out set of 200 Hindi and 200 Kannada prompts, require **≥70%** of responses to be rated natural/conversational by the reviewer, with **≤2% absolute regression** on a small factuality/safety checklist. For languages without reviewer coverage, use a formality classifier as a weak proxy and inspect examples manually before launch.

## Kill criterion

By **end of Day 7**, if Hindi has not reached **50% conversational** on 200 reviewed outputs after one SFT iteration, stop investing in SFT and pivot to path (c), prompt-engineering. If the highest-resource reviewed language does not move quickly, the synthetic-data pipeline is probably not teaching the intended register.

## First experiment on Day 1

Write 10 reviewer-approved Hindi formal→casual examples, prompt the base model to rewrite 100 formal Hindi responses, and have the reviewer rate them. If **≥40%** are acceptable, proceed with synthetic data generation; if **<20%**, redesign the data source/prompt before training.

## Why not the other paths

- **Path (b), ≤1B rewriter:** adds serving cost and latency, and a small model is likely weak across six Indic languages.
- **Path (c), prompt-only:** fastest fallback, but consumes context, is injection-prone, and is harder to keep consistent across languages.
