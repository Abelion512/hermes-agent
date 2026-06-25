# ChatGPT — Research Brief Export

## Cara
1. Buka chatgpt.com
2. Paste prompt di bawah
3. Tunggu output selesai
4. Kalau terpotong, ketik "lanjutkan"
5. Copy output → simpan ke `results/reports/from-ai/chatgpt-full-report.md`

---

## Prompt

Saya sedang melakukan riset tentang **RSI (Recurrent Self-Improvement)** untuk LLM agent.

Konsep: Agent AI yang self-improve dari runtime experience — bukan dari retraining. Setiap task menghasilkan execution trace, diekstrak jadi "lesson", lalu di-inject ke sesi berikutnya.

Kendala: 4 GB RAM, no GPU, memory terisolasi per persona, multi-agent async.

Saya butuh output terstruktur untuk 8 brief berikut. Jawab SEMUA dalam 1 balasan panjang, jangan terpotong.

### Brief 1: Literature Survey
- Posisi RSI di landscape agent self-improvement
- Paper 2025-2026 yang relevan (Self-Harness, Continual Harness, dll)
- Gap: belum ada empirical RSI loop testing

### Brief 2: Memory Architecture
- Persona-isolated memory tanpa vector DB
- SQLite + FTS5: pro, con, tradeoff
- Tiered retrieval strategy

### Brief 3: Failure Propagation
- Multi-agent hierarchy failure modes
- Circuit breaker, DLQ, poison task detection

### Brief 4: RSI Loop Evaluation
- Metrik evaluasi: completion rate, negative transfer, learning curve
- Protocol: n≥20 tasks, 3 conditions (control, raw, validated)

### Brief 5: Cache Prefix Stability
- Prompt caching mechanism di major providers
- Kapan inject lesson vs defer (cache-aware decision)

### Brief 6: Context Compression
- Teknik kompresi tanpa kehilangan fakta
- Selective retention, summarization, KV eviction

### Brief 7: Token Budget Routing
- Decision tree: cheap vs expensive model
- Cost-accuracy pareto frontier

### Brief 8: Experience Extraction
- Cara ekstrak "lesson" dari execution trace
- Hybrid representation: structured + NL
- Validasi 3 lapisan (detect → test → revise)

Format: Markdown, Bahasa Indonesia atau Inggris, dengan tabel perbandingan dan daftar referensi (DOI/arXiv).
