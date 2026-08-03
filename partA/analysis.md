# Part A3 — Corrected Analysis (12 pts)

## Setup
Using the FLORES-200 devtest corpus (1012 parallel sentences per language), we computed tokenizer statistics for four languages: English, Hindi, Kannada, and Tamil.

We compared the original `gpt2` (tiktoken) tokenizer against `hf:xlm-roberta-base`, a multilingual tokenizer. For both, we computed four denominators:
- `tok/word` (whitespace separated)
- `tok/char` (Python string length)
- `tok/byte` (UTF-8 encoded size)
- `tok/grapheme` (User-perceived characters)
- `tok/sentence` (Tokens per parallel sentence)

## Results

### 1. `gpt2` (tiktoken)

| lang | sentences | tok/word | tok/char | tok/byte | tok/grapheme | **tok/sentence** |
|------|-----------|----------|----------|----------|--------------|------------------|
| eng  | 1012      | 1.235    | 0.2049   | 0.2047   | 0.205        | **26.7**         |
| hin  | 1012      | 7.826    | 1.5299   | 0.5947   | 2.335        | **198.3**        |
| kan  | 1012      | 22.818   | 2.6616   | 0.9788   | 4.065        | **363.0**        |
| tam  | 1012      | 25.047   | 2.7261   | 0.9965   | 4.213        | **415.2**        |

**Ratios relative to English (`gpt2`):**
| lang | tok/word | tok/byte | tok/grapheme | **tok/sentence** |
|------|----------|----------|--------------|------------------|
| eng  | 1.00x    | 1.00x    | 1.00x        | **1.00x**        |
| hin  | 6.34x    | 2.90x    | 11.39x       | **7.42x**        |
| kan  | 18.48x   | 4.78x    | 19.84x       | **13.58x**       |
| tam  | 20.28x   | 4.87x    | 20.56x       | **15.54x**       |

### 2. `hf:xlm-roberta-base` (multilingual)

| lang | sentences | tok/word | tok/char | tok/byte | tok/grapheme | **tok/sentence** |
|------|-----------|----------|----------|----------|--------------|------------------|
| eng  | 1012      | 1.400    | 0.2323   | 0.2321   | 0.232        | **30.3**         |
| hin  | 1012      | 1.491    | 0.2914   | 0.1133   | 0.445        | **37.8**         |
| kan  | 1012      | 2.575    | 0.3004   | 0.1105   | 0.459        | **41.0**         |
| tam  | 1012      | 2.465    | 0.2683   | 0.0981   | 0.415        | **40.9**         |

**Ratios relative to English (`xlm-roberta-base`):**
| lang | tok/word | tok/byte | tok/grapheme | **tok/sentence** |
|------|----------|----------|--------------|------------------|
| eng  | 1.00x    | 1.00x    | 1.00x        | **1.00x**        |
| hin  | 1.06x    | 0.49x    | 1.91x        | **1.25x**        |
| kan  | 1.84x    | 0.48x    | 1.97x        | **1.35x**        |
| tam  | 1.76x    | 0.42x    | 1.78x        | **1.35x**        |

## Which single number should drive routing decisions?

**The single number that should drive routing and cost decisions is: `tok/sentence` (Tokens per parallel sentence).**

### Why?
The ultimate cost of serving a language is determined by how many tokens it takes to *express a given meaning* (or fulfill a given user intent). Because our eval corpus (FLORES) is strictly parallel, each sentence contains the exact same meaning across all languages. Therefore, the ratio of tokens per sentence directly measures the ratio of cost per unit of meaning.

Using `tok/word` is fundamentally flawed because different languages use different numbers of words to express the same idea (e.g., English uses prepositions where Hindi uses postpositions attached to words, or languages might be highly agglutinative). Using `tok/char` or `tok/byte` is better than words, but still penalized by the intrinsic byte-heaviness of certain scripts.

By anchoring the denominator to *meaning* (the parallel sentence), we get a true apples-to-apples comparison of how much more expensive one language is to serve than another.
