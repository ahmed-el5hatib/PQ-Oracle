# Changelog

All notable changes to the `PQ-Oracle` project will be documented in this file.

## [1.0.0] - 2026-07-18

### Added
- **Phase 1 Microbenchmarks:** Empirical evaluation of ECDSA (secp256k1), BLS12-381, ML-DSA-44/65/87, Falcon-512/1024, and SLH-DSA-SHA2-128s.
- **Phase 2 Consensus Aggregation Simulator:** N-of-M oracle consensus simulation ($N \in \{5, 11, 21, 31, 51\}$).
- **Phase 3 EVM Gas Analysis:** Solidity verifier contract (`contracts/OracleVerifier.sol`) and EVM gas cost engine (`scripts/benchmark_evm_gas.py`).
- **Phase 4 Adaptive Engine:** Dynamic multi-objective policy selector (`scripts/adaptive_engine.py`) integrating real-time gas costs, latency SLAs, and security levels.
- **Phase 5 Manuscript:** Complete IEEE Access manuscript draft (`paper/PQ_Oracle_IEEE_Access_Draft.md`).
- **Automation Pipeline:** Unified master runner script (`run_all.py`) and explicit dependency specifications (`requirements.txt`).

### Security & Quality Fixes
- Added `onlyOwner` and `onlyAuthorized` access controls in `OracleVerifier.sol`.
- Removed infinite `gasleft()` loop anti-pattern in Solidity.
- Replaced deterministic integer key loop in BLS microbenchmark with true cryptographically secure random private key generation (`secrets.randbelow`).
- Standardized algorithm nomenclature (`SLH-DSA-SHA2-128s`) across all scripts, CSVs, charts, and manuscripts.
- Coupled `adaptive_engine.py` dynamically to Phase 3 EVM gas CSV exports.
