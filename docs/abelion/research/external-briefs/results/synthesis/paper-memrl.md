# Paper Summary: MemRL (2601.03192)

> **Self-Evolving Agents via Runtime Reinforcement Learning on Episodic Memory** — Zhang et al. (12 authors, 2026-01-06)

## Core Idea

Non-parametric approach that evolves via **reinforcement learning on episodic memory**. Decouples stable reasoning from plastic memory — no weight updates needed.

## Mechanism

### Two-Phase Retrieval
1. **Phase 1**: Broad semantic search over episodic memory
2. **Phase 2**: Utility-based re-ranking using environmental feedback (Q-learning style)

### Key Design
- Stable reasoning module (frozen LLM) — never updated
- Plastic memory module (episodic buffer) — continuously updated via RL
- Non-parametric — no gradient descent, no weight updates
- Noise filtering through Two-Phase Retrieval

## Results

| Benchmark | MemRL vs SOTA |
|-----------|---------------|
| HLE | Outperforms |
| BigCodeBench | Outperforms |
| ALFWorld | Outperforms |
| Lifelong Agent Bench | Outperforms |

Code: github.com/MemTensor/MemRL

## Relevance to RSI

### Aligns
- Non-parametric (no weight updates) → matches "no fine-tuning" constraint
- Episodic memory + RL utility ranking → closest to our confidence tracking
- Two-Phase Retrieval → similar to our tiered retrieval design
- Decouples reasoning from memory → matches memory_store.py architecture

### Differs
- Uses RL (Q-values) — we use simpler confidence heuristics
- Single-agent — we target multi-persona isolation
- Requires environmental reward signal — we derive lessons from error patterns

### What We Can Adopt
- **Utility-based confidence decay** (already in memory_store.py: confidence *= 0.99/day)
- **Two-phase retrieval pattern** (FTS5 → synonym expansion → cross-persona)
- **Confidence thresholding** for lesson injection decisions
