"""
PQ-Oracle: Phase 5 Visualization Suite
Generates publication-quality figures for Phase 5 Distributed Oracle Testbed.
"""

import os
import json
from typing import List, Dict, Any
import matplotlib.pyplot as plt

def generate_phase5_plots(results: List[Dict[str, Any]], output_dir: str = "results"):
    os.makedirs(output_dir, exist_ok=True)
    
    algs = sorted(list(set(r["Algorithm"] for r in results)))
    
    fig, axes = plt.subplots(2, 4, figsize=(22, 10))
    
    # 1. Throughput vs Nodes
    ax = axes[0, 0]
    for alg in algs:
        sub = [r for r in results if r["Algorithm"] == alg]
        ax.plot([r["Nodes_N"] for r in sub], [r["Throughput_updates_per_sec"] for r in sub], marker='o', label=alg)
    ax.set_xlabel("Nodes (N)", fontweight='bold')
    ax.set_ylabel("Throughput (updates/s)", fontweight='bold')
    ax.set_title("1. Throughput vs Network Size", fontweight='bold', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8)

    # 2. End-to-End Latency vs Nodes
    ax = axes[0, 1]
    for alg in algs:
        sub = [r for r in results if r["Algorithm"] == alg]
        ax.plot([r["Nodes_N"] for r in sub], [r["Avg_E2E_Latency_ms"] for r in sub], marker='s', label=alg)
    ax.set_xlabel("Nodes (N)", fontweight='bold')
    ax.set_ylabel("E2E Latency (ms)", fontweight='bold')
    ax.set_title("2. E2E Latency vs Network Size", fontweight='bold', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)

    # 3. CPU Utilization
    ax = axes[0, 2]
    for alg in algs:
        sub = [r for r in results if r["Algorithm"] == alg]
        ax.plot([r["Nodes_N"] for r in sub], [r["CPU_Usage_Pct"] for r in sub], marker='^', label=alg)
    ax.set_xlabel("Nodes (N)", fontweight='bold')
    ax.set_ylabel("CPU Usage (%)", fontweight='bold')
    ax.set_title("3. System CPU Utilization", fontweight='bold', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)

    # 4. Memory Consumption
    ax = axes[0, 3]
    for alg in algs:
        sub = [r for r in results if r["Algorithm"] == alg]
        ax.plot([r["Nodes_N"] for r in sub], [r["Memory_MB"] for r in sub], marker='d', label=alg)
    ax.set_xlabel("Nodes (N)", fontweight='bold')
    ax.set_ylabel("Memory (MB)", fontweight='bold')
    ax.set_title("4. RAM Memory Footprint", fontweight='bold', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)

    # 5. Aggregation Delay
    ax = axes[1, 0]
    for alg in algs:
        sub = [r for r in results if r["Algorithm"] == alg]
        ax.plot([r["Nodes_N"] for r in sub], [r["Avg_Aggregation_Delay_ms"] for r in sub], marker='p', label=alg)
    ax.set_xlabel("Nodes (N)", fontweight='bold')
    ax.set_ylabel("Aggregation Delay (ms)", fontweight='bold')
    ax.set_title("5. Aggregation Service Delay", fontweight='bold', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)

    # 6. Network Bandwidth
    ax = axes[1, 1]
    for alg in algs:
        sub = [r for r in results if r["Algorithm"] == alg]
        ax.plot([r["Nodes_N"] for r in sub], [r["Transmitted_KB"] for r in sub], marker='h', label=alg)
    ax.set_xlabel("Nodes (N)", fontweight='bold')
    ax.set_ylabel("Bandwidth Transmitted (KB)", fontweight='bold')
    ax.set_title("6. Total Network Bandwidth", fontweight='bold', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)

    # 7. Byzantine & Verification Failure Rate
    ax = axes[1, 2]
    n21_sub = [r for r in results if r["Nodes_N"] == 21]
    n21_algs = [r["Algorithm"] for r in n21_sub]
    fail_rates = [r["Failure_Rate_Pct"] for r in n21_sub]
    x = range(len(n21_algs))
    ax.bar(x, fail_rates, color='crimson', alpha=0.7, width=0.4)
    ax.set_xlabel("Algorithm", fontweight='bold')
    ax.set_ylabel("Rejection / Failure Rate (%)", fontweight='bold')
    ax.set_title("7. Byzantine Rejection Rate (N=21)", fontweight='bold', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(n21_algs, rotation=30, ha='right', fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)

    # 8. Verification Latency per Node
    ax = axes[1, 3]
    v_times = [r["Avg_Verify_Latency_ms"] for r in n21_sub]
    ax.bar(x, v_times, color='darkslateblue', alpha=0.8, width=0.4)
    ax.set_xlabel("Algorithm", fontweight='bold')
    ax.set_ylabel("Verify Latency (ms)", fontweight='bold')
    ax.set_title("8. Aggregator Verification Time (N=21)", fontweight='bold', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(n21_algs, rotation=30, ha='right', fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)

    plt.suptitle("PQ-Oracle Phase 5: Distributed Oracle Testbed Empirical Evaluation", fontsize=15, fontweight='bold')
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "pq_oracle_phase5_distributed_testbed.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Phase 5 distributed testbed plots saved to {plot_path}")
