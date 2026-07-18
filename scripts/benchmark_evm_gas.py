import os
import csv
import math

try:
    import matplotlib.pyplot as plt
except ImportError:
    raise ImportError("Required package 'matplotlib' missing. Install via: pip install matplotlib")

NETWORK_SIZES = [5, 11, 21, 31, 51]
GAS_PRICES_GWEI = [10, 30, 50, 100]
ETH_PRICE_USD = 3000.0
UPDATES_PER_YEAR = 525600  # 1 update per minute

# Calldata estimation (assuming 95% non-zero bytes for signature payloads)
def calc_calldata_gas(payload_bytes):
    non_zero_bytes = int(payload_bytes * 0.95)
    zero_bytes = payload_bytes - non_zero_bytes
    return (non_zero_bytes * 16) + (zero_bytes * 4)

# Precompile / Verification gas models for ALL algorithms
VERIFY_GAS_MODELS = {
    "ECDSA (secp256k1)": {
        "unagg_func": lambda num_nodes: num_nodes * 3000,
        "agg_func": lambda num_nodes: int(num_nodes * 3000 * 0.7),
        "unagg_payload": lambda num_nodes: num_nodes * (70 + 4),
        "agg_payload": lambda num_nodes: num_nodes * (70 + 4),
        "category": "Classical"
    },
    "BLS12-381": {
        "unagg_func": lambda num_nodes: num_nodes * 45000,
        "agg_func": lambda num_nodes: 45000 + int(num_nodes * 1200),
        "unagg_payload": lambda num_nodes: num_nodes * (96 + 4),
        "agg_payload": lambda num_nodes: 96 + (num_nodes * 4),
        "category": "Classical"
    },
    "ML-DSA-44": {
        "unagg_func": lambda num_nodes: num_nodes * 240000,
        "agg_func": lambda num_nodes: 240000 + int(45000 * math.log2(num_nodes)),
        "unagg_payload": lambda num_nodes: num_nodes * (2420 + 4),
        "agg_payload": lambda num_nodes: 2420 + int(128 * math.log2(num_nodes)) + (num_nodes * 4),
        "category": "PQ - Lattice"
    },
    "ML-DSA-65": {
        "unagg_func": lambda num_nodes: num_nodes * 340000,
        "agg_func": lambda num_nodes: 340000 + int(60000 * math.log2(num_nodes)),
        "unagg_payload": lambda num_nodes: num_nodes * (3309 + 4),
        "agg_payload": lambda num_nodes: 3309 + int(144 * math.log2(num_nodes)) + (num_nodes * 4),
        "category": "PQ - Lattice"
    },
    "ML-DSA-87": {
        "unagg_func": lambda num_nodes: num_nodes * 450000,
        "agg_func": lambda num_nodes: 450000 + int(80000 * math.log2(num_nodes)),
        "unagg_payload": lambda num_nodes: num_nodes * (4627 + 4),
        "agg_payload": lambda num_nodes: 4627 + int(160 * math.log2(num_nodes)) + (num_nodes * 4),
        "category": "PQ - Lattice"
    },
    "Falcon-512": {
        "unagg_func": lambda num_nodes: num_nodes * 180000,
        "agg_func": lambda num_nodes: 180000 + int(35000 * math.log2(num_nodes)),
        "unagg_payload": lambda num_nodes: num_nodes * (653 + 4),
        "agg_payload": lambda num_nodes: 653 + int(160 * math.log2(num_nodes)) + (num_nodes * 4),
        "category": "PQ - Lattice"
    },
    "Falcon-1024": {
        "unagg_func": lambda num_nodes: num_nodes * 320000,
        "agg_func": lambda num_nodes: 320000 + int(55000 * math.log2(num_nodes)),
        "unagg_payload": lambda num_nodes: num_nodes * (1270 + 4),
        "agg_payload": lambda num_nodes: 1270 + int(192 * math.log2(num_nodes)) + (num_nodes * 4),
        "category": "PQ - Lattice"
    },
    "SLH-DSA-SHA2-128s": {
        "unagg_func": lambda num_nodes: num_nodes * 850000,
        "agg_func": lambda num_nodes: 850000 + int(120000 * math.log2(num_nodes)),
        "unagg_payload": lambda num_nodes: num_nodes * (7856 + 4),
        "agg_payload": lambda num_nodes: 7856 + int(256 * math.log2(num_nodes)) + (num_nodes * 4),
        "category": "PQ - Hash-based"
    }
}

BASE_TRANSACTION_GAS = 21000
STORAGE_EVENT_GAS = 6500

def run_evm_gas_benchmark():
    os.makedirs("results", exist_ok=True)
    results = []

    for alg, model in VERIFY_GAS_MODELS.items():
        fn_unagg_payload = model["unagg_payload"]
        fn_unagg_func = model["unagg_func"]
        fn_agg_payload = model["agg_payload"]
        fn_agg_func = model["agg_func"]

        for num_nodes in NETWORK_SIZES:
            unagg_payload = fn_unagg_payload(num_nodes)
            unagg_calldata_gas = calc_calldata_gas(unagg_payload)
            unagg_verify_gas = fn_unagg_func(num_nodes)
            total_unagg_gas = BASE_TRANSACTION_GAS + STORAGE_EVENT_GAS + unagg_calldata_gas + unagg_verify_gas

            agg_payload = fn_agg_payload(num_nodes)
            agg_calldata_gas = calc_calldata_gas(agg_payload)
            agg_verify_gas = fn_agg_func(num_nodes)
            total_agg_gas = BASE_TRANSACTION_GAS + STORAGE_EVENT_GAS + agg_calldata_gas + agg_verify_gas

            gas_savings_pct = ((total_unagg_gas - total_agg_gas) / total_unagg_gas) * 100

            for gwei in GAS_PRICES_GWEI:
                unagg_cost_eth = (total_unagg_gas * gwei) / 1e9
                agg_cost_eth = (total_agg_gas * gwei) / 1e9
                
                unagg_cost_usd = unagg_cost_eth * ETH_PRICE_USD
                agg_cost_usd = agg_cost_eth * ETH_PRICE_USD
                annual_agg_cost_usd = agg_cost_usd * UPDATES_PER_YEAR

                results.append({
                    "Algorithm": alg,
                    "Category": model["category"],
                    "Network_Nodes_N": num_nodes,
                    "Gas_Price_Gwei": gwei,
                    "Unagg_Total_Gas": total_unagg_gas,
                    "Agg_Total_Gas": total_agg_gas,
                    "Gas_Savings_Pct": round(gas_savings_pct, 2),
                    "Unagg_Tx_USD": round(unagg_cost_usd, 4),
                    "Agg_Tx_USD": round(agg_cost_usd, 4),
                    "Annual_Agg_Cost_USD": round(annual_agg_cost_usd, 2)
                })

    csv_path = os.path.join("results", "pq_oracle_evm_gas_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"EVM Gas benchmark results saved to {csv_path}")
    return results

def generate_gas_plots(results):
    selected_algs = ["ECDSA (secp256k1)", "BLS12-381", "ML-DSA-44", "Falcon-512", "SLH-DSA-SHA2-128s"]
    gwei_30_data = [r for r in results if r["Gas_Price_Gwei"] == 30 and r["Network_Nodes_N"] == 21 and r["Algorithm"] in selected_algs]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    ax1 = axes[0]
    algs = [r["Algorithm"] for r in gwei_30_data]
    unagg_gas = [r["Unagg_Total_Gas"] / 1000 for r in gwei_30_data]
    agg_gas = [r["Agg_Total_Gas"] / 1000 for r in gwei_30_data]

    x = range(len(algs))
    width = 0.35
    ax1.bar([i - width/2 for i in x], unagg_gas, width, label='Unaggregated Gas (KGas)', color='crimson')
    ax1.bar([i + width/2 for i in x], agg_gas, width, label='Aggregated Gas (KGas)', color='seagreen')
    ax1.set_xlabel("Algorithm", fontweight='bold')
    ax1.set_ylabel("Total EVM Gas per Update (kGas)", fontweight='bold')
    ax1.set_title("EVM Gas Consumption per Oracle Update (N=21)", fontweight='bold', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(algs, rotation=25, ha='right')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend()

    ax2 = axes[1]
    annual_usd = [r["Annual_Agg_Cost_USD"] / 1000 for r in gwei_30_data]
    ax2.bar(algs, annual_usd, color='darkslateblue', alpha=0.8, width=0.4)
    ax2.set_xlabel("Algorithm", fontweight='bold')
    ax2.set_ylabel("Annual Operational Cost ($k USD)", fontweight='bold')
    ax2.set_title("Annual Oracle Operational Cost (30 Gwei, $3000 ETH)", fontweight='bold', fontsize=12)
    ax2.set_xticks(range(len(algs)))
    ax2.set_xticklabels(algs, rotation=25, ha='right')
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.suptitle("PQ-Oracle Phase 3: EVM On-Chain Gas & Cost Benchmarks", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plot_path = os.path.join("results", "pq_oracle_gas_cost_analysis.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Gas plot saved to {plot_path}")

def main():
    results = run_evm_gas_benchmark()
    generate_gas_plots(results)

if __name__ == "__main__":
    main()
