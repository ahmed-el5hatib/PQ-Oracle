"""
PQ-Oracle: Phase 5 Fault Injector
Provides configurable fault injection for testing consensus resiliency under Byzantine nodes,
price tampering, invalid signatures, replay attacks, and node crashes.
"""

import random
import time
from typing import Set, Dict, Any, List
from nodes.oracle_node import OracleNode, OracleMessage

class FaultInjector:
    def __init__(
        self,
        byzantine_node_ratio: float = 0.1,
        tamper_price_rate: float = 0.05,
        invalid_sig_rate: float = 0.05,
        replay_attack_rate: float = 0.02,
        crash_rate: float = 0.02
    ):
        self.byzantine_node_ratio = byzantine_node_ratio
        self.tamper_price_rate = tamper_price_rate
        self.invalid_sig_rate = invalid_sig_rate
        self.replay_attack_rate = replay_attack_rate
        self.crash_rate = crash_rate
        self.byzantine_nodes: Set[int] = set()
        self.replayed_messages: List[OracleMessage] = []

    def assign_byzantine_nodes(self, nodes: List[OracleNode]) -> None:
        num_byzantine = int(len(nodes) * self.byzantine_node_ratio)
        if num_byzantine > 0:
            byz_nodes = random.sample(nodes, num_byzantine)
            for node in byz_nodes:
                self.byzantine_nodes.add(node.node_id)

    def process_node_signing(self, node: OracleNode, feed_id: str, current_price: float, timestamp: float) -> OracleMessage:
        is_byzantine = node.node_id in self.byzantine_nodes
        price = current_price
        corrupt_sig = False

        if is_byzantine:
            # Tamper price
            if random.random() < self.tamper_price_rate:
                price = current_price * random.choice([0.5, 1.5, 2.0])
            # Corrupt signature
            if random.random() < self.invalid_sig_rate:
                corrupt_sig = True

        msg = node.sign_payload(feed_id, price, timestamp, corrupt_sig=corrupt_sig)
        msg.is_byzantine = is_byzantine or corrupt_sig or (price != current_price)

        # Replay attack capture
        if random.random() < self.replay_attack_rate and not msg.is_byzantine:
            replay_msg = OracleMessage(
                feed_id=msg.feed_id,
                price=msg.price,
                timestamp=msg.timestamp - 300,  # Old timestamp replay
                node_id=msg.node_id,
                algorithm=msg.algorithm,
                signature=msg.signature,
                public_key=msg.public_key,
                is_replayed=True
            )
            self.replayed_messages.append(replay_msg)

        return msg
