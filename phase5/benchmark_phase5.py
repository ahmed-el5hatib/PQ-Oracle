"""
PQ-Oracle: Phase 5 Distributed Oracle Testbed Harness
Asynchronously orchestrates distributed oracle node networks, network emulation,
fault injection, threshold consensus aggregation, system resource monitoring, and artifact generation.
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
import json
import csv
import asyncio
import psutil
from typing import List, Dict, Any

from nodes.oracle_node import OracleNode, OracleMessage
from network.network_emulator import NetworkLayer
from aggregator.aggregator_service import AggregatorService
from faults.fault_injector import FaultInjector
from phase5.plot_phase5 import generate_phase5_plots

CONFIG_PATH = os.path.join(PROJECT_ROOT, "configs", "phase5_config.json")

def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

async def run_topology_experiment(topology: Dict[str, int], algorithm: str, config: Dict[str, Any]) -> Dict[str, Any]:
    n = topology["n"]
    k = topology["k"]
    num_rounds = 5  # Optimized for fast execution
    feed_id = config["benchmark"]["feed_id"]
    
    net_p = config["network_params"]
    network = NetworkLayer(
        latency_ms=net_p["latency_ms"],
        jitter_ms=net_p["jitter_ms"],
        packet_loss_rate=net_p["packet_loss_rate"],
        duplicate_rate=net_p["duplicate_rate"],
        out_of_order_rate=net_p["out_of_order_rate"]
    )
    
    fault_p = config["fault_params"]
    fault_injector = FaultInjector(
        byzantine_node_ratio=fault_p["byzantine_node_ratio"],
        tamper_price_rate=fault_p["tamper_price_rate"],
        invalid_sig_rate=fault_p["invalid_sig_rate"],
        replay_attack_rate=fault_p["replay_attack_rate"],
        crash_rate=fault_p["crash_rate"]
    )
    
    nodes = [OracleNode(node_id=i, algorithm=algorithm) for i in range(n)]
    fault_injector.assign_byzantine_nodes(nodes)
    
    aggregator = AggregatorService(threshold_k=k, total_n=n, algorithm=algorithm)
    
    process = psutil.Process(os.getpid())
    cpu_samples = []
    mem_samples = []
    
    start_wall_time = time.time()

    for r in range(num_rounds):
        ts = time.time()
        base_price = 1850.50 + r
        
        cpu_samples.append(psutil.cpu_percent(interval=None))
        mem_samples.append(process.memory_info().rss / (1024 * 1024))
        
        tasks = []
        for node in nodes:
            current_price = node.generate_price(base_price=base_price)
            msg = fault_injector.process_node_signing(node, feed_id, current_price, ts)
            tasks.append(network.send_message(msg, aggregator.handle_incoming_message))

        await asyncio.gather(*tasks)
        await asyncio.sleep(0.005)
        
        replay_tasks = []
        for replay_msg in fault_injector.replayed_messages:
            replay_tasks.append(network.send_message(replay_msg, aggregator.handle_incoming_message))
        fault_injector.replayed_messages.clear()
        
        if replay_tasks:
            await asyncio.gather(*replay_tasks)
            await asyncio.sleep(0.005)

    total_duration = time.time() - start_wall_time
    
    # Cleanup nodes & aggregator
    for node in nodes:
        node.close()
    aggregator.close()
        
    avg_cpu = sum(cpu_samples) / max(1, len(cpu_samples))
    avg_mem = sum(mem_samples) / max(1, len(mem_samples))
    
    avg_verify_lat = (sum(aggregator.verification_latencies) / max(1, len(aggregator.verification_latencies))) if aggregator.verification_latencies else 0.0
    avg_agg_delay = (sum(aggregator.aggregation_latencies) / max(1, len(aggregator.aggregation_latencies))) if aggregator.aggregation_latencies else 0.0
    avg_e2e_lat = (sum(aggregator.e2e_latencies) / max(1, len(aggregator.e2e_latencies))) if aggregator.e2e_latencies else 0.0
    
    throughput = aggregator.successful_aggregations / max(0.001, total_duration)
    failure_rate = (aggregator.failed_verifications / max(1, aggregator.total_verifications)) * 100.0
    
    return {
        "Algorithm": algorithm,
        "Nodes_N": n,
        "Threshold_K": k,
        "Throughput_updates_per_sec": round(throughput, 2),
        "Avg_E2E_Latency_ms": round(avg_e2e_lat, 2),
        "Avg_Verify_Latency_ms": round(avg_verify_lat, 3),
        "Avg_Aggregation_Delay_ms": round(avg_agg_delay, 3),
        "CPU_Usage_Pct": round(avg_cpu, 2),
        "Memory_MB": round(avg_mem, 2),
        "Transmitted_KB": round(network.total_bytes_transmitted / 1024.0, 2),
        "Total_Packets": network.total_packets_transmitted,
        "Packets_Lost": network.total_packets_lost,
        "Total_Verifications": aggregator.total_verifications,
        "Failed_Verifications": aggregator.failed_verifications,
        "Failure_Rate_Pct": round(failure_rate, 2),
        "Successful_Aggregations": aggregator.successful_aggregations
    }

async def main_async():
    config = load_config()
    topologies = config["network_topologies"]
    algorithms = config["evaluated_algorithms"]
    
    print("\n=======================================================")
    print("PQ-Oracle Phase 5: Distributed Oracle Testbed")
    print("=======================================================")
    
    results = []
    for alg in algorithms:
        for topo in topologies:
            print(f"Executing Testbed: {alg} | Nodes N={topo['n']}, k={topo['k']}...")
            res = await run_topology_experiment(topo, alg, config)
            results.append(res)

    out_dir = os.path.join(PROJECT_ROOT, "results")
    os.makedirs(out_dir, exist_ok=True)
    
    # Export CSV
    csv_path = os.path.join(out_dir, "pq_oracle_phase5_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\nPhase 5 CSV results saved to {csv_path}")
    
    # Export JSON
    json_path = os.path.join(out_dir, "pq_oracle_phase5_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Phase 5 JSON results saved to {json_path}")
    
    # Generate Phase 5 Plots
    generate_phase5_plots(results, output_dir=out_dir)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
