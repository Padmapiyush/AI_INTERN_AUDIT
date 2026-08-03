# B1 — KV-Cache Capacity Calculation (7 pts)

## Given (from `model_spec.md`)

| Property | Value |
|----------|-------|
| Model | FLM-4B-Instruct (dense) |
| Parameters | 4.2 B |
| Layers | 28 |
| Attention heads (Q) | 24 |
| **KV heads (GQA)** | **8** |
| head_dim | 128 |
| Weights precision | fp16 (2 bytes) |
| KV cache precision | fp16 (2 bytes) |
| GPU | 1× NVIDIA L4, 24 GB |
| `gpu_memory_utilization` | 0.92 |
| Non-KV overhead | ~1.6 GB |
| `max_model_len` | 4096 |

---

## (a) KV-cache bytes per token — exact

Every stored token needs both K and V vectors for every layer and KV head:

```text
bytes_per_token = 2 (K and V)
                × 8 (KV heads)
                × 128 (head_dim)
                × 28 (layers)
                × 2 (fp16 bytes)
                = 114,688 bytes/token
                = 112 KiB/token
```

---

## (b) Approximate maximum concurrent 4096-token sequences

Use decimal GB consistently, because the spec gives 24 GB and 4.2B parameters in decimal units:

```text
Usable GPU memory = 24.0 GB × 0.92 = 22.08 GB
Model weights     = 4.2B params × 2 bytes = 8.40 GB
Non-KV overhead   = 1.60 GB
Available for KV  = 22.08 - 8.40 - 1.60 = 12.08 GB
```

Per 4096-token sequence:

```text
KV per sequence = 114,688 bytes/token × 4096 tokens
                = 469,762,048 bytes
                ≈ 0.470 GB
```

Maximum full-length sequences:

```text
12.08 GB / 0.469762048 GB = 25.72
floor(25.72) = 25 full 4096-token sequences
```

**Prediction from the model spec alone: about 25 full 4096-token sequences (roughly 26 at the boundary).**

---

## Check against `bench_log.csv`

| batch | prompt_len | gen_len | total_tokens/seq | kv_cache_util | preempted_seqs |
|-------|------------|---------|------------------|---------------|----------------|
| 24 | 3584 | 512 | 4096 | 0.93 | 0 |
| 32 | 3584 | 512 | 4096 | 0.97 | 7 |

This matches the prediction closely:

- Batch 24 fits without preemption and uses 93% KV cache. `24 / 25.72 = 93.3%`, almost exactly the logged `kv_cache_util=0.93`.
- Batch 32 has `preempted_seqs=7`, implying about `32 - 7 = 25` active full-length sequences can remain resident at once.
- Therefore the log validates the spec-derived capacity: **the practical safe limit is 24, and the hard full-length capacity is about 25 sequences.**
