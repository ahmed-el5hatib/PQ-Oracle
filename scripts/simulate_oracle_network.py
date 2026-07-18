import time
import math
import csv
import os
import oqs
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from py_ecc.bls import G2ProofOfPossession as bls
import matplotlib.pyplot as plt

NETWORK_SIZES = [5, 11, 21, 31, 51]
MESSAGE = b"oracle_price_update_eth_usd_1850.50_timestamp_1750000000"

# Base empirical per-signature sizes from Phase 1
BASE_METRICS = {
    "ECDSA (secp256k1)": {"pk": 88, "sig": 70, "verify_ms": 0.44, "category": "Classical"},
    "BLS12-381": {"pk": 48, "sig": 96, "verify_ms": 331.65, "category": "Classical"},
    "ML-DSA-44": {"pk": 1312, "sig": 2420, "verify_ms": 0.37, "category": "PQ - Lattice"},
    "ML-DSA-65": {"pk": 1952, "sig": 3309, "verify_ms": 0.61, "category": "PQ - Lattice"},
    "ML-DSA-87": {"pk": 2592, "sig": 4627, "verify_ms": 0.99, "category": "PQ - Lattice"},
    "Falcon-512": {"pk": 897, "sig": 653, "verify_ms": 0.20, "category": "PQ - Lattice"},
    "Falcon-1024": {"pk": 1793, "sig": 1270, "verify_ms": 0.39, "category": "PQ - Lattice"},
    "SLH_DSA_PURE_SHA2_128S": {"pk": 32, "sig": 7856, "verify_ms": 3.44, "category": "PQ - Hash-based"},
}

def simulate_unaggregated(alg, N):
    metrics = BASE_METRICS[alg]
    # In individual mode: send N signatures + N public keys (or 4-byte node IDs if registered on-chain)
    node_id_overhead = 4  # 4 bytes per node ID when registered on-chain
    payload_size = N * (metrics["sig"] + node_id_overhead)
    total_verify_ms = N * metrics["verify_ms"]
    return payload_size, total_verify_ms

def simulate_aggregated(alg, N):
    metrics = BASE_METRICS[alg]
    node_id_overhead = 4
    
    if alg == "BLS12-381":
        # BLS signatures aggregate into a SINGLE 96-byte signature!
        # Overhead: 96B aggregate sig + N * 4B node bitmask/IDs
        payload_size = 96 + (N * node_id_overhead)
        # Verification requires 2 pairings + N scalar mults (~15% overhead over single verify)
        total_verify_ms = metrics["verify_ms"] * (1 + 0.15 * math.log2(N))
        
    elif "ML-DSA" in alg:
        # Lattice aggregation (Dilithium-like / Orthus sublinear batch verification model)
        # Single representative signature + sublinear proof overhead (approx 128 bytes per log2(N))
        batch_proof_bytes = int(128 * math.log2(N))
        payload_size = metrics["sig"] + batch_proof_bytes + (N * node_id_overhead)
        total_verify_ms = metrics["verify_ms"] * (1 + 0.25 * math.log2(N))
        
    elif "Falcon" in alg:
        # Falcon Orthus sublinear batch verification
        batch_proof_bytes = int(160 * math.log2(N))
        payload_size = metrics["sig"] + batch_proof_bytes + (N * node_id_overhead)
        total_verify_ms = metrics["verify_ms"] * (1 + 0.20 * math.log2(N))
        
    elif "SLH_DSA" in alg:
        # Hash-based Merkle tree batching
        batch_proof_bytes = int(256 * math.log2(N))
        payload_size = metrics["sig"] + batch_proof_bytes + (N * node_id_overhead)
        total_verify_ms = metrics["verify_ms"] * (1 + 0.35 * math.log2(N))
        
    else:  # ECDSA
        # ECDSA does not natively aggregate into 1 signature without ZK (SNARK wrapper)
        # e.g., secp256k1 batch verification overhead
        payload_size = N * metrics["sig"] + (N * node_id_overhead)
        total_verify_ms = N * metrics["verify_ms"] * 0.7  # ~30% batch verify speedup
        
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
    # Filter key candidate algorithms for clean visualization
    selected_algs = ["ECDSA (secp256k1)", "BLS12-381", "ML-DSA-44", "Falcon-512", "SLH_DSA_PURE_SHA2_128S"]
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Unaggregated Payload Size vs N
    ax1 = axes[0]
    for alg in selected_algs:
        subset = [r for r in results if r["Algorithm"] == alg]
        nodes = [r["Network_Nodes_N"] for r in subset]
        unagg_bytes = [r["Unagg_Payload_Bytes"] for r in subset]
        ax1.plot(nodes, unagg_bytes, marker='o', linewidth=2, label=f"{alg} (Unaggregated)")
        
    ax1.set_xlabel("Number of Oracle Consensus Nodes (N)", fontweight='bold')
    ax1.set_ylabel("Total Oracle Payload Size (Bytes)", fontweight='bold')
    ax1.set_title("Unaggregated Payload Size Growth", fontweight='bold', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend()
    
    # Plot 2: Aggregated vs Unaggregated Payload Size for PQC algorithms (N=21)
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
    ax2.set_xticklabels(algs, rotation=25, ha='right')
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
