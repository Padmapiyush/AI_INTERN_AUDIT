# AI Intern Audit Assignment

This repository contains my completed audit of the AI intern assignment. It is organized to match the assignment parts and includes the corrected code, benchmark artifacts, written analyses, and decision memos.

## Repository structure

- `partA/` — tokenizer fertility audit, corrected benchmarking script, FLORES corpus notes, benchmark outputs, and routing recommendation.
- `partB/` — KV-cache capacity math, throughput anomaly analysis, goodput correction, and the production counter to monitor.
- `partC/` — decision memo for making Indic assistant replies more conversational.
- `NOTEBOOK.md` — chronological lab notebook of hypotheses, experiments, results, and revisions.
- `AI_USAGE.md` — disclosure of AI assistance used while completing the assignment.
- `DEFENSE_PREP.md` — concise defense notes for likely review questions.

## Reproducing Part A

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the corrected GPT-2-tokenizer audit:

```bash
python partA/fertility_corrected.py \
  --corpus eng=partA/corpus/eng.txt \
  --corpus hin=partA/corpus/hin.txt \
  --corpus kan=partA/corpus/kan.txt \
  --corpus tam=partA/corpus/tam.txt \
  --tokenizer gpt2 \
  --compare-original
```

Run the multilingual-tokenizer comparison:

```bash
python partA/fertility_corrected.py \
  --corpus eng=partA/corpus/eng.txt \
  --corpus hin=partA/corpus/hin.txt \
  --corpus kan=partA/corpus/kan.txt \
  --corpus tam=partA/corpus/tam.txt \
  --tokenizer hf:xlm-roberta-base
```

Expected saved outputs are in `partA/results_gpt2.txt` and `partA/results_xlm.txt`.

## Solution headline

The original intern report used tokens per word as a serving-cost proxy. That is not reliable across languages because a word is not a constant semantic unit across English and Indic languages. The corrected analysis uses a parallel corpus and emphasizes tokens per parallel sentence as the closest available cost-per-meaning metric.

With the English-centric GPT-2 tokenizer, Hindi remains very expensive at 7.42× English tokens per parallel sentence. However, the multilingual XLM-R tokenizer reduces Hindi to 1.25× English and Kannada/Tamil to about 1.35×. The main recommendation is therefore not to route Indic traffic to a separate stack solely because of the original 6× claim; instead, use a model/tokenizer stack with multilingual coverage and monitor production tokenization metrics by language.
