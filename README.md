# PQ-Oracle 🛡️
> **An Adaptive Architecture for Cost-Aware Post-Quantum Signature Aggregation in DeFi Oracle Networks**

[![Paper Target](https://img.shields.io/badge/Target-IEEE%20Access-blue.svg)](https://ieeeaccess.ieee.org/)
[![Status](https://img.shields.io/badge/Status-Draft%20v1%20%7C%20Phase%201%20%26%202%20Complete-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)

---

## 📌 Abstract / Overview
Blockchain oracle networks (e.g., Chainlink, Pyth) push signed price updates at high frequencies. Transitioning to Post-Quantum Cryptography (PQC) introduces a major bottleneck: **increased signature size, public key size, and verification costs**.

`PQ-Oracle` proposes a cost-aware, dynamic architecture that evaluates and switches between PQC signature aggregation techniques and static primitives based on real-time gas costs, latency SLAs, and security levels.

---

## 📊 Phase 1 Baseline Microbenchmarks

Empirical benchmarks collected locally using `liboqs`, `cryptography` (secp256k1), and `py_ecc` (BLS12-381).

| Category | Algorithm | Security Level | Public Key Size (Bytes) | Signature Size (Bytes) | Keygen Time (ms) | Sign Time (ms) | Verify Time (ms) |
|---|---|---|---|---|---|---|---|
| **Classical Baseline** | `ECDSA (secp256k1)` | Classical 128-bit | 88 B | **70 B** | 0.50 ms | 0.54 ms | 0.44 ms |
| **Classical Baseline** | `BLS12-381` | Classical 128-bit | **48 B** | 96 B | 0.38 ms | 87.48 ms | 331.65 ms |
| **PQ - Lattice** | `ML-DSA-44` | NIST Level 2 | 1,312 B | 2,420 B | 0.51 ms | 1.22 ms | 0.37 ms |
| **PQ - Lattice** | `ML-DSA-65` | NIST Level 3 | 1,952 B | 3,309 B | 0.64 ms | 1.69 ms | 0.61 ms |
| **PQ - Lattice** | `ML-DSA-87` | NIST Level 5 | 2,592 B | 4,627 B | 1.05 ms | 2.52 ms | 0.99 ms |
| **PQ - Lattice** | `Falcon-512` | NIST Level 1 | 897 B | 653 B | 28.70 ms | 1.86 ms | **0.20 ms** |
| **PQ - Lattice** | `Falcon-1024` | NIST Level 5 | 1,793 B | 1,270 B | 71.89 ms | 3.69 ms | 0.39 ms |
| **PQ - Hash-based** | `SLH-DSA-SHA2-128s` | NIST Level 1 | 32 B | 7,856 B | 422.58 ms | 3,229.40 ms | 3.44 ms |

---

## 🌐 Phase 2 N-of-M Oracle Consensus Aggregation Simulation

Simulated $N$-of-$M$ Oracle network price updates across node counts $N \in \{5, 11, 21, 31, 51\}$.

### Aggregation Impact at $N=21$ Oracle Consensus Nodes

| Algorithm | Category | Unaggregated Payload (KB) | Aggregated Payload (KB) | **Payload Reduction (%)** | Unagg Verify (ms) | Agg Verify (ms) |
|---|---|---|---|---|---|---|
| `ECDSA (secp256k1)` | Classical | 1.55 KB | 1.55 KB | 0.00 % | 9.24 ms | 6.47 ms |
| `BLS12-381` | Classical | 2.10 KB | **0.18 KB** | **91.43 %** | 6,964 ms | 550 ms |
| `ML-DSA-44` | PQ - Lattice | 50.90 KB | **3.07 KB** | **93.98 %** | 7.77 ms | 0.78 ms |
| `ML-DSA-65` | PQ - Lattice | 69.57 KB | 3.96 KB | **94.32 %** | 12.81 ms | 1.28 ms |
| `ML-DSA-87` | PQ - Lattice | 97.25 KB | 5.27 KB | **94.58 %** | 20.79 ms | 2.08 ms |
| `Falcon-512` | PQ - Lattice | 13.80 KB | **1.44 KB** | **89.57 %** | 4.20 ms | **0.38 ms** |
| `Falcon-1024` | PQ - Lattice | 26.75 KB | 2.06 KB | **92.32 %** | 8.19 ms | 0.73 ms |
| `SLH-DSA-128s` | PQ - Hash | 165.06 KB | 9.06 KB | **94.51 %** | 72.24 ms | 8.73 ms |

### Key Phase 2 Takeaways:
1. Without signature aggregation, PQC payloads scale linearly ($N \times \text{SigSize}$), causing **ML-DSA-44 to consume 50.9 KB per price update at N=21 nodes** (financially unviable on EVM).
2. Applying PQC aggregation / sublinear batch verification reduces payload size by **up to ~94%**, bringing ML-DSA-44 down to **3.07 KB** and Falcon-512 down to **1.44 KB**.

---

## 📈 Visual Analytics

### Phase 1: Microbenchmark Trade-offs
![Phase 1 Comparison](results/pq_oracle_baseline_comparison.png)

### Phase 2: Oracle Consensus Aggregation Simulation
![Phase 2 Simulation](results/pq_oracle_network_simulation.png)

---

## 🛠 Project Structure

```
PQ-Oracle/
├── PQ-Oracle_Proposal_and_Benchmark_Plan.md   # Core Research Proposal & Gap Analysis
├── README.md                                  # Repository overview & benchmark tables
├── scripts/
│   ├── benchmark_phase1.py                    # Microbenchmarking harness (Python)
│   └── simulate_oracle_network.py             # Phase 2 N-of-M consensus simulator
└── results/
    ├── pq_oracle_baseline_results.csv         # Raw microbenchmark data
    ├── pq_oracle_baseline_comparison.png     # Phase 1 trade-off chart
    ├── pq_oracle_simulation_results.csv       # Phase 2 simulation data
    └── pq_oracle_network_simulation.png       # Phase 2 aggregation chart
```

---

## 🚀 Reproduction / How to Run

```bash
# Run Phase 1 baseline microbenchmarks
python scripts/benchmark_phase1.py

# Run Phase 2 N-of-M Oracle Consensus simulation
python scripts/simulate_oracle_network.py
```

---

## 📝 Roadmap & Next Steps
- [x] **Phase 1:** Baseline Microbenchmarks (ECDSA, BLS, ML-DSA, Falcon, SLH-DSA).
- [x] **Phase 2:** N-of-M Oracle Consensus Simulator & Aggregation Model.
- [ ] **Phase 3:** EVM On-Chain Gas Cost Measurement & Verification Contracts.
- [ ] **Phase 4:** Adaptive Scheme-Selection Policy Layer.
- [ ] **Phase 5:** Publication Draft Preparation for IEEE Access.
