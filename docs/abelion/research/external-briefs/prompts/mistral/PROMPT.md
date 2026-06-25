# Mistral — Research Prompt (sama dengan ChatGPT)

Saya sedang melakukan riset tentang RSI (Recurrent Self-Improvement) untuk LLM agent.

Konsep: Agent AI yang self-improve dari runtime experience — bukan dari retraining. Setiap task menghasilkan execution trace, diekstrak jadi "lesson", lalu di-inject ke sesi berikutnya.

Kendala: 4 GB RAM, no GPU, memory terisolasi per persona, multi-agent async.

Saya butuh output terstruktur untuk 8 brief berikut. Jawab SEMUA dalam 1 balasan panjang.

1. Literature Survey — Posisi RSI di landscape, paper 2025-2026, gap empirical testing
2. Memory Architecture — Persona-isolated tanpa vector DB, SQLite+FTS5, tiered retrieval
3. Failure Propagation — Multi-agent failure modes, circuit breaker, DLQ, poison task
4. RSI Loop Evaluation — Metrik: completion rate, negative transfer, learning curve
5. Cache Prefix Stability — Provider cache mechanism, cache-aware learning decision
6. Context Compression — Selective retention, summarization, KV eviction
7. Token Budget Routing — Decision tree, cost-accuracy pareto
8. Experience Extraction — Ekstrak lesson dari trace, hybrid representation, 3-layer validation

Format: Markdown dengan tabel perbandingan + referensi (DOI/arXiv).
