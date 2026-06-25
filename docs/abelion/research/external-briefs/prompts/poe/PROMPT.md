# Poe — Research Prompt

Saya melakukan riset tentang RSI (Recurrent Self-Improvement) — agent AI yang belajar dari runtime experience tanpa retraining. Lingkungan: 4 GB RAM, no GPU, persona-isolated memory, multi-agent async.

Analisis 8 topik berikut dalam 1 balasan Markdown panjang:

1. Literature Survey & Gap Analysis — posisi RSI vs Reflexion/Voyager/ExpeL. Paper 2025-2026.
2. Memory Architecture — SQLite + FTS5 per-persona, tiered retrieval, tanpa vector DB.
3. Failure Propagation — circuit breaker, DLQ, poison task, saga pattern.
4. RSI Loop Evaluation — metrik, protocol, statistical test.
5. Cache Prefix Stability — cache-aware injection decision.
6. Context Compression — selective retention, tradeoff analysis.
7. Token Budget Routing — cost-aware model selection.
8. Experience Extraction — lesson extraction dari execution trace, 3-layer validation.

Sertakan tabel perbandingan dan referensi (DOI).
