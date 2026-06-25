# Gemini Deep Research — Research Brief Export

## Cara
1. Buka gemini.google.com
2. Aktifkan "Deep Research" mode
3. Paste prompt di bawah
4. Tunggu 3-5 menit
5. Export hasil → simpan ke `results/reports/from-ai/gemini-full-report.md`

---

## Prompt

Lakukan riset mendalam tentang **RSI (Recurrent Self-Improvement) untuk LLM Agent**.

Konsep: Agent AI yang belajar dari pengalaman runtime tanpa retraining. Mirip AlphaGo Zero tapi untuk LLM agent — knowledge grows from experience, not from pre-trained weights alone.

Kendala teknis: 4GB RAM, no GPU, memory terisolasi per persona, multi-agent async.

Saya butuh analisis untuk 8 topik berikut. Output 1 dokumen Markdown panjang dengan tabel perbandingan.

1. **Literature Survey** — Posisi RSI vs Reflexion/Voyager/ExpeL. Paper 2025-2026: Self-Harness, Continual Harness, MemRL, Closing the Feedback Loop. Gap: belum ada empirical test.

2. **Memory Architecture** — Persona isolation tanpa vector DB. SQLite + FTS5 + tiered retrieval. Tradeoff vs vector DB.

3. **Failure Propagation** — Multi-agent hierarchy: circuit breaker, DLQ, poison task, saga pattern. Taksonomi failure.

4. **RSI Loop Evaluation** — Metrik: completion rate, negative transfer, learning curve. Protocol design.

5. **Cache Prefix Stability** — Provider cache mechanism (OpenRouter, Anthropic, OpenAI). Kapan inject lesson vs defer.

6. **Context Compression** — Selective retention, summarization, KV eviction. Information retention rate.

7. **Token Budget Routing** — Smart model routing: decision tree, cost vs accuracy.

8. **Experience Extraction** — Extract lesson from execution trace. Validasi 3 layer: detect → test → revise.
