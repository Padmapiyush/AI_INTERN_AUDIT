# B3 — The "Goodput" Misreading (4 pts)

## The Claim in REPORT_v0

Section 2 states:
> *"at batch 16, long prompts hit **1311 tok/s** vs only **883 tok/s** for short prompts. Longer prompts clearly give better GPU utilization."*

Both conclusions — that long prompts are faster and that batch-48 will deliver ~3200 tok/s — come from the **same misreading of one column**: `reported_tok_s`.

---

## What `reported_tok_s` actually measures

`reported_tok_s` counts **all tokens processed**, including both:
- **Prefill tokens** (processing the input prompt — done in parallel, very fast)
- **Decode tokens** (generating output — done sequentially per token, much slower)

For long prompts (3584 tokens), prefill dominates the token count and inflates `reported_tok_s`.

---

## Honest "goodput" of batch-24 long-prompt row

The honest measure is **decode goodput**: how fast does the system generate new (useful) tokens?

### Method 1 — From wall clock time

```
Batch-24 row: 24 requests × 512 gen_len = 12,288 generated tokens
wall_clock = 61.16 s

Decode goodput = 12,288 / 61.16 ≈ 200.9 tok/s
```

Cross-check: the `reported_tok_s` counts all tokens:
```
Total tokens = 24 × (3584 prompt + 512 gen) = 24 × 4096 = 98,304
98,304 / 61.16 ≈ 1,607.5 tok/s ✓ (matches reported_tok_s = 1607.4)
```

So `reported_tok_s` is ~8× higher than actual decode goodput because it includes the 3584 prefill tokens per request.

### Method 2 — From inter-token latency (ITL)

```
itl_ms_p50 = 96.07 ms  (batch-24 row)

Per-request decode time ≈ 512 tokens × 96.07 ms = 49,188 ms ≈ 49.2 s
With 24 concurrent requests:
  decode throughput ≈ (24 × 512) / 49.2 ≈ 249.8 tok/s
```

> **Note:** Method 2 gives a slightly higher number (~250 vs ~201) because ITL is the p50 (median), which underestimates the mean. The wall-clock method (Method 1) is more accurate for aggregate throughput.

---

## The correct comparison

| Config | reported_tok_s | decode goodput (tok/s) | What's inflating it |
|--------|---------------|----------------------|-------------------|
| batch-16, short (512+256) | 883.2 | 883 × 256/768 = **294** | Prefill of 512 tokens |
| batch-16, long (3584+512) | 1,311.4 | 1311 × 512/4096 = **164** | Prefill of 3584 tokens |

When properly adjusted, **short prompts actually have ~1.8× higher decode goodput than long prompts** at batch-16 — the exact opposite of the report's claim. Long prompts look faster only because the prefill tokens inflate the numerator.

---

## What the report should have said

> "At batch 24, the system generates ~200 tok/s of new tokens (decode goodput). The reported 1607 tok/s figure includes prefill processing and should not be used for capacity planning of generation workloads. Short-prompt batches achieve higher decode goodput per request because less memory and compute is consumed by prefill."
