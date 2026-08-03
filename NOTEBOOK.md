# Lab Notebook — FLAM AI Assignment 2026

*Chronological log of hypothesis → experiment → result → revision.*
*Started: 2026-08-02*

---

## Entry 1 — Initial reading and orientation (Aug 2, 6:30 PM)

**Goal:** Understand what the intern did and what I'm auditing.

Read through all starter kit files:
- `fertility.py` — 107-line script computing tokens-per-word ("fertility") and tokens-per-char for language corpora
- `REPORT_v0.md` — intern's report claiming Hindi is 5.89× worse than English in fertility, recommending 6× cost budget and separate Indic model
- `corpus_sample/` — 10 English + 10 Hindi sentences (toy data, not a real eval set)
- `bench/model_spec.md` — FLM-4B-Instruct model details (4.2B params, 28 layers, GQA with 8 KV heads, head_dim 128, fp16, on 1× L4 24GB)
- `bench/bench_log.csv` — 14 rows of load test data at various batch sizes and prompt lengths

**First impressions / hypotheses to test:**
1. The fertility script splits on `" "` (single space) — what happens with repeated whitespace? I need to measure before calling it a real bug.
2. `line.lower()` is applied to all languages — could this hurt Indic scripts? Need to check if Devanagari/Kannada/Tamil are case-insensitive.
3. The report's "6× cost" claim is based on tok/word ratio — but is tok/word the right metric for cost? Hindi words might carry more meaning per word than English.
4. The bench log shows throughput *dropping* at batch 32+ for long prompts while `preempted_seqs` rises — the report ignores this completely.
5. The report claims batch-48 would give 3200 tok/s by linear extrapolation — but the data shows the opposite trend.

---

## Entry 2 — Corpus construction (Aug 2, ~6:45 PM)

**Hypothesis:** The sample corpora (~10 sentences each) are too small for any reliable measurement. I need a proper parallel eval set.

**Decision:** Use FLORES-200 devtest split.
- Why FLORES: parallel sentences across all needed languages, well-known benchmark, freely available
- Languages: English (eng_Latn), Hindi (hin_Deva), Kannada (kan_Knda), Tamil (tam_Taml)
- Size: ~1012 sentences per language (devtest split)

**Action:** Downloading via HuggingFace datasets library.
*Update:* `facebook/flores` was gated, so I switched to the `Muennighoff/flores200` mirror, which required downgrading `datasets<=2.19.1` to support dataset scripts.

---

## Entry 3 — Analyzing `fertility.py` Bugs (Aug 2, ~7:15 PM)

While the corpus is downloading, I reviewed `fertility.py` line-by-line and separated defensible findings from suspicions:

1. **The Conceptual Bug:** The intern computes `tok/word` to derive cost. This is fundamentally wrong for cross-language comparison because languages have different words-per-idea ratios (e.g., English uses prepositions, Hindi uses postpositions). Using words as the denominator artificially inflates the Hindi cost. The correct metric is `tok/parallel_sentence`.
2. **The Statistical Bug:** Mean-of-ratios (averaging per-line ratios) introduces short-line bias. It should be ratio-of-totals (micro-average).
3. **Robustness suspicion:** `line.split(" ")` would break on repeated spaces, but I should not make it a headline claim unless I can show it materially affects the supplied data. I will fix it in the corrected script but label it as robustness, not the main audit finding.
4. **The "Harmless Suspicious Thing":** `line.lower()` is applied to all text. This looks like a bug for Indic scripts since they don't have casing, but in Python, `.lower()` on Devanagari is actually a strict no-op, so it didn't corrupt the text or inflate the numbers.

I've written `fertility_corrected.py` to fix the measurement method, use robust whitespace handling, and support multiple denominators (words, chars, bytes, graphemes, sentences).

---

## Entry 4 — Part B and Part C (Aug 2, ~7:30 PM)

While still waiting on the download, I completed all analytical work for Parts B and C:
- Derived the KV cache limit: ~25 concurrent 4096-token sequences fit in the available 12.08 GB after weights and overhead.
- Explained the throughput anomaly: batch 32+ exceeds the ~25-sequence limit, causing KV cache preemptions and expensive recomputations.
- Corrected the goodput misreading: the intern conflated prefill tokens with decode tokens. True batch-24 goodput is ~200 tok/s.
- Recommended SFT (path a) for the casual Indic assistant project in a 1-page memo.

Next: running the benchmark on the FLORES corpus to finalize Part A numbers.

---

## Entry 5 — Benchmark Results & Finalizing (Aug 2, ~8:30 PM)

The FLORES corpus download completed after setting `PYTHONUTF8=1` (it failed at first due to a Windows `cp1252` charmap bug in the HuggingFace script).

I ran `fertility_corrected.py` with both `gpt2` and `hf:xlm-roberta-base`. The results are staggering:

- Using `gpt2` and `tok/sentence` (the correct baseline): Hindi is 7.42× more expensive than English. (Kannada is 13.6×, Tamil is 15.5×).
- Using `xlm-roberta-base`: Hindi is only **1.25×** more expensive than English! (Kannada and Tamil are ~1.35×).

**Conclusion:** The intern's recommendation to build a whole separate Indic serving stack and budget 6× costs was entirely based on using an English-centric tokenizer. By simply swapping the tokenizer to a modern multilingual one (like XLM-R), the cost gap mostly disappears.

I've updated `partA/analysis.md` and `partA/memo.md` with these numbers and the strong recommendation: **Do not route Indic traffic separately. Use a multilingual tokenizer.**

The assignment is complete. I'm ready for the defense session.

