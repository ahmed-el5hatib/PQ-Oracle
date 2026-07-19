#!/usr/bin/env python3
"""
PQ-Oracle: Master Reproduction Pipeline
Runs all benchmarking, simulation, and distributed testbed scripts sequentially to reproduce
all empirical data, CSV artifacts, JSON metrics, and visual charts across Phases 1 through 5.
"""

import sys
import os
import time

def run_step(step_name, script_path):
    print(f"\n=======================================================")
    print(f"[RUN] {step_name}...")
    print(f"=======================================================")
    t0 = time.time()
    
    if not os.path.exists(script_path):
        print(f"[ERROR] Script {script_path} not found.")
        sys.exit(1)
        
    ret = os.system(f"{sys.executable} {script_path}")
    elapsed = time.time() - t0
    
    if ret != 0:
        print(f"[ERROR] Failed executing {step_name} (Exit code: {ret})")
        sys.exit(1)
    else:
        print(f"[OK] Completed {step_name} in {elapsed:.2f} seconds.")

def main():
    print("=======================================================")
    print("PQ-Oracle: End-to-End Empirical Pipeline Runner")
    print("=======================================================")
    
    start_time = time.time()
    
    # Phase 1: Microbenchmarks
    run_step("Phase 1: Baseline Microbenchmarks", "scripts/benchmark_phase1.py")
    
    # Phase 2: N-of-M Consensus Aggregation Simulation
    run_step("Phase 2: N-of-M Consensus Aggregation Simulation", "scripts/simulate_oracle_network.py")
    
    # Phase 3: EVM On-Chain Gas Cost Analysis
    run_step("Phase 3: EVM Gas Cost & Financial Analysis", "scripts/benchmark_evm_gas.py")
    
    # Phase 4: Adaptive Scheme Selection Engine
    run_step("Phase 4: Adaptive Scheme Selection Engine", "scripts/adaptive_engine.py")
    
    # Phase 5: Distributed Oracle Testbed Evaluation
    run_step("Phase 5: Distributed Oracle Testbed Prototype", "run_phase5.py")
    
    total_time = time.time() - start_time
    
    print("\n=======================================================")
    print(f"[SUCCESS] All PQ-Oracle Benchmarks (Phases 1-5) Executed Successfully in {total_time:.2f}s!")
    print("=======================================================")
    print("Artifacts generated in /results/ directory:")
    print("  - pq_oracle_baseline_results.csv")
    print("  - pq_oracle_baseline_comparison.png")
    print("  - pq_oracle_simulation_results.csv")
    print("  - pq_oracle_network_simulation.png")
    print("  - pq_oracle_evm_gas_results.csv")
    print("  - pq_oracle_gas_cost_analysis.png")
    print("  - pq_oracle_gas_sensitivity.png")
    print("  - pq_oracle_adaptive_results.csv")
    print("  - pq_oracle_adaptive_policy.png")
    print("  - pq_oracle_phase5_results.csv")
    print("  - pq_oracle_phase5_results.json")
    print("  - pq_oracle_phase5_distributed_testbed.png")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
