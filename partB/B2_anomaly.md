# B2 — Throughput Anomaly in Long-Context Sweep (6 pts)

## The Anomaly

The long-context sweep (prompt_len=3584, gen_len=512, total=4096 tokens/seq) shows throughput **declining** beyond batch 24, contradicting the naive expectation that "throughput scales with batch size":

| batch | reported_tok_s | preempted_seqs | kv_cache_util | wall_clock_s |
|-------|---------------|----------------|---------------|-------------|
| 4 | 565.4 | 0 | 0.16 | 28.98 |
| 8 | 902.6 | 0 | 0.31 | 36.30 |
| 16 | 1,311.4 | 0 | 0.62 | 49.97 |
| **24** | **1,607.4** | **0** | **0.93** | **61.16** |
| 32 | 1,384.0 | **7** | 0.97 | 94.71 |
| 48 | 1,298.5 | **23** | 0.97 | 151.41 |

Throughput peaks at batch 24 (1,607 tok/s) then **drops 19%** to 1,298 tok/s at batch 48.

---

## Mechanism — KV Cache Saturation and Preemption

**Root cause: the KV cache cannot hold more than ~25 concurrent 4096-token sequences** (see B1 derivation: 12.08 GB available / 0.470 GB per sequence = 25.7).

**What happens at batch 32+:**
1. The scheduler accepts 32 requests but can only fit ~25 in the KV cache simultaneously.
2. To make progress on all requests, the scheduler must **preempt** (evict) some sequences' KV cache — the `preempted_seqs` column confirms this: 7 at batch-32, 23 at batch-48.
3. When a preempted sequence is rescheduled, its KV cache must be **recomputed from scratch** (re-running prefill for all prior tokens). For prompt_len=3584, this is expensive.
4. The recomputation wastes GPU cycles that could have been spent on decode, causing *net throughput to drop*.

**The specific rows and columns as evidence:**
- **Row 12 (batch=24):** `preempted_seqs=0`, `kv_cache_util=0.93` — all 24 sequences fit, no recomputation overhead.
- **Row 13 (batch=32):** `preempted_seqs=7`, `kv_cache_util=0.97` — 7 sequences had to be evicted and recomputed. Wall clock jumps from 61s to 95s (+55%) despite only 33% more requests.
- **Row 14 (batch=48):** `preempted_seqs=23`, `kv_cache_util=0.97` — nearly half the sequences are preempted. Wall clock is 151s (2.47× batch-24) for only 2× the requests.

---

## Why the report got it wrong

REPORT_v0 Section 2 states:
> *"scale linearly with batch size, so batch 48 should give us ~3200 tok/s"*

This assumes throughput is proportional to batch size: `1607 × (48/24) = 3214`. But:
- This linear extrapolation ignores the **hard memory ceiling** of the KV cache
- The `preempted_seqs` column is the direct signal that linear scaling has broken
- The actual batch-48 throughput is **1,298 tok/s** — a 19% *decrease* from batch-24, not a 100% increase

---

## Proposed Config/Deployment Change

**Change:** Cap the maximum concurrent long-context requests at 24 (or set the scheduler's `max_num_seqs` parameter to ≤ 25 for 4096-token requests).

**Predicted quantitative effect:**
- Eliminates all preemptions → `preempted_seqs` drops to 0
- Preserves peak throughput of ~1,607 tok/s
- Additional requests beyond 24 are queued rather than preempted, giving predictable latency instead of cascading recomputation
- For batch-48 worth of requests: 48 requests served in 2 waves of 24, each taking ~61s → ~122s total, vs the current 151s with preemption thrashing. That's a **19% latency improvement** for the same total work.
