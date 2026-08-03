#!/usr/bin/env python3
"""
fertility_corrected.py -- tokenizer fertility benchmark (corrected)

Fixes from the audit of fertility.py (v0):
  1. Uses split() instead of split(" ") to handle double-spaces correctly
  2. Removes line.lower() -- unnecessary for Indic scripts, and creates
     an asymmetry in English (reduces token count via case folding)
  3. Uses ratio-of-totals (micro-average) instead of mean-of-ratios
     to avoid short-line bias
  4. Adds multiple denominator options: per-word, per-byte, per-grapheme,
     per-sentence (for parallel corpora)

Usage:
    python fertility_corrected.py --corpus eng=corpus/eng.txt \
                                   --corpus hin=corpus/hin.txt \
                                   --corpus kan=corpus/kan.txt \
                                   --corpus tam=corpus/tam.txt \
                                   --tokenizer gpt2

    python fertility_corrected.py --corpus eng=corpus/eng.txt \
                                   --corpus hin=corpus/hin.txt \
                                   --tokenizer hf:xlm-roberta-base

Author: audit submission
"""

import argparse
import sys
import unicodedata
import re
import json


def load_tokenizer(spec: str):
    if spec.startswith("hf:"):
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(spec[3:])
        return lambda s: tok.encode(s, add_special_tokens=False)
    else:
        import tiktoken

        enc = tiktoken.get_encoding(spec)
        return enc.encode


def read_lines(path: str):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            # NFC normalization for consistency
            line = unicodedata.normalize("NFC", line)
            lines.append(line)
    return lines


def count_grapheme_clusters(text: str) -> int:
    """Count user-perceived characters (grapheme clusters) using regex."""
    # Use Unicode grapheme cluster boundary: \X
    # Fallback if 'regex' module not available: count codepoints
    try:
        import regex
        return len(regex.findall(r'\X', text))
    except ImportError:
        # Fallback: count codepoints (less accurate for complex scripts)
        return len(text)


def analyze_corrected(lines, encode):
    """
    Return micro-averaged metrics over all lines.
    Uses ratio-of-totals instead of mean-of-ratios to avoid short-line bias.
    Does NOT lowercase (removed — asymmetric effect across scripts).

    Returns dict with:
      - total_tokens, total_words, total_chars, total_bytes, total_graphemes
      - tok_per_word, tok_per_char, tok_per_byte, tok_per_grapheme
      - tok_per_sentence (average)
      - n_sentences
    """
    total_tokens = 0
    total_words = 0
    total_chars = 0
    total_bytes = 0
    total_graphemes = 0
    n_sentences = 0
    per_sentence_tokens = []

    for line in lines:
        # NO lowercasing -- removed to avoid cross-script asymmetry
        tokens = encode(line)
        # Use split() not split(" ") to handle multiple whitespace correctly
        words = line.split()
        n_tok = len(tokens)
        n_words = len(words)
        n_chars = len(line)
        n_bytes = len(line.encode("utf-8"))
        n_graphemes = count_grapheme_clusters(line)

        total_tokens += n_tok
        total_words += n_words
        total_chars += n_chars
        total_bytes += n_bytes
        total_graphemes += n_graphemes
        n_sentences += 1
        per_sentence_tokens.append(n_tok)

    return {
        "total_tokens": total_tokens,
        "total_words": total_words,
        "total_chars": total_chars,
        "total_bytes": total_bytes,
        "total_graphemes": total_graphemes,
        "n_sentences": n_sentences,
        "tok_per_word": total_tokens / total_words if total_words else 0,
        "tok_per_char": total_tokens / total_chars if total_chars else 0,
        "tok_per_byte": total_tokens / total_bytes if total_bytes else 0,
        "tok_per_grapheme": total_tokens / total_graphemes if total_graphemes else 0,
        "tok_per_sentence": sum(per_sentence_tokens) / n_sentences if n_sentences else 0,
        "per_sentence_tokens": per_sentence_tokens,
    }


def analyze_original_style(lines, encode):
    """
    Reproduce the ORIGINAL (buggy) analysis from fertility.py v0 for comparison.
    - Uses line.lower()
    - Uses split(" ") (not split())
    - Uses mean-of-ratios (not ratio-of-totals)
    """
    per_line_fertility = []
    per_line_tpc = []
    for line in lines:
        line_lower = line.lower()
        tokens = encode(line_lower)
        words = line_lower.split(" ")
        chars = len(line_lower)
        per_line_fertility.append(len(tokens) / len(words))
        per_line_tpc.append(len(tokens) / chars)
    n = len(per_line_fertility)
    return {
        "fertility_mean_of_ratios": sum(per_line_fertility) / n,
        "tpc_mean_of_ratios": sum(per_line_tpc) / n,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Corrected tokenizer fertility benchmark"
    )
    ap.add_argument(
        "--corpus",
        action="append",
        required=True,
        metavar="LANG=PATH",
        help="language code and path, e.g. eng=data/eng.txt (repeatable)",
    )
    ap.add_argument("--tokenizer", default="gpt2")
    ap.add_argument(
        "--json-out",
        default=None,
        help="Optional: write full results as JSON to this file",
    )
    ap.add_argument(
        "--compare-original",
        action="store_true",
        help="Also run the original buggy analysis for comparison",
    )
    args = ap.parse_args()

    encode = load_tokenizer(args.tokenizer)

    print(f"\n{'='*72}")
    print(f"Tokenizer: {args.tokenizer}")
    print(f"{'='*72}\n")

    # Header
    header = (
        f"{'lang':<8}"
        f"{'sentences':>10}"
        f"{'tok/word':>12}"
        f"{'tok/char':>12}"
        f"{'tok/byte':>12}"
        f"{'tok/grapheme':>14}"
        f"{'tok/sentence':>14}"
    )
    print(header)
    print("-" * len(header))

    results = {}
    for spec in args.corpus:
        lang, path = spec.split("=", 1)
        lines = read_lines(path)
        r = analyze_corrected(lines, encode)
        results[lang] = r
        print(
            f"{lang:<8}"
            f"{r['n_sentences']:>10}"
            f"{r['tok_per_word']:>12.3f}"
            f"{r['tok_per_char']:>12.4f}"
            f"{r['tok_per_byte']:>12.4f}"
            f"{r['tok_per_grapheme']:>14.3f}"
            f"{r['tok_per_sentence']:>14.1f}"
        )

    # Cross-language ratios (relative to first language)
    if len(results) >= 2:
        langs = list(results)
        base = langs[0]
        print(f"\n--- Ratios relative to {base} ---\n")
        ratio_header = (
            f"{'lang':<8}"
            f"{'tok/word':>12}"
            f"{'tok/byte':>12}"
            f"{'tok/grapheme':>14}"
            f"{'tok/sentence':>14}"
        )
        print(ratio_header)
        print("-" * len(ratio_header))
        for lang in langs:
            r_lang = results[lang]
            r_base = results[base]
            print(
                f"{lang:<8}"
                f"{r_lang['tok_per_word']/r_base['tok_per_word']:>12.2f}x"
                f"{r_lang['tok_per_byte']/r_base['tok_per_byte']:>12.2f}x"
                f"{r_lang['tok_per_grapheme']/r_base['tok_per_grapheme']:>14.2f}x"
                f"{r_lang['tok_per_sentence']/r_base['tok_per_sentence']:>14.2f}x"
            )

    # Compare with original buggy analysis if requested
    if args.compare_original:
        print(f"\n{'='*72}")
        print("COMPARISON: Original (buggy) vs Corrected analysis")
        print(f"{'='*72}\n")
        comp_header = (
            f"{'lang':<8}"
            f"{'orig tok/word':>16}"
            f"{'fixed tok/word':>16}"
            f"{'delta':>10}"
            f"{'orig tok/char':>16}"
            f"{'fixed tok/char':>16}"
        )
        print(comp_header)
        print("-" * len(comp_header))
        for spec in args.corpus:
            lang, path = spec.split("=", 1)
            lines = read_lines(path)
            orig = analyze_original_style(lines, encode)
            fixed = results[lang]
            delta_fert = (
                (fixed["tok_per_word"] - orig["fertility_mean_of_ratios"])
                / orig["fertility_mean_of_ratios"]
                * 100
            )
            print(
                f"{lang:<8}"
                f"{orig['fertility_mean_of_ratios']:>16.3f}"
                f"{fixed['tok_per_word']:>16.3f}"
                f"{delta_fert:>+9.1f}%"
                f"{orig['tpc_mean_of_ratios']:>16.4f}"
                f"{fixed['tok_per_char']:>16.4f}"
            )

    # JSON output
    if args.json_out:
        # Remove per_sentence_tokens for cleaner JSON
        json_results = {}
        for lang, r in results.items():
            json_results[lang] = {k: v for k, v in r.items() if k != "per_sentence_tokens"}
            json_results[lang]["tokenizer"] = args.tokenizer
        with open(args.json_out, "w") as f:
            json.dump(json_results, f, indent=2)
        print(f"\nJSON results written to {args.json_out}")


if __name__ == "__main__":
    main()
