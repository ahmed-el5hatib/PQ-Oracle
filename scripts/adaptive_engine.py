import os
import csv
import random

try:
    import matplotlib.pyplot as plt
except ImportError:
    raise ImportError("Required package 'matplotlib' missing. Install via: pip install matplotlib")

ETH_PRICE_USD = 3000.0

SECURITY_SCORES = {
    "ECDSA (secp256k1)": 1.0,
    "BLS12-381": 1.0,
    "Falcon-512": 1.0,   # NIST Level 1
    "ML-DSA-44": 2.0,    # NIST Level 2
    "ML-DSA-65": 3.0,    # NIST Level 3
    "Falcon-1024": 5.0,  # NIST Level 5
    "ML-DSA-87": 5.0,    # NIST Level 5
    "SLH-DSA-SHA2-128s": 1.0, # NIST Level 1
}

PQC_FLAGS = {
    "ECDSA (secp256k1)": False,
    "BLS12-381": False,
    "Falcon-512": True,
    "ML-DSA-44": True,
    "ML-DSA-65": True,
    "Falcon-1024": True,
    "ML-DSA-87": True,
    "SLH-DSA-SHA2-128s": True,
}

LATENCY_ESTIMATES_MS = {
    "ECDSA (secp256k1)": 6.47,
    "BLS12-381": 550.0,
    "Falcon-512": 0.38,
    "ML-DSA-44": 0.78,
    "ML-DSA-65": 1.28,
    "Falcon-1024": 0.73,
    "ML-DSA-87": 2.08,
    "SLH-DSA-SHA2-128s": 8.73,
}

def load_gas_models_from_csv(csv_path="results/pq_oracle_evm_gas_results.csv"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Gas results CSV not found at {csv_path}. Run benchmark_evm_gas.py first.")
        
    schemes = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Network_Nodes_N"] == "21":
                alg = row["Algorithm"]
                if alg not in schemes:
                    schemes[alg] = {
                        "gas": int(row["Agg_Total_Gas"]),
                        "latency": LATENCY_ESTIMATES_MS.get(alg, 1.0),
                        "security": SECURITY_SCORES.get(alg, 3.0),
                        "pqc": PQC_FLAGS.get(alg, True)
                    }
    return schemes

def adaptive_policy(schemes, gas_price_gwei, max_cost_usd_target, max_latency_ms, require_pqc=True):
    best_scheme = None
    best_score = float('-inf')

    for name, s in schemes.items():
        if require_pqc and not s["pqc"]:
            continue
        
        tx_cost_usd = (s["gas"] * gas_price_gwei * 1e-9) * ETH_PRICE_USD
        
        if s["latency"] > max_latency_ms:
            continue
            
        cost_penalty = (tx_cost_usd / max_cost_usd_target) if max_cost_usd_target > 0 else 0
        utility_score = (s["security"] * 2.0) - (cost_penalty * 3.0)
        
        if utility_score > best_score:
            best_score = utility_score
            best_scheme = name
            
    if best_scheme is None and require_pqc:
        best_scheme = next((k for k, v in schemes.items() if v["pqc"]), "Falcon-512")
    elif best_scheme is None:
        best_scheme = next((k for k in schemes.keys()), "ECDSA (secp256k1)")
        
    return best_scheme

def simulate_24h_oracle_feed():
    os.makedirs("results", exist_ok=True)
    schemes = load_gas_models_from_csv()
    
    random.seed(42)
    time_steps = 1440
    gas_prices = []
    
    current_gas = 25.0
    for t in range(time_steps):
        hour = (t // 60) % 24
        if 12 <= hour <= 16:
            current_gas += random.uniform(-2, 5)
        else:
            current_gas += random.uniform(-3, 3)
            
        current_gas = max(12.0, min(140.0, current_gas))
        gas_prices.append(current_gas)

    results = []
    
    total_cost_adaptive = 0.0
    total_cost_static_mldsa44 = 0.0
    total_cost_static_falcon512 = 0.0
    total_cost_static_falcon1024 = 0.0
    total_cost_static_mldsa87 = 0.0
    
    adaptive_choices = []
    level_counts = {1.0: 0, 2.0: 0, 3.0: 0, 5.0: 0}
    
    for t, gwei in enumerate(gas_prices):
        chosen_scheme = adaptive_policy(schemes, gwei, max_cost_usd_target=50.0, max_latency_ms=50.0, require_pqc=True)
        adaptive_choices.append(chosen_scheme)
        
        sec_level = SECURITY_SCORES[chosen_scheme]
        level_counts[sec_level] = level_counts.get(sec_level, 0) + 1
        
        cost_adaptive = (schemes[chosen_scheme]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cost_mldsa44 = (schemes["ML-DSA-44"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cost_falcon512 = (schemes["Falcon-512"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cost_falcon1024 = (schemes["Falcon-1024"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cost_mldsa87 = (schemes["ML-DSA-87"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        
        total_cost_adaptive += cost_adaptive
        total_cost_static_mldsa44 += cost_mldsa44
        total_cost_static_falcon512 += cost_falcon512
        total_cost_static_falcon1024 += cost_falcon1024
        total_cost_static_mldsa87 += cost_mldsa87
        
        if t % 60 == 0:
            results.append({
                "Hour": t // 60,
                "Gas_Price_Gwei": round(gwei, 2),
                "Chosen_Scheme": chosen_scheme,
                "Adaptive_Cost_USD": round(cost_adaptive, 2),
                "MLDSA44_Static_Cost_USD": round(cost_mldsa44, 2),
                "Falcon512_Static_Cost_USD": round(cost_falcon512, 2),
                "Falcon1024_Static_Cost_USD": round(cost_falcon1024, 2),
            })

    avg_security_level = sum(s * c for s, c in level_counts.items()) / time_steps
    daily_cost_k = total_cost_adaptive / 1000.0
    scer = avg_security_level / daily_cost_k  # Security-Cost Efficiency Ratio

    print(f"\n=======================================================")
    print(f"24h Operational Cost & Security Summary (1,440 price updates):")
    print(f"=======================================================")
    print(f"  - PQ-Oracle Adaptive Engine: ${total_cost_adaptive:,.2f}")
    print(f"  - Static Falcon-512 (L1):    ${total_cost_static_falcon512:,.2f}")
    print(f"  - Static ML-DSA-44 (L2):     ${total_cost_static_mldsa44:,.2f}")
    print(f"  - Static Falcon-1024 (L5):   ${total_cost_static_falcon1024:,.2f}")
    print(f"  - Static ML-DSA-87 (L5):     ${total_cost_static_mldsa87:,.2f}")
    print(f"-------------------------------------------------------")
    print(f"NIST Security Level Breakdown (% Time):")
    for lvl in sorted(level_counts.keys()):
        pct = (level_counts[lvl] / time_steps) * 100
        print(f"  - NIST Level {int(lvl)}: {pct:.1f}% of updates")
    print(f"-------------------------------------------------------")
    print(f"Average Security Level: {avg_security_level:.2f} / 5.0")
    print(f"Security-Cost Efficiency Ratio (SCER): {scer:.4f} Level/$k")
    print(f"=======================================================\n")
    
    csv_path = os.path.join("results", "pq_oracle_adaptive_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Adaptive simulation saved to {csv_path}")
    
    return gas_prices, adaptive_choices, results, total_cost_adaptive, total_cost_static_falcon512, total_cost_static_mldsa44, total_cost_static_falcon1024, total_cost_static_mldsa87, schemes

def generate_adaptive_plots(gas_prices, adaptive_choices, total_adaptive, total_f512, total_ml44, total_f1024, total_ml87, schemes):
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    hours = [t / 60 for t in range(len(gas_prices))]
    
    ax1 = axes[0]
    ax1.plot(hours, gas_prices, color='firebrick', linewidth=1.5, label='EVM Gas Price (Gwei)')
    ax1.set_ylabel("Gas Price (Gwei)", fontweight='bold', color='firebrick')
    ax1.set_title("EVM Gas Price Volatility & Adaptive PQC Scheme Selection", fontweight='bold', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    ax2 = axes[1]
    cum_adaptive = []
    cum_f512 = []
    cum_ml44 = []
    cum_f1024 = []
    cum_ml87 = []
    
    ca, cf5, cml, cf10, cml87 = 0, 0, 0, 0, 0
    for t, gwei in enumerate(gas_prices):
        chosen = adaptive_choices[t]
        ca += (schemes[chosen]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cf5 += (schemes["Falcon-512"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cml += (schemes["ML-DSA-44"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cf10 += (schemes["Falcon-1024"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cml87 += (schemes["ML-DSA-87"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        
        cum_adaptive.append(ca)
        cum_f512.append(cf5)
        cum_ml44.append(cml)
        cum_f1024.append(cf10)
        cum_ml87.append(cml87)
        
    ax2.plot(hours, cum_ml87, label='Static ML-DSA-87 (Level 5)', color='darkred', linestyle=':')
    ax2.plot(hours, cum_f1024, label='Static Falcon-1024 (Level 5)', color='purple', linestyle='--')
    ax2.plot(hours, cum_ml44, label='Static ML-DSA-44 (Level 2)', color='coral', linestyle='--')
    ax2.plot(hours, cum_f512, label='Static Falcon-512 (Level 1)', color='orange', linestyle='--')
    ax2.plot(hours, cum_adaptive, label='PQ-Oracle Adaptive Engine (Dynamic Level 1-5)', color='green', linewidth=2.5)
    
    ax2.set_xlabel("Time (Hours)", fontweight='bold')
    ax2.set_ylabel("Cumulative Cost ($ USD)", fontweight='bold')
    ax2.set_title("24-Hour Cumulative Operational Cost Comparison", fontweight='bold', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend()
    
    plt.suptitle("PQ-Oracle Phase 4: Dynamic Adaptive Selection Policy Engine", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plot_path = os.path.join("results", "pq_oracle_adaptive_policy.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Adaptive policy plot saved to {plot_path}")

def main():
    gas_prices, choices, results, ta, tf5, tml, tf10, tml87, schemes = simulate_24h_oracle_feed()
    generate_adaptive_plots(gas_prices, choices, ta, tf5, tml, tf10, tml87, schemes)

if __name__ == "__main__":
    main()
