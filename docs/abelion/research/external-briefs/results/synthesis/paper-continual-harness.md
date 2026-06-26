# Paper Summary: Continual Harness (2605.09998)

> **Online Adaptation for Self-Improving Foundation Agents** — Karten, Zhang, Upaa, Feng, Li, Shi, Jin, Vodrahalli (2026-05-11)

## Core Idea

Reset-free self-improving harness for embodied agents. Agent refines its own prompt, sub-agents, skills, and memory using past trajectory data — entirely without human intervention.

## Three Key Innovations

### 1. Gemini Plays Pokemon (GPP)
First AI system to complete Pokemon Blue, Yellow Legacy (hard mode), and Crystal undefeated. During hardest stages, agent began iterating on its own strategy via long-context memory — **emergent self-improvement signal**.

### 2. Continual Harness Algorithm
- **Reset-free** — adapts within a single run, no episode resets
- Alternates between: acting in environment ↔ refining own harness
- Richer refinement space than prompt-optimization (sub-agents, skills, memory)
- Draws on any past trajectory data

### 3. Online Process-Reward Co-Learning
- Open-source agent generates rollouts through refining harness
- Frontier teacher model relabels these rollouts
- Used to update the open-source model
- **No environment resets between training iterations**

## Results
- Substantially reduces button-press cost vs minimalist baseline
- Recovers majority of gap to hand-engineered expert harness
- Capability-dependent gains across frontier models
- Sustained in-game milestone progress on Pokemon Red

## Relevance to RSI

### Aligns
- Reset-free self-improvement → matches "lifelong learning" vision
- Agent refines own prompt, sub-agents, skills, memory → close to lesson injection
- Uses past trajectory data → matches execution trace approach
- Online adaptation without episode resets → our single-agent lifecycle

### Differs
- Embodied agent domain (Pokemon) — we target coding/shell tasks
- Co-learning loop needs frontier teacher — we avoid any external model
- Single-run focus — we target cross-session persistence (across days)

### Key Contribution
- **Demonstrates self-improvement signals emerge naturally** during agent execution — validates RSI direction
- Reset-free constraint stronger than we need, but proves feasibility
