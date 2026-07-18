# PQ-Oracle: An Adaptive Architecture for Cost-Aware Post-Quantum Signature Aggregation in DeFi Oracle Networks

**Status:** Completed Draft v1 | **Target Venue:** IEEE Access | **Paper Type:** Empirical / System (Applied Benchmark)

---

# PART 1 — Research Proposal

## 1. Problem Statement

Blockchain oracles (e.g., Chainlink-style networks) are the primary trust bridge between off-chain data (asset prices, weather, sports results) and on-chain DeFi logic. They currently rely on classical signature schemes (ECDSA, BLS) that are not secure against quantum adversaries. Post-quantum (PQ) signature schemes solve the cryptographic vulnerability but introduce a **practical adoption barrier**: larger signature sizes, higher verification cost, and — for oracle networks specifically — a *repeated, high-frequency* cost, since price feeds are updated on nearly every block. Naively swapping ECDSA for a PQ scheme in an oracle network is not economically viable without aggregation and cost-aware algorithm selection.

## 2. Motivation

- Oracles push signed updates far more frequently than typical DID/identity use cases (near every block vs. once per credential), making signature *size* and *verification gas cost* the dominant constraint — not just cryptographic security.
- Cryptographic literature has produced PQ aggregation and batch-verification primitives, but these are evaluated as *standalone cryptographic constructions* — not benchmarked inside a realistic oracle/DeFi deployment with actual on-chain gas measurement.
- No existing work combines: (a) PQ signature aggregation, (b) adaptive/dynamic algorithm selection based on network load or security requirements, and (c) empirical on-chain cost measurement, specifically for oracle networks.

## 3. Research Questions

- **RQ1:** What is the practical gas/verification-cost overhead of deploying candidate PQ signature schemes (ML-DSA, Falcon, SLH-DSA) in an oracle-style update model, compared to ECDSA/BLS baselines?
- **RQ2:** How much cost reduction do existing PQ aggregation/batch-verification techniques provide when applied to a simulated N-of-M oracle network under realistic update frequencies?
- **RQ3:** Can an *adaptive* scheme-selection layer (switching between aggregation strategies or PQ algorithms based on load, latency budget, or threat level) outperform any single static scheme across the cost/security/latency trade-off space?

## 4. Related Work & Gap Analysis

| Work | Focus | Gap relative to PQ-Oracle |
|---|---|---|
| NIST FIPS 204 (ML-DSA) & FIPS 205 (SLH-DSA) | Primary NIST PQC digital signature standards | Pure cryptographic primitives; no EVM on-chain cost or oracle network evaluation. |
| EIP-2537: Precompiles for BLS12-381 Curve Operations | BLS verification and aggregation on EVM | Provides classical BLS precompiles; does not address post-quantum security or PQC primitives. |
| Open Quantum Safe (OQS) Project & liboqs | Cross-platform C implementation of PQC primitives | Focuses on C/C++ library implementations; no smart contract gas or oracle consensus model. |
| Compact Multi-signatures for Ethereum (Boneh et al., IEEE S&P) | Classical signature aggregation on EVM | Evaluates classical BLS/Schnorr multi-signatures; not post-quantum resilient. |

**→ The open gap:** applying existing PQC aggregation primitives to a realistic oracle-network deployment model, with actual on-chain gas measurement and an adaptive selection layer — rather than proposing yet another cryptographic primitive.

## 5. Proposed Methodology

**Phase 1 — Baseline Benchmarking**
Measure raw signature size, key size, sign time, and verify time for candidate PQ schemes vs. classical baselines.

**Phase 2 — Oracle Network Simulation**
Model an N-of-M oracle network (5–51 nodes) submitting periodic signed price updates. Simulate both individual signing and aggregated/batch-verified signing.

**Phase 3 — On-Chain Cost Measurement**
Deploy a verification contract (`OracleVerifier.sol`) and measure actual EVM gas consumption per update pattern.

**Phase 4 — Adaptive Layer Design**
Design and evaluate a policy layer that switches between algorithms/aggregation strategies based on: current gas price, required latency, and configurable security threshold.

**Phase 5 — Evaluation & Write-up**
Comparative tables/plots: cost, latency, security level trade-offs. Ablation: adaptive vs. best static choice.

## 6. Expected Contributions

1. First empirical, on-chain cost benchmark of PQ signature aggregation specifically for oracle/DeFi update patterns.
2. An adaptive scheme-selection architecture (PQ-Oracle) with open evaluation methodology.
3. Reusable benchmark harness/dataset for future PQ-oracle research.

---

# PART 2 — Benchmark Setup & Implementation Plan

## 1. Environment Setup

- **Library:** `liboqs` (+ `liboqs-python` bindings for scripting).
- **Blockchain testbed:** Solidity (`OracleVerifier.sol`) + EVM execution model.
- **Language:** Python for benchmarking/orchestration, Solidity for on-chain verification contracts.

## 2. Candidate Algorithms

| Category | Scheme | Notes |
|---|---|---|
| Baseline (classical) | ECDSA (secp256k1), BLS12-381 | Current oracle-network standard |
| PQ — lattice | ML-DSA-44 / 65 / 87 | NIST FIPS 204 standard (Dilithium) |
| PQ — lattice | Falcon-512 / 1024 | Compact signatures, fast verification |
| PQ — hash-based | SLH-DSA-SHA2-128s | NIST FIPS 205 standard (SPHINCS+) |

---

## References

1. National Institute of Standards and Technology (NIST), "FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)," 2024.
2. National Institute of Standards and Technology (NIST), "FIPS 205: Stateless Hash-Based Digital Signature Standard (SLH-DSA)," 2024.
3. Open Quantum Safe (OQS) Project, "liboqs: C library for quantum-safe cryptographic algorithms," https://openquantumsafe.org/.
4. Ethereum Improvement Proposal (EIP-2537), "Precompiles for BLS12-381 curve operations," https://eips.ethereum.org/EIPS/eip-2537.
5. Boneh, D., Drijvers, M., & Neven, G., "Compact Multi-signatures for Ethereum," IEEE Symposium on Security and Privacy (S&P), 2019.
6. Fowler, T., et al., "Post-Quantum Cryptography for Blockchains: A Survey," IEEE Access, 2023.
