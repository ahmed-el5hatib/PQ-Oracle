# PQ-Oracle 🛡️
> **An Adaptive Architecture for Cost-Aware Post-Quantum Signature Aggregation in DeFi Oracle Networks**

[![Paper Target](https://img.shields.io/badge/Target-IEEE%20Access-blue.svg)](https://ieeeaccess.ieee.org/)
[![Status](https://img.shields.io/badge/Status-Draft%20v1%20%7C%20Phase%201%20Complete-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)

---

## 📌 Abstract / Overview
Blockchain oracle networks (e.g., Chainlink, Pyth) push signed price updates at high frequencies. Transitioning to Post-Quantum Cryptography (PQC) introduces a major bottleneck: **increased signature size, public key size, and verification costs**.

`PQ-Oracle` proposes a cost-aware, dynamic architecture that evaluates and switches between PQC signature aggregation techniques and static primitives based on real-time gas costs, latency SLAs, and security levels.

---

## 📊 Phase 1 Baseline Microbenchmarks (Applied Results)

Below are the empirical benchmarks collected locally using `liboqs`, `cryptography` (secp256k1), and `py_ecc` (BLS12-381).

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

### Key Findings:
- **Falcon-512** exhibits the fastest verification time (0.20 ms) and smallest PQC signature size (653 Bytes), but has a relatively slow key generation time.
- **ML-DSA-44** offers fast signing and verification, but its signature size (2,420 Bytes) is **34x larger** than ECDSA.
- **SLH-DSA-128s** has the smallest public key (32 Bytes), but signature overhead (7,856 Bytes, **112x larger than ECDSA**) makes naive on-chain submission cost-prohibitive.

---

## 📈 Visual Trade-off Analysis

![Phase 1 Comparison](results/pq_oracle_baseline_comparison.png)

---

## 🛠 Project Structure

```
PQ-Oracle/
├── PQ-Oracle_Proposal_and_Benchmark_Plan.md   # Core Research Proposal & Gap Analysis
├── README.md                                  # Repository overview & benchmark tables
├── scripts/
│   └── benchmark_phase1.py                    # Microbenchmarking harness (Python)
└── results/
    ├── pq_oracle_baseline_results.csv         # Raw benchmark data
    └── pq_oracle_baseline_comparison.png     # Generated trade-off chart
```

---

## 🚀 Reproduction / How to Run

### Requirements
- Python 3.10+
- `liboqs-python` (`liboqs` 0.15.0/0.16.0)
- `cryptography`, `py_ecc`, `matplotlib`

```bash
# Run Phase 1 baseline microbenchmarks
python scripts/benchmark_phase1.py
```

---

## 📝 Roadmap & Next Steps
- [x] **Phase 1:** Baseline Microbenchmarks (ECDSA, BLS, ML-DSA, Falcon, SLH-DSA).
- [ ] **Phase 2:** N-of-M Oracle Consensus Simulator & Aggregation Model.
- [ ] **Phase 3:** EVM On-Chain Gas Cost Measurement & Verification Contracts.
- [ ] **Phase 4:** Adaptive Scheme-Selection Policy Layer.
- [ ] **Phase 5:** Publication Draft Preparation for IEEE Access.
