# Paper Summary: Self-Harness (2606.09498)

> **Harnesses That Improve Themselves** — Zhang, Zhang, Li, Zhang, Chen, Zhang, Bai, Hu (2026-06-08)

## Core Idea

LLM-based agent improves its **own operating harness** (system prompt, tools, memory config) without human engineers or stronger external agents. Three-stage iterative loop.

## The Loop

```
1. Weakness Mining
   ├─ Execute task with current harness
   ├─ Collect execution traces (success/failure)
   └─ Identify model-specific failure patterns

2. Harness Proposal
   ├─ Generate candidate harness modifications
   ├─ Diverse (different approaches per failure)
   └─ Minimal (smallest change that could fix it)

3. Proposal Validation
   ├─ Run regression test suite with candidate harness
   ├─ Accept if pass rate improves
   └─ Reject if regression detected
```

## Results (Terminal-Bench-2.0)

| Model | Before | After | Δ |
|-------|--------|-------|---|
| MiniMax M2.5 | 40.5% | 61.9% | +21.4% |
| Qwen3.5-35B-A3B | 23.8% | 38.1% | +14.3% |
| GLM-5 | 42.9% | 57.1% | +14.2% |

## Relevance to RSI

### Aligns
- Iterative extraction from execution traces → mirrors RSI loop
- No retraining, no stronger external model → matches "no fine-tuning" constraint
- Regression testing before accepting changes → validates RQ4 (validation approach)

### Differs
- Modifies harness (prompts, tools, memory config) — we inject lessons into existing harness
- Targets single-model — we target multi-persona isolation
- Uses regression test suite — we use cause-effect + tool-mention + conflict detection

### Gaps Not Addressed
- Multi-persona isolation
- Cache-aware deployment
- Cross-session persistence (Self-Harness is within-session)
