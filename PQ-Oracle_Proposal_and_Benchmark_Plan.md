# PQ-Oracle: An Adaptive Architecture for Cost-Aware Post-Quantum Signature Aggregation in DeFi Oracle Networks

**Status:** Draft v1 | **Target Venue:** IEEE Access | **Paper Type:** Empirical / System (Applied Benchmark)

---

# PART 1 — Research Proposal

## 1. Problem Statement

Blockchain oracles (e.g., Chainlink-style networks) are the primary trust bridge between off-chain data (asset prices, weather, sports results) and on-chain DeFi logic. They currently rely on classical signature schemes (ECDSA, BLS) that are not secure against quantum adversaries. Post-quantum (PQ) signature schemes solve the cryptographic vulnerability but introduce a **practical adoption barrier**: larger signature sizes, higher verification cost, and — for oracle networks specifically — a *repeated, high-frequency* cost, since price feeds are updated on nearly every block. Naively swapping ECDSA for a PQ scheme in an oracle network is not economically viable without aggregation and cost-aware algorithm selection.

## 2. Motivation

- Oracles push signed updates far more frequently than typical DID/identity use cases (near every block vs. once per credential), making signature *size* and *verification gas cost* the dominant constraint — not just cryptographic security.
- Recent cryptographic literature (2025–2026) has produced PQ aggregation and batch-verification primitives (lattice-based aggregate signatures, sublinear batch verification for lattice relations), but these are evaluated as *standalone cryptographic constructions* — not benchmarked inside a realistic oracle/DeFi deployment with actual on-chain gas measurement.
- No existing work combines: (a) PQ signature aggregation, (b) adaptive/dynamic algorithm selection based on network load or security requirements, and (c) empirical on-chain cost measurement, specifically for oracle networks.

## 3. Research Questions

- **RQ1:** What is the practical gas/verification-cost overhead of deploying candidate PQ signature schemes (ML-DSA, Falcon, SLH-DSA) in an oracle-style update model, compared to ECDSA/BLS baselines?
- **RQ2:** How much cost reduction do existing PQ aggregation/batch-verification techniques provide when applied to a simulated N-of-M oracle network under realistic update frequencies?
- **RQ3:** Can an *adaptive* scheme-selection layer (switching between aggregation strategies or PQ algorithms based on load, latency budget, or threat level) outperform any single static scheme across the cost/security/latency trade-off space?

## 4. Related Work & Gap Analysis

| Work | Focus | Gap relative to PQ-Oracle |
|---|---|---|
| Lattice-based oracle-conditional payment scheme (witness encryption), ScienceDirect, Oct 2025 | First PQ construction for oracle-triggered conditional payments | Focused on payment triggering, not price-feed signature cost/aggregation |
| Updatable encryption for blockchain oracles (Kyber-based), Springer *Cybersecurity*, Jan 2026 | Long-term confidentiality of oracle data via updatable encryption | Confidentiality-focused, not signature aggregation or gas cost |
| PQ identity verification for DeFi with dynamic trust scoring, CMC, Aug 2025 | PQC + ZKP for identity/trust in DeFi oracles | Identity-layer, not price-feed signature overhead |
| Lattice-based PQ signature aggregation for low-latency distributed networks, Springer *JIS*, Feb 2026 | General-purpose aggregation scheme (Dilithium-like structure) | Generic distributed-systems evaluation; no blockchain deployment or gas benchmarking |
| Orthus — sublinear batch verification for lattice relations (incl. Falcon aggregation), IACR ePrint 2026 | Cryptographic proof system for efficient batch verification | Pure cryptographic construction; no applied oracle/DeFi cost study |

**→ The open gap:** applying existing PQ aggregation primitives to a realistic oracle-network deployment model, with actual on-chain gas measurement and an adaptive selection layer — rather than proposing yet another cryptographic primitive.

## 5. Proposed Methodology

**Phase 1 — Baseline Benchmarking**
Measure raw signature size, key size, sign time, and verify time for candidate PQ schemes vs. classical baselines (see Part 2).

**Phase 2 — Oracle Network Simulation**
Model a simplified N-of-M oracle network (e.g., 5–21 nodes) submitting periodic signed price updates. Simulate both individual signing and aggregated/batch-verified signing.

**Phase 3 — On-Chain Cost Measurement**
Deploy a verification contract on an Ethereum testnet (Sepolia) — or emulate precompile costs if native PQ verification isn't feasible — and record actual gas consumption per update pattern.

**Phase 4 — Adaptive Layer Design**
Design and evaluate a policy layer that switches between algorithms/aggregation strategies based on: current gas price, required latency, and configurable security threshold. Compare against each static baseline.

**Phase 5 — Evaluation & Write-up**
Comparative tables/plots: cost, latency, security level trade-offs. Ablation: adaptive vs. best static choice.

## 6. Expected Contributions

1. First empirical, on-chain cost benchmark of PQ signature aggregation specifically for oracle/DeFi update patterns.
2. An adaptive scheme-selection architecture (PQ-Oracle) with open evaluation methodology.
3. Reusable benchmark harness/dataset for future PQ-oracle research.

## 7. Rough Timeline

| Phase | Duration |
|---|---|
| Phase 1: Baseline benchmarking | 2–3 weeks |
| Phase 2: Oracle simulation | 2 weeks |
| Phase 3: On-chain gas measurement | 2–3 weeks |
| Phase 4: Adaptive layer + evaluation | 3–4 weeks |
| Phase 5: Write-up | 2 weeks |

---

# PART 2 — Benchmark Setup & Implementation Plan

## 1. Environment Setup

- **Library:** [`liboqs`](https://github.com/open-quantum-safe/liboqs) (+ `liboqs-python` bindings for scripting).
- **⚠️ Important version note:** `liboqs` 0.16.0 (released July 9, 2026) **removed SPHINCS+ entirely**. If SLH-DSA (hash-based) is needed in the comparison, either:
  - pin to `liboqs` 0.15.0, or
  - check for a maintained SLH-DSA-specific fork/binding.
- **Blockchain testbed:** Solidity + Hardhat/Foundry, deployed to Sepolia testnet.
- **Language:** Python for benchmarking/orchestration, Solidity for on-chain verification contracts.

## 2. Candidate Algorithms

| Category | Scheme | Notes |
|---|---|---|
| Baseline (classical) | ECDSA (secp256k1), BLS | Current oracle-network standard |
| PQ — lattice | ML-DSA-44 / 65 / 87 | NIST standard (Dilithium) |
| PQ — lattice | Falcon-512 / 1024 | Compact signatures, slower signing |
| PQ — hash-based | SLH-DSA-128s | Conservative security, larger signatures — requires liboqs ≤0.15.0 |
| PQ — aggregation | Lattice-based aggregate scheme (Dilithium-like, per Springer JIS Feb 2026) | For Phase 2 comparison |

## 3. Benchmark Script Skeleton (Phase 1)

```python
import oqs
import time
import statistics
import csv

ALGORITHMS = [
    "ML-DSA-44", "ML-DSA-65", "ML-DSA-87",
    "Falcon-512", "Falcon-1024",
    # "SLH-DSA-128s",  # requires liboqs <= 0.15.0
]

MESSAGE = b"oracle_price_update_payload_example"
N_TRIALS = 200

def benchmark_algorithm(alg_name):
    with oqs.Signature(alg_name) as signer:
        public_key = signer.generate_keypair()

        sign_times, verify_times = [], []
        signature = None

        for _ in range(N_TRIALS):
            t0 = time.perf_counter()
            signature = signer.sign(MESSAGE)
            sign_times.append(time.perf_counter() - t0)

        with oqs.Signature(alg_name) as verifier:
            for _ in range(N_TRIALS):
                t0 = time.perf_counter()
                verifier.verify(MESSAGE, signature, public_key)
                verify_times.append(time.perf_counter() - t0)

        return {
            "algorithm": alg_name,
            "public_key_size_bytes": len(public_key),
            "signature_size_bytes": len(signature),
            "avg_sign_ms": statistics.mean(sign_times) * 1000,
            "avg_verify_ms": statistics.mean(verify_times) * 1000,
        }

def main():
    results = [benchmark_algorithm(alg) for alg in ALGORITHMS]
    with open("pq_oracle_baseline_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print("Done. Results saved to pq_oracle_baseline_results.csv")

if __name__ == "__main__":
    main()
```

## 4. Metrics to Collect (Phase 1 output → Table I in the paper)

- Public key size (bytes)
- Signature size (bytes)
- Average sign time (ms)
- Average verify time (ms)
- NIST security level (for context in the write-up)

## 5. Phase 3 Plan — On-Chain Gas Measurement

1. Write a minimal Solidity verifier contract per scheme (or use a precompile emulation approach if native EC-style precompiles don't exist for PQ schemes).
2. Deploy to Sepolia via Hardhat/Foundry.
3. Submit simulated price-update transactions at realistic frequency (e.g., every N blocks) for each scheme individually and in aggregated/batched form.
4. Record actual gas consumed per transaction type; compare against ECDSA baseline.

## 6. Immediate Next Steps Checklist

- [ ] Install `liboqs` (pin version if SLH-DSA is required) + `liboqs-python`
- [ ] Run Phase 1 benchmark script above, produce baseline CSV + plot
- [ ] Draft Related Work section using the gap-analysis table in Part 1
- [ ] Set up Hardhat/Foundry project skeleton for Phase 3
- [ ] Decide on N-of-M parameters for the oracle simulation (Phase 2)

---

## References

1. *A quantum-resistant oracle-based conditional payment scheme from lattice*, ScienceDirect, Oct 2025. https://www.sciencedirect.com/science/article/abs/pii/S2214212625002856
2. *An updatable encryption scheme for blockchain oracle based on post-quantum cryptography*, Cybersecurity (Springer), Jan 2026. https://link.springer.com/article/10.1186/s42400-025-00442-w
3. *Quantum-Resilient Blockchain for Secure Digital Identity Verification in DeFi*, CMC, Aug 2025. https://www.techscience.com/cmc/v85n1/63556/html
4. *Efficient post-quantum cryptographic signature aggregation for low-latency distributed networks*, Journal on Information Security (Springer), Feb 2026. https://link.springer.com/article/10.1186/s13635-026-00228-8
5. *Practical Sublinear Batch-Verification of Lattice Relations (Orthus)*, IACR ePrint 2026/398. https://eprint.iacr.org/2026/398.pdf
6. `liboqs` releases, Open Quantum Safe project. https://github.com/open-quantum-safe/liboqs/releases
