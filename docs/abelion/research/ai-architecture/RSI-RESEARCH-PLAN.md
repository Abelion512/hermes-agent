# RSI Research Plan

> Recurrent Self-Improvement — Agent yang belajar dari experience, bukan cuma dari pre-trained weights.

## Status: Phase 1 — Foundation

## Core Thesis

Agent yang bisa self-improve dari pengalaman (success/failure) selama runtime, bukan bergumpul on pre-trained knowledge saja. Inspired by AlphaGo Zero → experience-driven knowledge base.

## Existing Assets

- `RSI_EXPERIENTIAL_LEARNING_ARCHITECTURE.md` — base spec (memory isolation, multi-agent hierarchy, fault tolerance)
- `RSI_EXPERIENTIAL_LEARNING_ARCHITECTURE_ID.md` — Indonesian version
- `DeepSeek_record.md` — audit notes from earlier research

## Research Questions

1. **RSI Loop** — gimana cara agent collect experience → extract lesson → apply next time?
2. **Memory Architecture** — persona-based isolation vs shared knowledge, trade-nya apa?
3. **Multi-Agent Hierarchy** — CEO → Division → Worker, gimana failure propagation-nya?
4. **Experiential Learning** — bedanya sama RL? bedanya sama fine-tuning? kenapa pakai RSI?

## Study Plan (2h/day)

### Week 1: Survey
- [ ] Baca RSImm paper (jika ada) atau related work: Reflexion, ReAct,~
- [ ] Baca **Claude Constitutional AI** paper (Anthropic approach ke safety via experience)
- [ ] Identify gap/positioning: RSI vs existing approaches
- [ ] **Output:** literature review notes

### Week 2: Architecture Design
- [ ] Compare memory approaches: profile-based (Hermes) vs project-based vs global
- [ ] Map failure modes di multi-agent setup
- [ ] Design RSI loop cadangan untuk Hermes agent
- [ ] **Output:** architecture diagram (updated dari existing spec)

### Week 3: Prototype (Gap → Product)
- [ ] Implement simple RSI loop di Hermes: task execution → extract lesson → store memory → inject next session
- [ ] Test: run task, deliberately fail, run again. Harusnya second run lebih baik.
- [ ] **Output:** working prototype + demo notes

### Week 4: Write-up
- [ ] Synthesize findings
- [ ] Write blog post / paper draft
- [ ] **Output:** publishable write-up

## Target Output

1. **Working RSI loop** implementation (bisa di-demo)
2. **Write-up** yang bisa di-submit ke blog/conference
3. **Course material reference** — buat matkul AI/ML yang loe ambil
4. **S2 portfolio piece** — buat application ke Tsinghua/Zhejiang

## Course Connection

Kalo ada matkul yang bersinggungan:
- Reinforcement Learning → RSI loop = reward dari task success/failure
- Multi-Agent Systems → CEO/Division/Worker hierarchy
- Knowledge Representation → memory architecture, semantic isolation
- NLP → experience extraction dari task execution traces

## Key Papers to Read (Priority)

1. **Reflexion** (Shinn et al., 2023) — agent reflects on failure → verbal reinforcement
2. **ReAct** (Yao et al., 2022) — reasoning + acting loop
3. **Constitutional AI** (Bai et al., 2022) — Anthropic's approach to alignment via experience
4. **SPIN** (React) — self-play iterative improvement
5. **AlphaGo Zero** (Silver et al., 2017) — experience-driven mastery

---

Created: 2026-06-13
Next review: 2026-06-17 (end of Week 1)
