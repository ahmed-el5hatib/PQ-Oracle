import time
import statistics
import csv
import os
import oqs
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from py_ecc.bls import G2ProofOfPossession as bls
import matplotlib.pyplot as plt

MESSAGE = b"oracle_price_update_payload_eth_usd_1850.50_timestamp_1750000000"
N_TRIALS = 100

def benchmark_ecdsa():
    keygen_times, sign_times, verify_times = [], [], []
    pub_key_bytes = b""
    signature = b""
    
    for _ in range(N_TRIALS):
        t0 = time.perf_counter()
        priv_key = ec.generate_private_key(ec.SECP256K1())
        keygen_times.append(time.perf_counter() - t0)
        
        pub_key = priv_key.public_key()
        pub_key_bytes = pub_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        t0 = time.perf_counter()
        signature = priv_key.sign(MESSAGE, ec.ECDSA(hashes.SHA256()))
        sign_times.append(time.perf_counter() - t0)
        
        t0 = time.perf_counter()
        pub_key.verify(signature, MESSAGE, ec.ECDSA(hashes.SHA256()))
        verify_times.append(time.perf_counter() - t0)
        
    return {
        "Category": "Baseline (Classical)",
        "Algorithm": "ECDSA (secp256k1)",
        "Security_Level": "Classical 128-bit",
        "Public_Key_Size_Bytes": len(pub_key_bytes),
        "Signature_Size_Bytes": len(signature),
        "Avg_Keygen_ms": statistics.mean(keygen_times) * 1000,
        "Avg_Sign_ms": statistics.mean(sign_times) * 1000,
        "Avg_Verify_ms": statistics.mean(verify_times) * 1000
    }

def benchmark_bls():
    keygen_times, sign_times, verify_times = [], [], []
    pub_key_bytes = b""
    signature = b""
    
    for i in range(1, N_TRIALS + 1):
        t0 = time.perf_counter()
        sk = i + 100
        pub_key_bytes = bls.SkToPk(sk)
        keygen_times.append(time.perf_counter() - t0)
        
        t0 = time.perf_counter()
        signature = bls.Sign(sk, MESSAGE)
        sign_times.append(time.perf_counter() - t0)
        
        t0 = time.perf_counter()
        bls.Verify(pub_key_bytes, MESSAGE, signature)
        verify_times.append(time.perf_counter() - t0)
        
    return {
        "Category": "Baseline (Classical)",
        "Algorithm": "BLS12-381",
        "Security_Level": "Classical 128-bit",
        "Public_Key_Size_Bytes": len(pub_key_bytes),
        "Signature_Size_Bytes": len(signature),
        "Avg_Keygen_ms": statistics.mean(keygen_times) * 1000,
        "Avg_Sign_ms": statistics.mean(sign_times) * 1000,
        "Avg_Verify_ms": statistics.mean(verify_times) * 1000
    }

def benchmark_oqs(alg_name, category, sec_level):
    keygen_times, sign_times, verify_times = [], [], []
    pub_key = b""
    signature = b""
    
    with oqs.Signature(alg_name) as signer:
        for _ in range(N_TRIALS):
            t0 = time.perf_counter()
            pub_key = signer.generate_keypair()
            keygen_times.append(time.perf_counter() - t0)
            
            t0 = time.perf_counter()
            signature = signer.sign(MESSAGE)
            sign_times.append(time.perf_counter() - t0)
            
            with oqs.Signature(alg_name) as verifier:
                t0 = time.perf_counter()
                verifier.verify(MESSAGE, signature, pub_key)
                verify_times.append(time.perf_counter() - t0)

    return {
        "Category": category,
        "Algorithm": alg_name,
        "Security_Level": sec_level,
        "Public_Key_Size_Bytes": len(pub_key),
        "Signature_Size_Bytes": len(signature),
        "Avg_Keygen_ms": statistics.mean(keygen_times) * 1000,
        "Avg_Sign_ms": statistics.mean(sign_times) * 1000,
        "Avg_Verify_ms": statistics.mean(verify_times) * 1000
    }

def generate_plots(results):
    os.makedirs("results", exist_ok=True)
    
    algs = [r["Algorithm"] for r in results]
    sig_sizes = [r["Signature_Size_Bytes"] for r in results]
    verify_times = [r["Avg_Verify_ms"] for r in results]
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Signature Algorithm', fontweight='bold')
    ax1.set_ylabel('Signature Size (Bytes)', color=color, fontweight='bold')
    bars = ax1.bar(algs, sig_sizes, color=color, alpha=0.6, width=0.4, label='Signature Size (B)')
    ax1.tick_params(axis='y', labelcolor=color)
    plt.xticks(rotation=25, ha='right')
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Verification Time (ms)', color=color, fontweight='bold')
    lines = ax2.plot(algs, verify_times, color=color, marker='o', linewidth=2, label='Verify Time (ms)')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('PQ-Oracle Phase 1: Signature Size vs Verification Time Overhead', fontsize=14, fontweight='bold')
    fig.tight_layout()
    plot_path = os.path.join("results", "pq_oracle_baseline_comparison.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Plot saved to {plot_path}")

def main():
    os.makedirs("results", exist_ok=True)
    results = []
    
    print("Benchmarking ECDSA...")
    results.append(benchmark_ecdsa())
    
    print("Benchmarking BLS12-381...")
    results.append(benchmark_bls())
    
    pqc_algs = [
        ("ML-DSA-44", "PQ - Lattice", "NIST Level 2"),
        ("ML-DSA-65", "PQ - Lattice", "NIST Level 3"),
        ("ML-DSA-87", "PQ - Lattice", "NIST Level 5"),
        ("Falcon-512", "PQ - Lattice", "NIST Level 1"),
        ("Falcon-1024", "PQ - Lattice", "NIST Level 5"),
        ("SLH_DSA_PURE_SHA2_128S", "PQ - Hash-based", "NIST Level 1"),
    ]
    
    for alg, cat, sec in pqc_algs:
        print(f"Benchmarking {alg}...")
        results.append(benchmark_oqs(alg, cat, sec))
        
    csv_path = os.path.join("results", "pq_oracle_baseline_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Results saved to {csv_path}")
    generate_plots(results)

if __name__ == "__main__":
    main()
