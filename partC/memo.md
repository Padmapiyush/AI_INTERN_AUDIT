# Part C — Decision Memo: Making Indic Assistant Replies Conversational

## Recommendation: Path (a) — SFT on Synthetic "Casualized" Response Pairs

---

## Assumptions

1. **Style ≠ knowledge.** Casualizing text is a surface-level style transfer task, not a factual accuracy problem. The base model already "knows" the right answers; it just outputs them in formal/textbook register.
2. **Synthetic data quality is sufficient for style.** Unlike factual QA where hallucination is catastrophic, style transfer training data can be noisy — a slightly imperfect casual rewrite still teaches the model the right register.
3. **Cross-lingual style transfer partially generalizes.** Training on Hindi/Kannada casual pairs will transfer some stylistic signal to Tamil, Telugu, Bengali, and Marathi due to shared model representations, though quality will be lower for languages without reviewer coverage.
4. **LoRA fine-tuning is practical at 4B scale on A100-80GB.** A 4B-parameter model with LoRA (rank 16-64) can be fine-tuned in a few hours on a single A100.

---

## Back-of-Envelope Arithmetic

### Data Generation
- **Target:** 5,000 formal→casual parallel pairs per language × 6 languages = 30,000 pairs
- **Method:** Self-distillation — prompt the base model with few-shot examples of formal→casual rewrites, generate candidates, filter by reviewer (Hindi/Kannada only)
- **Token budget:** ~200 tokens/pair average × 30,000 pairs = 6M tokens of training data
- **Generation time:** At ~200 tok/s decode on the A100, generating 6M tokens ≈ 8.3 hours. With prompt overhead and batching, estimate ~1-2 days.

### Training
- **LoRA config:** rank=32, alpha=64, targeting attention layers → ~26M trainable parameters (0.6% of 4.2B)
- **Training time:** 6M tokens / 4096 seq_len ≈ 1,465 samples. At ~3 samples/sec on A100-80GB with batch size 4 and gradient accumulation, ~8 minutes per epoch. Plan for 3-5 epochs = ~30-40 minutes of training.
- **Total compute:** Well within the 2-week A100 window (< 3 days including all iterations)

### Reviewer Throughput
- **Available:** 1 reviewer, Hindi + Kannada only, 10 h/week, 3 weeks = 30 hours
- **Throughput:** ~100 response evaluations/hour (binary: casual/not-casual) = 3,000 evaluations total
- **Allocation:** 
  - Week 1: Evaluate 500 synthetic training pairs (quality gate for data generation)
  - Week 2: Evaluate 500 model outputs (post-SFT quality check)
  - Week 3: Evaluate 500 final outputs + regression check on formal/factual quality
  - Reserve: 1,500 evaluations for iteration and edge cases

---

## Success Metric with Numeric Threshold

**Primary metric:** ≥ **70%** of reviewer-evaluated model responses rated as "natural/conversational" (on a binary scale) for Hindi and Kannada, on a held-out test set of 200 prompts per language.

**Baseline (expected pre-SFT):** < 30% rated conversational (based on the problem statement that outputs are "too formal/textbook").

**Secondary metrics (automated, for languages without reviewer):**
- Formality classifier score (train a simple classifier on the synthetic pairs) < 0.3 on a 0-1 formality scale for Tamil, Telugu, Bengali, Marathi
- No regression on factual accuracy: score on a translated subset of a QA benchmark should not drop > 2%

---

## Kill Criterion

**If after 1 week of SFT iteration** (i.e., by end of Week 1), the reviewer rating for Hindi has not crossed **50%** on a sample of 200 outputs:

→ **Abandon SFT (path a) and pivot to prompt-engineering (path c).**

**Rationale:** If 5 days of data generation + training + 1 iteration cycle can't get Hindi (the highest-resource language with direct reviewer coverage) above 50%, then either the synthetic data pipeline is broken or the task requires more nuance than LoRA fine-tuning can capture. Prompt-engineering is the fastest fallback and can still ship by Week 3.

**By when:** Decision point is **end of Day 7** (Friday of Week 1).

---

## First Experiment — Day 1

**Goal:** Validate that the base model can produce acceptable casual rewrites when prompted, before investing in the full SFT pipeline.

**Protocol:**
1. Manually write 10 formal→casual Hindi example pairs (with the reviewer's input on what "casual" means for Hindi)
2. Use these as few-shot examples in a prompt to the base model
3. Feed 100 formal Hindi responses from the model and collect casual rewrites
4. Have the reviewer evaluate all 100 rewrites (takes ~1 hour)
5. Measure: what % are rated "natural/casual"?

**Expected outcome:** If few-shot self-distillation produces ≥ 40% acceptable casual outputs, the data generation pipeline is viable and we proceed to full-scale pair generation. If < 20%, we need to reconsider whether the base model's register range is sufficient for self-distillation (may need external casual text as seed).

---

## Why Not Paths (b) or (c)

| | Path (a) SFT | Path (b) Rewriter ≤1B | Path (c) Prompt-only |
|---|---|---|---|
| **Inference cost** | None (style baked in) | +50-100ms latency per request, 2nd model serving cost | Uses context window (~200 tokens of instruction) |
| **Quality ceiling** | High — model learns register natively | Low — 1B model is undertrained for 6 languages | Medium — fragile, hard to maintain across languages |
| **Effort to ship** | ~1 week data + train | ~2 weeks (architecture, training, serving infra) | ~2-3 days per language × 6 = ~2 weeks |
| **Scalability** | Survives model updates (LoRA adapters can be retrained) | Must maintain and serve a second model | Must maintain 6+ language-specific prompts |
| **Risk** | Reviewer bottleneck (only Hindi+Kannada) | Undertrained 1B model for 6 Indic scripts | Style drift, prompt injection vulnerability |

Path (b) is the worst fit: serving a second model adds infrastructure complexity and latency, and a ≤1B model cannot handle 6 typologically diverse languages well. Path (c) is the fallback if (a) fails.
