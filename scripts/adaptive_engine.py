import os
import csv
import math
import random
import matplotlib.pyplot as plt

# Candidate scheme parameters: (Name, Gas_Agg_N21, Latency_ms, Security_Score 1-5)
SCHEMES = {
    "ECDSA": {"gas": 95528, "latency": 6.47, "security": 1.0, "pqc": False},
    "BLS12-381": {"gas": 100472, "latency": 550.0, "security": 1.0, "pqc": False},
    "Falcon-512": {"gas": 383391, "latency": 0.38, "security": 3.0, "pqc": True},
    "Falcon-1024": {"gas": 526710, "latency": 0.73, "security": 5.0, "pqc": True},
    "ML-DSA-44": {"gas": 512362, "latency": 0.78, "security": 3.0, "pqc": True},
    "ML-DSA-87": {"gas": 895420, "latency": 2.08, "security": 5.0, "pqc": True},
}

ETH_PRICE_USD = 3000.0

def adaptive_policy(gas_price_gwei, max_cost_usd_target, max_latency_ms, require_pqc=True):
    """
    PQ-Oracle Adaptive Policy Selector:
    Selects the optimal cryptographic signature scheme based on real-time gas price,
    latency SLA, and post-quantum security requirements.
    """
    best_scheme = None
    best_score = float('-inf')

    for name, s in SCHEMES.items():
        if require_pqc and not s["pqc"]:
            continue
        
        tx_cost_usd = (s["gas"] * gas_price_gwei * 1e-9) * ETH_PRICE_USD
        
        # Hard constraint check: latency budget
        if s["latency"] > max_latency_ms:
            continue
            
        # Multi-objective utility score:
        # Score = Security Weight - Normalized Cost Penalty
        cost_penalty = (tx_cost_usd / max_cost_usd_target) if max_cost_usd_target > 0 else 0
        utility_score = (s["security"] * 2.0) - (cost_penalty * 3.0)
        
        if utility_score > best_score:
            best_score = utility_score
            best_scheme = name
            
    # Fallback to Falcon-512 if no PQC scheme meets strict constraint
    if best_scheme is None and require_pqc:
        best_scheme = "Falcon-512"
    elif best_scheme is None:
        best_scheme = "ECDSA"
        
    return best_scheme

def simulate_24h_oracle_feed():
    os.makedirs("results", exist_ok=True)
    random.seed(42)
    
    # 24 hours simulation with 1 update per minute (1440 updates)
    time_steps = 1440
    gas_prices = []
    
    # Simulate realistic gas volatility (base 20 Gwei, spikes up to 120 Gwei)
    current_gas = 25.0
    for t in range(time_steps):
        # Peak congestion hours (hours 12-16)
        hour = (t // 60) % 24
        if 12 <= hour <= 16:
            current_gas += random.uniform(-2, 5)
        else:
            current_gas += random.uniform(-3, 3)
            
        current_gas = max(12.0, min(140.0, current_gas))
        gas_prices.append(current_gas)

    results = []
    
    # Trackers for total costs
    total_cost_adaptive = 0.0
    total_cost_static_mldsa = 0.0
    total_cost_static_falcon512 = 0.0
    total_cost_static_falcon1024 = 0.0
    
    adaptive_choices = []
    
    for t, gwei in enumerate(gas_prices):
        # Target max budget per update: $50 USD, max latency: 50ms
        chosen_scheme = adaptive_policy(gwei, max_cost_usd_target=50.0, max_latency_ms=50.0, require_pqc=True)
        adaptive_choices.append(chosen_scheme)
        
        cost_adaptive = (SCHEMES[chosen_scheme]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cost_mldsa44 = (SCHEMES["ML-DSA-44"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cost_falcon512 = (SCHEMES["Falcon-512"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cost_falcon1024 = (SCHEMES["Falcon-1024"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        
        total_cost_adaptive += cost_adaptive
        total_cost_static_mldsa += cost_mldsa44
        total_cost_static_falcon512 += cost_falcon512
        total_cost_static_falcon1024 += cost_falcon1024
        
        if t % 60 == 0:  # Hourly snapshot
            results.append({
                "Hour": t // 60,
                "Gas_Price_Gwei": round(gwei, 2),
                "Chosen_Scheme": chosen_scheme,
                "Adaptive_Cost_USD": round(cost_adaptive, 2),
                "MLDSA44_Static_Cost_USD": round(cost_mldsa44, 2),
                "Falcon512_Static_Cost_USD": round(cost_falcon512, 2),
                "Falcon1024_Static_Cost_USD": round(cost_falcon1024, 2),
            })
            
    print(f"24h Operational Cost Summary (1,440 price updates):")
    print(f"  - PQ-Oracle Adaptive Engine: ${total_cost_adaptive:,.2f}")
    print(f"  - Static Falcon-512:         ${total_cost_static_falcon512:,.2f}")
    print(f"  - Static ML-DSA-44:          ${total_cost_static_mldsa:,.2f}")
    print(f"  - Static Falcon-1024 (L5):   ${total_cost_static_falcon1024:,.2f}")
    
    csv_path = os.path.join("results", "pq_oracle_adaptive_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Adaptive simulation saved to {csv_path}")
    
    return gas_prices, adaptive_choices, results, total_cost_adaptive, total_cost_static_falcon512, total_cost_static_mldsa, total_cost_static_falcon1024

def generate_adaptive_plots(gas_prices, adaptive_choices, total_adaptive, total_f512, total_ml44, total_f1024):
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    hours = [t / 60 for t in range(len(gas_prices))]
    
    # Subplot 1: Gas Price fluctuations & Chosen Algorithm
    ax1 = axes[0]
    ax1.plot(hours, gas_prices, color='firebrick', linewidth=1.5, label='EVM Gas Price (Gwei)')
    ax1.set_ylabel("Gas Price (Gwei)", fontweight='bold', color='firebrick')
    ax1.set_title("EVM Gas Price Volatility & Adaptive PQC Scheme Selection", fontweight='bold', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Subplot 2: Cumulative Operational Cost Comparison
    ax2 = axes[1]
    cum_adaptive = []
    cum_f512 = []
    cum_ml44 = []
    cum_f1024 = []
    
    ca, cf5, cml, cf10 = 0, 0, 0, 0
    for t, gwei in enumerate(gas_prices):
        chosen = adaptive_choices[t]
        ca += (SCHEMES[chosen]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cf5 += (SCHEMES["Falcon-512"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cml += (SCHEMES["ML-DSA-44"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        cf10 += (SCHEMES["Falcon-1024"]["gas"] * gwei * 1e-9) * ETH_PRICE_USD
        
        cum_adaptive.append(ca)
        cum_f512.append(cf5)
        cum_ml44.append(cml)
        cum_f1024.append(cf10)
        
    ax2.plot(hours, cum_f1024, label='Static Falcon-1024 (Level 5)', color='purple', linestyle='--')
    ax2.plot(hours, cum_ml44, label='Static ML-DSA-44 (Level 2)', color='coral', linestyle='--')
    ax2.plot(hours, cum_f512, label='Static Falcon-512 (Level 1)', color='orange', linestyle='--')
    ax2.plot(hours, cum_adaptive, label='PQ-Oracle Adaptive Engine', color='green', linewidth=2.5)
    
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
    gas_prices, choices, results, ta, tf5, tml, tf10 = simulate_24h_oracle_feed()
    generate_adaptive_plots(gas_prices, choices, ta, tf5, tml, tf10)

if __name__ == "__main__":
    main()
