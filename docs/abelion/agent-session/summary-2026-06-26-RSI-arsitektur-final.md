# Session Summary — 2026-06-26/27

> **Sesi ini mencakup:** Arsitektur ulang RSI, 4 eksperimen (540 tasks), Pre-flight spec validator, Live status tool.
> **Durasi:** ~12 jam (2 sesi terpisah, fork + lanjutan)
> **Commit:** 8562fe9b6, 3d55e3b52, 374f150ce
> **Branch:** research

---

## 1. Problem Discovery

### Eksperimen v1 (Sejak awal — sebelum sesi ini)
- 20 easy tasks, max_iter=10, Gemini flash-lite
- **100% completion across ALL conditions** → ceiling effect
- Lesson template: *"Using X without proper validation causes errors: {raw dump}"* → useless

### Eksperimen v2 (Awal sesi)
- 20 hard tasks, max_iter=3, Gemini flash-lite
- **25% completion** → meaningful baseline
- A=25% B=27% C=18% → pola B > A > C
- Tapi **lesson quality rendah** → extractor bungkus raw error, bukan synthesize actionable heuristic

### Eksperimen v3 (Tengah sesi — partial)
- Pipeline improved (extractor v2 → actionable heuristics)
- **Dihentikan** karena API key OpenRouter expired (401)

### Eksperimen v4 (Akhir sesi)
- Gemini proxy (`gc/gemini-3.1-flash-lite-preview`)
- 180 tasks, hard, max_iter=3
- **A=20% B=23% C=18%** — konsisten dengan v2
- Pola B > A stabil di 2 independent run ✅
- Belum signifikan (p=0.48), butuh n lebih besar atau effect size lebih kuat

---

## 2. Arahan Arsitektur Final

### Kesimpulan dari Mentor (Pertanyaan #1-6)

| # | Pertanyaan | Jawaban |
|---|-----------|---------|
| 1 | abelion_core vs RSI plugin? | **Bukan duplikasi.** Pattern first, LLM fallback. Hubungkan via interface, jangan merge. |
| 2 | MemoryProvider → general plugin? | **Salah extension point.** Pindah ke general plugin (`post_tool_call`, `on_session_start`, `on_session_end`). |
| 3 | Prompt cache strategy? | **Tiered injection.** Static (cached) + semi-static (session) + dynamic (ephemeral). RSI inject via `agent.ephemeral_system_prompt`. |
| 4 | Apakah RSI cukup bridging gap? | **Tidak sendiri.** RSI tutup behavioral gaps, bukan capability gaps. Tapi complementary dengan model upgrade. |
| 5 | Metrik lebih baik? | **FASR** (First-Attempt Success Rate) + **Error Type Entropy**. Bukan completion rate. |
| 6 | Prompt caching di Hermes? | **Sudah handle.** `_cached_system_prompt` + `ephemeral_system_prompt`. RSI injection di ephemeral aman untuk cache. |

### File Structure Final

```
plugins/
├── rsi/                              # General plugin (bukan MemoryProvider!)
│   ├── __init__.py                   # Hooks: on_session_start, post_tool_call, on_session_end
│   ├── plugin.yaml
│   ├── compressor.py                 # Rule-based, dedup + priority sort
│   ├── lesson_extractor.py           # 16 heuristic patterns + tool fallback
│   └── lesson_store.py               # MEMORY.md-backed, no own DB
├── preflight/                        # Pre-flight spec validator
│   ├── __init__.py                   # validate() + format_goal_prompt()
│   └── plugin.yaml
└── memory/rsi/                       # 🔴 DELETED — salah extension point

plugins/memory/abelion_core/          # Tetap — LLM-driven deep reflection

docs/abelion/research/scripts/
├── run_experiment.py                 # Single entry point (--tasks, --max-iter, --base-url, --provider)
├── rsi_extractor.py                  # v2: actionable heuristic patterns
├── rsi_validator.py                  # Single validator (merge dari rsl_validator)
├── tasks.py / tasks_hard.py          # 20 + 20 benchmark tasks
├── analyze_results.py                # efficiency_score + t-test
├── status.py                         # Live status tool (baru!)
├── data/
│   ├── experiment_v4.csv             # 180 rows (v4 — final)
│   └── archive/                      # v1, v2, v3 data

docs/specs/rsi/
├── PRD.md                            # Product Requirements Document
├── SRS.md                            # Software Requirements Spec
├── SDD.md                            # Software Design Document
└── Phase-2-Tasks.md                  # Task breakdown (belum full executed)
```

---

## 3. Yang Masih Pending

| Item | Priority | Notes |
|------|----------|-------|
| **Tuning validated RSI (C)** | 🔴 | Confidence threshold 0.6 → 0.3-0.4. C underperform karena terlalu ketat. |
| **Plugin integrasi** | 🟡 | `plugins/rsi/` + `plugins/preflight/` butuh di-register di config Hermes |
| **Pre-flight jadi intercept /goal** | 🟡 | Saat ini pure logic. Butuh wiring ke `/goal` handler. |
| **Replace completion rate → FASR + entropy** | 🟡 | Kode siap di `analyze_results.py`? Cek dulu. |
| **Phase 2 experiment (paper-grade)** | 🟡 | Butuh API key dengan kredit untuk model lebih baik (gpt-4o-mini, claude-sonnet-4) |
| **Phase 3: tulis paper** | 🟢 | Paling akhir. Data cukup untuk workshop paper 4-6 halaman. |

---

## 4. Cara Lanjut di Sesi Berikutnya

```bash
# 1. Pull latest
git checkout research
git pull origin research

# 2. Status experiment terakhir
source .venv/bin/activate
python3 docs/abelion/research/scripts/status.py

# 3. Lihat hasil
python3 docs/abelion/research/scripts/analyze_results.py \
  docs/abelion/research/scripts/data/experiment_v4.csv

# 4. Plugin RSI (butuh Hermes running untuk test)
# Aktifkan di config.yaml:
# memory:
#   provider: rsi
```
