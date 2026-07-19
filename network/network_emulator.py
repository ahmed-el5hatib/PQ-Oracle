"""
PQ-Oracle: Phase 5 Network Emulator
Simulates real-world network layer phenomena including latency, jitter, packet loss,
duplication, out-of-order delivery, and node disconnects.
"""

import asyncio
import random
import time
from typing import Callable, Awaitable, Set, Optional

from nodes.oracle_node import OracleMessage

class NetworkLayer:
    def __init__(
        self,
        latency_ms: float = 10.0,
        jitter_ms: float = 2.0,
        packet_loss_rate: float = 0.02,
        duplicate_rate: float = 0.01,
        out_of_order_rate: float = 0.01
    ):
        self.latency_ms = latency_ms
        self.jitter_ms = jitter_ms
        self.packet_loss_rate = packet_loss_rate
        self.duplicate_rate = duplicate_rate
        self.out_of_order_rate = out_of_order_rate
        self.offline_nodes: Set[int] = set()
        self.total_bytes_transmitted: int = 0
        self.total_packets_transmitted: int = 0
        self.total_packets_lost: int = 0

    def set_node_online_status(self, node_id: int, online: bool) -> None:
        if online:
            self.offline_nodes.discard(node_id)
        else:
            self.offline_nodes.add(node_id)

    async def send_message(
        self,
        msg: OracleMessage,
        destination_callback: Callable[[OracleMessage], Awaitable[None]]
    ) -> bool:
        if msg.node_id in self.offline_nodes:
            self.total_packets_lost += 1
            return False

        # Packet Loss Simulation
        if random.random() < self.packet_loss_rate:
            self.total_packets_lost += 1
            return False

        # Calculate Latency + Jitter
        jitter = random.uniform(-self.jitter_ms, self.jitter_ms)
        delay_sec = max(0.001, (self.latency_ms + jitter) / 1000.0)

        # Out of Order Delivery Simulation
        if random.random() < self.out_of_order_rate:
            delay_sec += random.uniform(0.02, 0.05)

        # Record bandwidth & packet stats
        msg_bytes = len(msg.signature) + len(msg.public_key) + 64
        self.total_bytes_transmitted += msg_bytes
        self.total_packets_transmitted += 1

        async def delayed_deliver():
            await asyncio.sleep(delay_sec)
            await destination_callback(msg)
            
            # Packet Duplication Simulation
            if random.random() < self.duplicate_rate:
                await asyncio.sleep(0.005)
                await destination_callback(msg)

        asyncio.create_task(delayed_deliver())
        return True

    def reset_stats(self) -> None:
        self.total_bytes_transmitted = 0
        self.total_packets_transmitted = 0
        self.total_packets_lost = 0
