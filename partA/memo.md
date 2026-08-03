# Recommendation Memo — Part A4 (8 pts)

## 1. Corrected Headline Numbers

The original report stated that Hindi tokenization was 5.89× worse than English based on `tok/word`, implying a 6× serving cost.

Our corrected analysis, using a parallel corpus and the proper metric (`tok/parallel_sentence`), shows that the answer depends heavily on tokenizer choice:

- **Original `gpt2` tokenizer:** Hindi is **7.42×** more expensive than English to serve equivalent meaning (198.3 vs 26.7 tok/sentence).
- **Multilingual `xlm-roberta-base` tokenizer:** Hindi is only **1.25×** more expensive than English (37.8 vs 30.3 tok/sentence). Kannada and Tamil are similarly efficient at **1.35×**.

## 2. Routing Recommendation

**Do not route Indic traffic to a separate model.**
Instead, we should standardize on a model/tokenizer stack with strong multilingual coverage. `xlm-roberta-base` is used here as a tokenizer benchmark, not as the recommended generative model.

The original report's recommendation of a 6× budget was based on a broken metric (`tok/word`) and an English-centric tokenizer (`gpt2`). When measured properly using a multilingual tokenizer and a constant-meaning denominator, the Hindi cost gap is about 25% over English rather than a blanket 6× serving penalty. A 25% throughput penalty for Indic traffic is small enough that the operational overhead of maintaining, deploying, and routing to a completely separate Indic-specific model outweighs the compute savings. Serve all languages from a unified multilingual model.

## 3. The Biggest Caveat

The eval corpus used (FLORES-200) is strictly Wikipedia-domain text with perfectly parallel, complete sentences. While excellent for controlled benchmarks, this is not representative of our production traffic. Real-world user prompts will likely contain casual conversational language, heavy code-switching (e.g., Hinglish), abbreviations, and incomplete sentences. The tokenization efficiency on formal Wikipedia text may not map directly to production chat data.

## 4. Production Monitoring Metric

To catch if this analysis becomes wrong in production, we should monitor:
**Median `tokens_per_utf8_byte`** (bucketed by detected language).

**Why:** Since we don't have parallel sentences in production, we can't measure `tok/sentence`. The next most stable physical constant is UTF-8 bytes. If the `tok/byte` ratio for a language begins to drift significantly (e.g., >10%) from the baseline measured on our corpus, it indicates a shift in domain, script usage (e.g., more English script being used for Hindi), or model behavior that warrants a fresh capacity analysis.
