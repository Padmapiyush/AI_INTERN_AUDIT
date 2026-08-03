# Defense Preparation Guide

The defense session is 30 minutes, screen shared, with your repo open. The graders will push you to see if you actually understand the work you submitted or if you just blindly pasted from an AI.

**Core Rule:** "Fabricated evidence discovered at any point... is an automatic fail." You must be able to prove everything you claim.

---

## 1. "Re-derive this number"

They will likely ask you to explain or recalculate one of the numbers from Part B on the fly.

### How to re-derive KV Cache limit (B1)
If asked: *"Where did ~25 concurrent sequences come from?"*
**What to say:** "The limit comes from the available GPU memory after model weights and overhead are loaded."
**Live derivation steps to type out or walk through:**
1. Usable memory = `24 GB * 0.92 = 22.08 GB`
2. Weights = `4.2B params * 2 bytes = 8.4 GB`
3. Available for cache = `22.08 - 8.4 - 1.6 (overhead) = 12.08 GB`
4. Cache per token = `2 (K+V) * 8 (KV heads) * 128 (head dim) * 28 (layers) * 2 bytes = 114,688 bytes` (112 KiB)
5. Cache per sequence = `114,688 * 4096 = 469,762,048 bytes (0.470 GB)`
6. Result: `12.08 / 0.470 = 25.7` → Floor to **25 full sequences**.

### How to re-derive Decode Goodput (B3)
If asked: *"How did you get ~200 tok/s for goodput when the log says 1607?"*
**What to say:** "The `reported_tok_s` includes prefill tokens which are processed instantly in parallel, inflating the number. Goodput only counts the generated tokens."
**Live derivation steps:**
1. Open `bench_log.csv`, point to Row 12 (batch 24, prompt 3584, gen 512).
2. "We generated 512 tokens for 24 requests = 12,288 new tokens."
3. "It took 61.16 seconds."
4. `12,288 / 61.16 = 200.9 tok/s decode goodput`.

---

## 2. "Run your script with this input I'm about to paste"

They may paste a weird string in chat (e.g., emojis, Zalgo text, or Hindi with weird zero-width joiners) and ask you to run the fertility script on it.

**How to handle it smoothly live:**
1. Have a terminal open in the repository root, then `cd partA` if needed
2. When they give you text, quickly create a text file:
   - On Windows: `notepad test.txt`
   - Paste the text, save, and close.
3. Run the script:
   `python fertility_corrected.py --corpus test=test.txt --tokenizer gpt2`
4. **Important:** If it crashes, *don't panic*. Look at the error. If it's a Unicode error, remind them that the script uses `utf-8` and `unicodedata.normalize("NFC", line)`, which handles standard text, but if they pasted binary junk, it might fail.

---

## 3. "Add this flag live"

They might say: *"Can you add a `--verbose` flag right now that prints the longest sentence in the corpus?"*

**How to do it live (practice this!):**
1. Open `fertility_corrected.py` in your IDE.
2. Go to `def main():` and the `argparse` section.
3. Add the argument:
   ```python
   ap.add_argument("--verbose", action="store_true", help="Print debug info")
   ```
4. Find where the lines are processed. If they asked for the longest sentence, you could modify `analyze_corrected` or just do it in `main()` after reading the lines:
   ```python
   lines = read_lines(path)
   if args.verbose:
       longest = max(lines, key=len)
       print(f"DEBUG: Longest line in {lang} has {len(longest)} chars: {longest[:50]}...")
   ```
5. Run it to prove it works.

---

## 4. Defending your Conceptual Claims

They will push back on your logic to see if you crumble. Hold your ground if you have the data.

### Pushback: "Why did you use tokens-per-sentence? Tokens-per-word is the standard metric."
**Your Defense:** "Tokens-per-word only measures tokenizer behavior relative to whitespace. But billing and capacity are based on serving user requests. A user asking 'Where is the book?' in English vs Hindi ('किताब कहाँ है?') is making the same semantic request. Because Hindi is postpositional and agglutinative in places English isn't, it uses fewer whitespace-separated words for the exact same idea. Using words as the denominator artificially makes Hindi look 6x worse. By using parallel sentences from FLORES, we hold the *meaning* constant, which is the only fair way to compare cost-to-serve."

### Pushback: "You removed `line.lower()` in your corrected script. Wasn't it a bug that it corrupted Hindi?"
**Your Defense (The Trap!):** "No, it wasn't a bug for Hindi. Devanagari is a unicameral script, so calling `.lower()` on it in Python is a strict no-op. It didn't corrupt the Hindi data or inflate the numbers in the intern's report. I removed it because applying it to English reduces English token counts by collapsing casing variants, creating an asymmetry in the benchmark. If I claimed `.lower()` broke the Hindi text, I would be making a claim without evidence."

### Pushback: "You claim the report was wrong about batch 48 scaling. But the log clearly shows 48 requests finished."
**Your Defense:** "They finished, but they thrashed the KV cache. The available memory only fits ~25 concurrent sequences of length 4096. At batch 48, the scheduler had to preempt 23 sequences (as shown in the log). Every preemption forces a recomputation of the 3584-token prompt. As a result, batch 48 actually took 151 seconds for 48 requests, whereas batch 24 took 61 seconds. Two waves of batch 24 would take 122 seconds. Batch 48 is actively slower than batch 24."

---

## 5. Live Defense Checklist

Before joining the call, make sure you have:
- [ ] Terminal open in the repository root (or `partA/` for the tokenizer script)
- [ ] Your IDE open with `fertility_corrected.py` ready to edit
- [ ] `bench_log.csv` open in a spreadsheet or markdown viewer so you can point to rows
- [ ] A scratchpad text file ready to paste whatever they throw at you
- [ ] A calculator app open for quick math
