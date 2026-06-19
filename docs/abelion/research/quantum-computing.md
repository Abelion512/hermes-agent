# Quantum Computing Research Brief
### compiled 2026-06-15 | ASA Research Division

---

## 1. Fundamentals

### Qubits
The quantum bit (qubit) is the basic unit of quantum information. Unlike classical bits (0 or 1), a qubit exists in a **superposition** of both states simultaneously, represented as |ψ⟩ = α|0⟩ + β|1⟩ where |α|² + |β|² = 1. Upon measurement, the superposition collapses to either |0⟩ or |1⟩ with probabilities |α|² and |β|².

### Core Principles
- **Superposition**: Qubits can be in multiple states at once, enabling parallel computation paths.
- **Entanglement**: Two qubits can be correlated such that the state of one instantly determines the other, regardless of distance. This enables quantum algorithms to explore solution spaces in ways classical systems cannot.
- **Interference**: Quantum states constructively or destructively interfere, allowing algorithms to amplify correct answers and cancel wrong ones.

### Quantum Gates & Circuits
- **Single-qubit gates**: Hadamard (H), Pauli-X/Y/Z, Phase (S, T), Rotation gates (Rx, Ry, Rz)
- **Two-qubit gates**: CNOT (controlled-NOT), CZ (controlled-Z) — these are the primary error source
- **Toffoli gate**: Universal reversible gate, important for fault-tolerant circuits
- Quantum gates are unitary (reversible), unlike classical AND/OR gates.

---

## 2. Hardware Approaches

### 2.1 Superconducting Qubits (IBM, Google)
- **How it works**: Josephson junctions cooled to ~15 millikelvin (colder than outer space) in dilution refrigerators. Qubits are microwave-controlled.
- **Pros**: Fast gate times (~10-50ns), mature fabrication (leverages semiconductor industry), high qubit counts
- **Cons**: Short coherence times (~100-300μs), requires extreme cooling, nearest-neighbor connectivity on 2D grids
- **State of the art (2026)**:
  - Google Willow: 105 physical qubits, 99.88% two-qubit gate fidelity, first below-threshold error correction (Dec 2024)
  - IBM Heron R2: 156 physical qubits; IBM Kookaburra: ~4,158 physical qubits (qLDPC architecture)
  - IBM Quantum System Two: modular architecture with L-couplers for inter-chip communication

### 2.2 Trapped Ion Qubits (IonQ, Quantinuum)
- **How it works**: Individual ions (e.g., Ytterbium, Barium) trapped in electromagnetic fields, manipulated with lasers.
- **Pros**: Highest gate fidelities (99.99% 2Q claimed by IonQ), all-to-all connectivity, long coherence times (seconds to minutes)
- **Cons**: Slower gate times (~10-100μs), scaling challenges, complex laser control systems
- **State of the art**:
  - Quantinuum Helios: 98 physical qubits, 48 verified logical qubits (color code, Nov 2025)
  - IonQ: #AQ64 algorithm qubit benchmark, pending $1.8B SkyWater acquisition

### 2.3 Photonic Qubits (PsiQuantum, Xanadu, Photonic)
- **How it works**: Photons (light particles) as qubits, manipulated with beam splitters, phase shifters, and photon detectors.
- **Pros**: Room temperature operation, natural for quantum communication, long coherence (photons don't decohere easily)
- **Cons**: Photon loss, probabilistic entanglement, requires massive multiplexing for fault tolerance
- **State of the art**:
  - PsiQuantum Omega: 99.98% 1Q / 99.95% 2Q fidelity, targeting million-qubit system
  - Photonic SHYPS codes: breakthrough QLDPC implementation for photonic "Entanglement First" architecture

### 2.4 Neutral Atom Qubits (Atom Computing, QuEra, Pasqal)
- **How it works**: Individual atoms trapped in optical tweezers (focused laser beams), excited to Rydberg states for interactions.
- **Pros**: Flexible/reconfigurable qubit arrangements, good coherence, natural for molecular simulation
- **Cons**: Higher error rates than trapped ions, complex optical setups
- **State of the art**:
  - Atom Computing Phoenix: 1,225 physical qubits, ~24 logical qubit demonstration
  - QuEra: ~48 logical qubit demonstration
  - Pasqal Orion: 100 qubits, first molecular-biology-class task on quantum hardware (hydration water placement with Qubit Pharmaceuticals)

### 2.5 Topological Qubits (Microsoft)
- **How it works**: Uses exotic particles called Majorana fermions. Topological properties inherently protect quantum information from local noise.
- **Pros**: Theoretically much lower error rates, could scale with far fewer physical qubits
- **Cons**: Experimental evidence contested (APS physicists called 2025 Nature paper "underwhelming")
- **Status**: Microsoft Majorana 1 chip announced Feb 2025, but stopped short of confirming topological qubits

### 2.6 Quantum Annealing (D-Wave)
- **How it works**: Special-purpose quantum optimizer, not a universal quantum computer. Uses quantum tunneling to find global minima of optimization landscapes.
- **Status**: Ford Otosan cut scheduling from 30 min to <5 min in production; ~5,000+ qubits in Advantage2 system

---

## 3. Quantum Error Correction

This is the **central bottleneck** for all quantum computing approaches.

### The Problem
Physical qubits have error rates of ~0.01-1% per operation. Useful algorithms need error rates of ~10⁻¹⁵ or better. The gap: ~12-15 orders of magnitude.

### Surface Code (Current Standard)
- Encodes 1 logical qubit in a 2D grid of physical qubits
- **Threshold**: Physical error rates below ~1% enable error suppression
- **Overhead**: ~1,000-10,000 physical qubits per logical qubit (practical algorithms need millions of physical qubits)
- **Google Willow milestone (Dec 2024)**: First demonstration of below-threshold error correction — as code distance increased from 3×3 → 5×5 → 7×7, error rate was suppressed by ~2x at each step (exponential suppression). Logical qubit lifetime exceeded best physical qubit by 2.4x.
- Distance-7 code achieved 0.143% error per cycle

### qLDPC Codes (Next Generation)
- **Quantum Low-Density Parity Check**: Can encode multiple logical qubits with far less overhead
- Potentially 5-20x reduction in physical qubits per logical qubit
- **Challenge**: Requires non-local connectivity (hard for 2D superconducting chips)
- IBM pursuing qLDPC with Kookaburra processor (low-loss wiring layer)
- Photonic SHYPS codes demonstrate efficient qLDPC logic implementation

### Other Approaches
- **Color codes** (Quantinuum): 48 verified logical qubits using trapped-ion all-to-all connectivity
- **Bosonic codes** (Alice & Bob): Cat qubits with built-in error bias
- **Floquet codes**: Time-dynamic codes for defective-qubit devices

### Decoding Bottleneck
Real-time decoders must process error syndromes at microsecond latency. Google's AlphaQubit (transformer-based AI decoder) achieved real-time decoding on Willow at ~3.7μs. GPU-accelerated decoders (NVIDIA DGX Quantum) are being explored.

### Timeline Reality
- **2025-2026**: Below-threshold logical qubits demonstrated (Google, IBM, Quantinuum, IonQ)
- **2026-2029**: IBM targets verified quantum advantage by end-2026, fault tolerance by 2029
- **2030+**: Millions of physical qubits needed for cryptographically relevant applications

---

## 4. Algorithms

### Foundational Algorithms
- **Shor's Algorithm**: Integer factorization in polynomial time. Would break RSA-2048. Requires ~4M logical qubits (estimated). Not near-term.
- **Grover's Algorithm**: Unstructured search, quadratic speedup (√N vs N). Less dramatic than Shor's but more broadly applicable.
- **Quantum Simulation**:模拟量子系统本身 — Feynman's original motivation. Chemistry, materials science.

### NISQ-Era Algorithms (Near-Term)
- **VQE (Variational Quantum Eigensolver)**: Hybrid quantum-classical for molecular ground state energy. Used by Biogen/Accenture for drug discovery molecular comparison.
- **QAOA (Quantum Approximate Optimization Algorithm)**: Combinative optimization. Applied to logistics (D-Wave/Walmart), portfolio optimization.
- **QSVM (Quantum Support Vector Machine)**: Kernel methods with quantum-enhanced feature spaces. ~90% validation scores reported for materials science tasks.

### Recent Research Highlights (2025-2026)
- **Quantum Echoes** (Google, Oct 2025): 13,000× faster on Willow vs classical supercomputer. Applied to molecular geometry measurement — step toward NMR-based drug discovery. Independently reproducible.
- **FeMo-cofactor** (Zhai et al., Chan group, Jan 2026): Classical solution to the 76-orbital/152-qubit nitrogenase active site problem. Shows quantum advantage frontier has moved — classical methods keep getting better.
- **IBM Group Theory Algorithm** (Oct 2025): New quantum algorithm using non-Abelian Fourier transform, demonstrating substantial speedup for symmetry-related problems.
- **Quantum Machine Learning Review** (2025-2026): QSVM, QNN, and quantum kernel methods show promise for small-sample learning, molecular modeling, and materials science.

---

## 5. Cloud Quantum Platforms

### Major Platforms
- **IBM Quantum (Qiskit 2.0)**: Largest fleet — Eagle (127Q), Condor (1,121Q), Heron R2 (156Q). Free tier available. Open-source SDK.
- **Google Quantum AI (Cirq)**: Willow (105Q), research-focused. Limited public access.
- **Amazon Braket**: Multi-hardware access (IonQ, QuEra, OQC, Rigetti). Added native Qiskit 2.0 support Dec 2025.
- **Azure Quantum**: Microsoft's platform, partnered with Quantinuum, IonQ, Pasqal.
- **IonQ Quantum Cloud**: Direct access to trapped-ion systems.
- **D-Wave Leap**: Quantum annealing cloud. Production deployments (Ford, HSBC).

### Developer Tools
- Qiskit (IBM), Cirq (Google), PennyLane (Xanadu), PyQuil (Rigetti), Q# (Microsoft)
- All Python-based. Open-source, vendor-neutral ecosystem.

---

## 6. Industry Landscape (2025-2026)

### Top Players by Category
| Rank | Company | Type | Key Metric |
|------|---------|------|-----------|
| 1 | IBM Quantum | Superconducting | Scale + ecosystem (Qiskit, 1000+ Q fleet) |
| 2 | Google Quantum AI | Superconducting | Error correction lead (Willow, Quantum Echoes) |
| 3 | IonQ | Trapped ion | Fidelity record (99.99% 2Q), $130M revenue |
| 4 | Quantinuum | Trapped ion | 48 logical qubits (color code), ~$20B IPO |
| 5 | PsiQuantum | Photonic | Million-qubit target, 99.98% 1Q fidelity |
| 6 | D-Wave | Annealing | Production deployments, 5000+ qubits |

### Geographic Landscape
- **US**: Leads in commercialization (IBM, Google, IonQ, PsiQuantum, QuEra, D-Wave)
- **China**: ~$15B national investment, quantum satellites/communication networks, targeting 1000+ qubit system by 2027
- **EU**: €1B Quantum Flagship program, focus on sovereign quantum stack (Pasqal/France, IQM/Finland, AQT/Austria)
- **UK**: National Quantum Computing Centre, Quantinuum (Honeywell spinout)
- **Canada**: Xanadu (photonic/PennyLane), early D-Wave history

### Funding
- Global Q1-Q2 2026: ~$17.3B cumulative investment
- Quantinuum S-1 filed Jan 2026 (~$2B raised, targeting IPO at ~$20B valuation)
- IonQ 2025 GAAP revenue: $130M (202% YoY growth)

### First Production Deployments
- **Ford Otosan**: D-Wave quantum annealing reduced scheduling from 30 min → <5 min
- **HSBC**: 34% improvement in bond trading predictions using IBM Heron
- **Q-CTRL**: 50-100× advantage in GPS-denied navigation
- **Biogen × Accenture**: Quantum molecular comparison matching/exceeding classical methods

---

## 7. Current Limitations & Realistic Timelines

### Technical Barriers
1. **Physical Qubit Quality**: Error rates still too high for deep circuits (though below threshold now)
2. **Qubit Count**: 100s of physical qubits → need millions for cryptographic applications
3. **Connectivity**: 2D nearest-neighbor (superconducting) limits algorithmic flexibility
4. **Cryogenics**: Superconducting qubits need 15mK — expensive, complex infrastructure
5. **Classical Competition**: Classical methods keep improving (see FeMo-coef result — quantum advantage target keeps moving)
6. **NISQ Limitations**: Without full error correction, algorithm depth constrained to ~100-1000 gates

### Realistic Expectations

| Milestone | Time Horizon | Status |
|-----------|-------------|--------|
| Below-threshold logical qubit | 2024-2025 | ✅ Achieved (Google, Quantinuum, IBM) |
| 100 logical qubits | 2026-2028 | In progress (Quantinuum at 48) |
| Useful quantum advantage (specific problems) | 2026-2028 | IBM targets end-2026 |
| 1,000 logical qubits | 2028-2030 | Roadmap stage |
| Fault-tolerant universal QC | 2030+ | IBM roadmap: 2029 |
| Breaking RSA-2048 | 2035+ (est.) | ~4M logical qubits needed |
| Fully error-corrected QC | 2030s | Dependent on qLDPC & boson codes |

### What Quantum Computing is NOT Good At
- General computing (word processing, web browsing, etc.)
- Simple math
- Tasks that parallelize well on GPUs already
- Most current ML training workloads

---

## 8. Relevance to AI/ML

### Quantum Machine Learning (QML)

#### Hybrid Approaches (Near-Term Reality)
- **Variational Quantum Circuits (VQC)**: Parameterized quantum circuits with classical optimizers. Quantum layer extracts features, classical layer classifies. Used in drug discovery, anomaly detection.
- **Quantum Kernel Methods**: QSVM with quantum-enhanced feature spaces. Promising for small-sample learning where classical kernels struggle.
- **Quantum Neural Networks (QNN)**: Circuit-based models with trainable parameters. ~90% accuracy on materials science regression/classification tasks.

#### Fully Quantum Approaches (Long-Term)
- **Quantum GANs**, **Quantum VAEs**: Generative models using quantum circuits for molecule/compound generation
- **Quantum Reinforcement Learning**: Quantum speedups for exploration in large state spaces
- **HHL Algorithm**: Linear system solver with exponential speedup — but requires fault-tolerant hardware

### Quantum-Classical AI Synergies
- **AlphaQubit** (Google): Transformer-based AI decoder for quantum error correction demontraining at microsecond latency
- **Quantum-inspired optimization**: Tensor network methods running on classical hardware but borrowing quantum math
- **NVIDIA DGX Quantum**: GPU-accelerated quantum simulation and GPU-based real-time decoders

### Current QML Challenges
1. **Barren plateaus**: Training landscapes become exponentially flat as qubit count grows
2. **Data encoding bottleneck**: Loading classical data into quantum states (state preparation) remains expensive
3. **Noise**: NISQ hardware noise limits circuit depth and model complexity
4. **Proven advantage elusive**: For most ML tasks, classical methods still match or beat quantum approaches. Genuine quantum advantage in ML remains mostly theoretical.

### AI for Quantum (Reverse Direction)
This is where the most concrete near-term value lies:
- AI decoders for quantum error correction (Google AlphaQubit)
- ML for qubit calibration and optimization
- Neural network decoders for surface codes
- AI-assisted quantum circuit compilation and optimization

---

## 9. Reading List (Key Papers & Sources)

### Landmark Papers
1. Google Quantum AI (2025). "Quantum error correction below the surface code threshold." Nature 638, 920-926. The Willow paper.
2. Zhai et al. (2026). "Classical Solution of the FeMo-cofactor Model." arXiv:2601.04621
3. Preskill (2018). "Quantum Computing in the NISQ era and beyond." The paper that coined "NISQ."
4. Shor (1995). "Scheme for reducing decoherence in quantum computer memory." The original QEC paper.
5. Kitaev (1997). "Fault-tolerant quantum computation by anyons." Topological QC foundation.

### Surveys & Reviews
- Quanta 15 (2026): "Quantum Machine Learning: A Review of Hybrid Classical-Quantum Approaches" (Prajapati & Prajapati)
- Nature Methods (2025): "Quantum machine learning: A comprehensive review" (ScienceDirect)
- PennyLane blog: Top Quantum Algorithms Papers, Winter 2026 edition

### Tracking the Field
- Quantum Navigator database (1,156 companies tracked)
- Quantum Zeitgeist logical qubit leaderboard
- IBM Quantum Advantage Tracker (with Algorithmiq & Flatiron Institute)

---

## 10. Key Takeaways

1. **Error correction is the bottleneck — and it's starting to crack.** Google's Willow demonstrated below-threshold error suppression. Quantinuum showed 48 logical qubits. This is real, verifiable progress.

2. **Physical qubit count is a misleading metric.** Quality (fidelity, connectivity, coherence) matters more. 50 all-to-all connected trapped ions > 1,000 poorly connected superconducting qubits for many tasks.

3. **Quantum advantage exists for specific problems** (Google Quantum Echoes: 13,000×), but **practical commercial advantage** is still emerging (Ford, HSBC case studies are promising but narrow).

4. **The "quantum winter" narrative is wrong — but so is quantum hype.** The field is in an inflection point. Not "quantum computers solve everything" and not "quantum is fake." The truth: narrow, verifiable milestones being hit at accelerating pace.

5. **AI-quantum convergence is the most interesting near-term direction.** AI for quantum (decoders, calibration) + quantum for AI (sampling, optimization) = productive hybrid systems that don't require fault-tolerant hardware.

6. **Timeline: useful quantum advantage in 2-4 years, fault-tolerant in 4-8 years, cryptographically relevant in 10-15 years.** Anyone telling you differently is selling something.
