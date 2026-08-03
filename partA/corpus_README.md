# Corpus Documentation (Part A1)

## Selection: FLORES-200 (devtest split)

The sample corpora provided (`eng_sample.txt`, `hin_sample.txt`) contained only ~10 sentences. This is insufficient for statistically reliable benchmark results, especially when computing metrics like tokens-per-word which are sensitive to sentence length and word choice.

To fix this, we assembled a proper multilingual eval set using **FLORES-200** (`Muennighoff/flores200` mirror of `facebook/flores`). FLORES is a widely cited, high-quality parallel corpus designed specifically for multilingual evaluation.

### Corpus Details
- **Source:** FLORES-200 `devtest` split
- **Size:** 1,012 parallel sentences per language
- **Domain:** General knowledge (extracted from Wikipedia)
- **Languages:**
  - `eng` — English (Latn script)
  - `hin` — Hindi (Deva script)
  - `kan` — Kannada (Knda script, Dravidian family)
  - `tam` — Tamil (Taml script, Dravidian family)
- **Preprocessing:**
  - Standard NFC Unicode normalization is applied on load (built into `fertility_corrected.py`)
  - No case-folding or destructive normalization was performed prior to tokenization.

### Caveats (What this corpus CANNOT tell you)
While FLORES-200 is an excellent baseline for cross-lingual tokenization efficiency, its domain is strict Wikipedia-style encyclopedia prose. It **cannot** tell us how the tokenizer performs on casual chat, informal slang, code-switching, or customer-service dialogue. Furthermore, because the sentences are strictly parallel, the average sentence length and semantic density are artificially constrained across languages compared to naturally occurring text. This means real-world token counts for typical user queries may diverge from this benchmark.
