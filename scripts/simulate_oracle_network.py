import time
import math
import csv
import os

try:
    import matplotlib.pyplot as plt
except ImportError:
    raise ImportError("Required package 'matplotlib' missing. Install via: pip install matplotlib")

NETWORK_SIZES = [5, 11, 21, 31, 51]
MESSAGE = b"oracle_price_update_eth_usd_1850.50_timestamp_1750000000"

BASE_METRICS = {
    "ECDSA (secp256k1)": {"pk": 88, "sig": 70, "verify_ms": 0.44, "category": "Classical"},
    "BLS12-381": {"pk": 48, "sig": 96, "verify_ms": 331.65, "category": "Classical"},
    "ML-DSA-44": {"pk": 1312, "sig": 2420, "verify_ms": 0.37, "category": "PQ - Lattice"},
    "ML-DSA-65": {"pk": 1952, "sig": 3309, "verify_ms": 0.61, "category": "PQ - Lattice"},
    "ML-DSA-87": {"pk": 2592, "sig": 4627, "verify_ms": 0.99, "category": "PQ - Lattice"},
    "Falcon-512": {"pk": 897, "sig": 653, "verify_ms": 0.20, "category": "PQ - Lattice"},
    "Falcon-1024": {"pk": 1793, "sig": 1270, "verify_ms": 0.39, "category": "PQ - Lattice"},
    "SLH-DSA-SHA2-128s": {"pk": 32, "sig": 7856, "verify_ms": 3.44, "category": "PQ - Hash-based"},
}

def simulate_unaggregated(alg, N):
    metrics = BASE_METRICS[alg]
    node_id_overhead = 4
    payload_size = N * (metrics["sig"] + node_id_overhead)
    total_verify_ms = N * metrics["verify_ms"]
    return payload_size, total_verify_ms

def simulate_aggregated(alg, N):
    metrics = BASE_METRICS[alg]
    node_id_overhead = 4
    
    if alg == "BLS12-381":
        payload_size = 96 + (N * node_id_overhead)
        total_verify_ms = metrics["verify_ms"] * (1 + 0.15 * math.log2(N))
        
    elif "ML-DSA" in alg:
        batch_proof_bytes = int(128 * math.log2(N))
        payload_size = metrics["sig"] + batch_proof_bytes + (N * node_id_overhead)
        total_verify_ms = metrics["verify_ms"] * (1 + 0.25 * math.log2(N))
        
    elif "Falcon" in alg:
        batch_proof_bytes = int(160 * math.log2(N))
        payload_size = metrics["sig"] + batch_proof_bytes + (N * node_id_overhead)
        total_verify_ms = metrics["verify_ms"] * (1 + 0.20 * math.log2(N))
        
    elif "SLH-DSA" in alg:
        batch_proof_bytes = int(256 * math.log2(N))
        payload_size = metrics["sig"] + batch_proof_bytes + (N * node_id_overhead)
        total_verify_ms = metrics["verify_ms"] * (1 + 0.35 * math.log2(N))
        
    else:  # ECDSA
        payload_size = N * metrics["sig"] + (N * node_id_overhead)
        total_verify_ms = N * metrics["verify_ms"] * 0.7
        
    return payload_size, total_verify_ms

def run_simulation():
    os.makedirs("results", exist_ok=True)
    results = []
    
    for alg in BASE_METRICS.keys():
        for N in NETWORK_SIZES:
            unagg_bytes, unagg_verify_ms = simulate_unaggregated(alg, N)
            agg_bytes, agg_verify_ms = simulate_aggregated(alg, N)
            
            savings_pct = ((unagg_bytes - agg_bytes) / unagg_bytes) * 100
            
            results.append({
                "Algorithm": alg,
                "Category": BASE_METRICS[alg]["category"],
                "Network_Nodes_N": N,
                "Unagg_Payload_Bytes": unagg_bytes,
                "Agg_Payload_Bytes": agg_bytes,
                "Payload_Savings_Pct": round(savings_pct, 2),
                "Unagg_Verify_ms": round(unagg_verify_ms, 2),
                "Agg_Verify_ms": round(agg_verify_ms, 2),
            })
            
    csv_path = os.path.join("results", "pq_oracle_simulation_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Simulation results saved to {csv_path}")
    return results

def generate_simulation_plots(results):
    # Include ALL 8 algorithms in the simulation charts
    selected_algs = list(BASE_METRICS.keys())
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    
    ax1 = axes[0]
    for alg in selected_algs:
        subset = [r for r in results if r["Algorithm"] == alg]
        nodes = [r["Network_Nodes_N"] for r in subset]
        unagg_bytes = [r["Unagg_Payload_Bytes"] for r in subset]
        ax1.plot(nodes, unagg_bytes, marker='o', linewidth=2, label=f"{alg}")
        
    ax1.set_xlabel("Number of Oracle Consensus Nodes (N)", fontweight='bold')
    ax1.set_ylabel("Total Oracle Payload Size (Bytes)", fontweight='bold')
    ax1.set_title("Unaggregated Payload Size Growth", fontweight='bold', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(fontsize=9)
    
    ax2 = axes[1]
    n21_data = [r for r in results if r["Network_Nodes_N"] == 21 and r["Algorithm"] in selected_algs]
    algs = [r["Algorithm"] for r in n21_data]
    unagg = [r["Unagg_Payload_Bytes"] for r in n21_data]
    agg = [r["Agg_Payload_Bytes"] for r in n21_data]
    
    x = range(len(algs))
    width = 0.35
    ax2.bar([i - width/2 for i in x], unagg, width, label='Unaggregated', color='salmon')
    ax2.bar([i + width/2 for i in x], agg, width, label='Aggregated / Batched', color='teal')
    
    ax2.set_xlabel("Algorithm", fontweight='bold')
    ax2.set_ylabel("Payload Size for N=21 Nodes (Bytes)", fontweight='bold')
    ax2.set_title("Aggregation Impact at N=21 Nodes", fontweight='bold', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(algs, rotation=35, ha='right', fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend()
    
    plt.suptitle("PQ-Oracle Phase 2: N-of-M Oracle Consensus Aggregation Simulation", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plot_path = os.path.join("results", "pq_oracle_network_simulation.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Simulation plot saved to {plot_path}")

def main():
    results = run_simulation()
    generate_simulation_plots(results)

if __name__ == "__main__":
    main()
