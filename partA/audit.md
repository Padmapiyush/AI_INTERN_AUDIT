# Part A2 — Tokenizer Audit (20 pts)

## Audit of `fertility.py`

I am only counting flaws I can tie to measured evidence. The script mostly computes what it says it computes; the biggest problem is that the thing it computes (`tokens / whitespace word`) is the wrong decision metric for routing/cost.

## Reproduction command for the measured evidence

The numbers below come from this run (saved in `results_gpt2.txt`):

```bash
python partA/fertility_corrected.py \
  --corpus eng=partA/corpus/eng.txt \
  --corpus hin=partA/corpus/hin.txt \
  --corpus kan=partA/corpus/kan.txt \
  --corpus tam=partA/corpus/tam.txt \
  --tokenizer gpt2 \
  --compare-original
```

### 1. Conceptual flaw: `tok/word` is the wrong denominator for serving cost

**Where:** `fertility_original.py` computes `len(tokens) / len(words)` after splitting each line into whitespace words.

**Why it matters:** Serving cost is proportional to tokens per request or per unit of user intent, not tokens per whitespace-delimited word. Words do not hold meaning constant across languages. Hindi can express the same sentence with fewer whitespace words than English, so normalizing by word can make Hindi look worse for reasons unrelated to request cost.

**Evidence and magnitude:** On the parallel FLORES corpus, the same 1,012 meanings contain about 23.3k English whitespace words and about 20.5k Hindi whitespace words, so Hindi has ~12% fewer denominator units for the same semantic payload. With GPT-2 tokenization, Hindi/English is 6.34× by `tok/word` but 7.42× by `tok/parallel_sentence`; the exact multiplier changes when the denominator is fixed to meaning. With the multilingual XLM-R tokenizer, Hindi/English is only 1.25× by `tok/parallel_sentence`, showing that the routing conclusion depends on tokenizer choice rather than the original `tok/word` headline.

**Direction of distortion:** `tok/word` does not provide a stable cross-language cost denominator. It can either understate or overstate cost depending on morphology and word segmentation; in this corpus, the original style of analysis gives a different Hindi multiplier than the meaning-held-constant metric, so it is not safe for routing.

### 2. Statistical flaw: mean of per-line ratios instead of ratio of totals

**Where:** `fertility_original.py` appends each line's ratio and then averages the ratios.

**Why it matters:** A 2-word line gets the same weight as a 50-word line. For aggregate rates, the defensible estimate is the micro-average: `total_tokens / total_words`, `total_tokens / total_chars`, etc.

**Evidence and magnitude:** On the FLORES corpus with GPT-2 tokenization:

| language | original mean-of-line-ratios `tok/word` | corrected ratio-of-totals `tok/word` | direction |
|----------|-----------------------------------------|--------------------------------------|-----------|
| eng | 1.287 | 1.235 | original is +4.1% high |
| hin | 7.865 | 7.826 | original is +0.5% high |
| kan | 22.570 | 22.818 | original is -1.1% low |
| tam | 25.127 | 25.047 | original is +0.3% high |

**Direction of distortion:** Small on this larger corpus but real, and not even directionally consistent across languages. That makes it a poor basis for a leadership-facing cost multiplier.

### 3. Robustness issue: `split(" ")` is brittle, but not my main claimed bug

**Where:** `fertility_original.py` uses `line.split(" ")` instead of `line.split()`.

**Why it matters:** If input contains repeated spaces, `split(" ")` counts empty strings as words and lowers `tok/word`. A robust script should use `split()` so arbitrary whitespace is treated as one separator.

**Evidence and magnitude:** This issue is input-dependent. The FLORES files in this repo are clean enough that the measured aggregate effect is negligible compared with the conceptual denominator problem above. I fixed it in `fertility_corrected.py` for robustness, but I would not present it as the headline audit finding unless the provided starter sample visibly contains repeated-space examples.

### 4. Suspicious but harmless: `line.lower()` on Indic scripts

**Where:** `fertility_original.py` lowercases every line before tokenization.

**Why it looks suspicious:** Applying English-style case normalization globally sounds like it might corrupt Indic scripts.

**Evidence it is harmless for the claimed Indic issue:** Devanagari, Kannada, and Tamil are unicameral scripts. In Python, lowercasing those characters leaves them unchanged; it does not strip matras, combining marks, or bytes. Therefore, claiming that `.lower()` corrupts Hindi/Kannada/Tamil would violate the evidence rule.

**Actual effect:** It can slightly change English tokenization by collapsing case variants, so I removed it from the corrected benchmark for symmetry. But it is not the cause of the large Indic token counts.
