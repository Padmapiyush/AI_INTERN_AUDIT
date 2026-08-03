# B4 — Single Counter to Confirm the B2 Mechanism (3 pts)

## The metric: `preempted_seqs` (or equivalently, `vllm:num_preemptions_total`)

The single counter/metric from the serving stack that directly confirms the B2 mechanism (KV-cache saturation causing throughput degradation) is the **preemption counter**.

In vLLM (the most common serving framework for this setup), this is exposed as:
- `vllm:num_preemptions_total` — a Prometheus counter on the `/metrics` endpoint
- `preempted_seqs` in the bench log (which is the same underlying counter)

## Why this metric, specifically

The B2 mechanism has three steps:
1. KV cache fills up → 2. Scheduler preempts sequences → 3. Recomputation causes throughput loss

The preemption counter sits at **step 2** — it's the direct causal link between "memory is full" and "throughput drops." It's more informative than `kv_cache_util` alone (which just says memory is full but doesn't tell you if preemption is actually happening) and more actionable than wall-clock time (which could degrade for many reasons).

## Expected values

| Batch size (4096-tok seqs) | Expected `preempted_seqs` | Rationale |
|---------------------------|--------------------------|-----------|
| ≤ 24 | **0** | Fits within ~25-seq KV cache capacity |
| 25–26 | 0 or small | Near the boundary |
| 32 | **7+** | Exceeds capacity by ~6-7 sequences |
| 48 | **23+** | Exceeds capacity by ~22-23 sequences |

If we set `max_num_seqs ≤ 25` as proposed in B2, this counter should remain at **0** for all batch sizes, confirming the fix eliminates the mechanism entirely.
