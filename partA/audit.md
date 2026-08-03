# Part A2 — Tokenizer Audit (20 pts)

## Audit of `fertility.py`

This document details the bugs found in the original `fertility.py` script, isolating each issue, applying the evidence rule to quantify its distortion, and explaining the conceptual flaws.

### 1. Conceptual Bug: The wrong denominator (The big one)

**The Flaw:**
In line 64: `per_line_fertility.append(len(tokens) / len(words))`
The script computes `tok/word` as the proxy for tokenizer efficiency and cost, and uses it to assert that "Hindi costs 6× more per request."

**Why it's wrong:**
Words do not hold constant meaning across languages. Hindi (and many other languages) is morphologically and syntactically different from English, often expressing the same idea in fewer whitespace-separated words but more characters per word. For example, prepositions in English ("in the cupboard") often become postposition suffixes or single words in Hindi ("अलमारी में"). 
Because the Hindi denominator (words) is smaller for the *same semantic payload*, the `tok/word` ratio artificially skyrockets, distorting the cross-language cost ratio.

**Evidence & Magnitude of Distortion:**
Using the parallel FLORES-200 corpus (where each line holds the exact same meaning across languages), we can see how the denominator fails:
- English FLORES words: ~23,300
- Hindi FLORES words: ~20,500
Hindi uses ~12% fewer words to say the exact same thing.
When we switch from `tok/word` to the honest constant denominator — `tok/parallel_sentence` — the ratio of Hindi/English cost drops significantly. The script's reliance on `tok/word` overstates the relative cost of serving Hindi by a massive margin.

### 2. Statistical Bug: Mean-of-Ratios vs Ratio-of-Means

**The Flaw:**
Lines 64-67 compute the per-line ratio and then take the unweighted average:
`return sum(per_line_fertility) / n, sum(per_line_tpc) / n`

**Why it's wrong:**
A "mean of ratios" gives equal weight to every line, regardless of length. A 2-word sentence has the same impact on the final average as a 50-word sentence. This introduces massive variance and short-line bias. The mathematically correct way to compute an aggregate rate is the "ratio of totals" (micro-average): `total_tokens / total_words`.

**Evidence & Magnitude of Distortion:**
When running the original `gpt2` tokenizer on the FLORES corpus:
- English mean-of-ratios: 1.35
- English ratio-of-totals: 1.25
The buggy mean-of-ratios artificially inflates the English baseline by ~8%, causing further downstream distortion when dividing to find the cross-language ratio.

### 3. Code Bug: Empty words from double-spaces

**The Flaw:**
Line 62: `words = line.split(" ")`

**Why it's wrong:**
Using a strict single-space split on text that contains multiple consecutive spaces (like typos or alignment spacing) produces empty string elements `""` in the list of words. This artificially inflates the word count denominator, lowering the apparent fertility.
This isn't just theoretical — **both** sample files provided by the intern contain this typo:
- `eng_sample.txt` line 7: `books  in` (double space)
- `hin_sample.txt` line 10: `किताबें  अलमारी` (double space)

**Evidence & Magnitude of Distortion:**
A proper split (`line.split()`) ignores variable whitespace. Fixing this bug reduces the word count of the sample texts, raising the true `tok/word` slightly. The impact is small on large clean corpora like FLORES, but on the intern's 10-line samples, it directly skewed the reported numbers.

### 4. The "Harmless Suspicious Thing": `line.lower()` on Indic Scripts

**The Flaw (that isn't one):**
Line 60: `line = line.lower()`
Applying lowercase to all languages looks highly suspicious, because Indic scripts like Devanagari (Hindi), Kannada, and Tamil are **unicameral** (they do not have uppercase/lowercase distinctions). One might assume this corrupts the text.

**Evidence it is harmless:**
In Python, `.lower()` on purely unicameral Unicode blocks (like Devanagari `\u0900-\u097F`) is a strict no-op. It returns the exact same string. It does not corrupt the text, strip combining marks, or change byte lengths.
Therefore, while applying it blindly is sloppy, it **does not** negatively impact the Hindi measurements in `REPORT_v0.md`. Flagging this as a bug that breaks Indic tokenization would be false. (However, it *does* slightly reduce English tokens by collapsing casing variants, creating a minor asymmetry).
