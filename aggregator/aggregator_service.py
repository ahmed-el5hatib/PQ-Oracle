"""
PQ-Oracle: Phase 5 Aggregator Service
Collects, verifies, and aggregates signed oracle reports across N consensus nodes,
enforcing k-of-N threshold consensus and recording performance metrics.
"""

import time
import math
import asyncio
from typing import Dict, List, Set, Tuple, Optional

import oqs
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from py_ecc.bls import G2ProofOfPossession as bls

from nodes.oracle_node import OracleMessage

class AggregatorService:
    def __init__(self, threshold_k: int, total_n: int, algorithm: str = "Falcon-512"):
        self.threshold_k = threshold_k
        self.total_n = total_n
        self.algorithm = algorithm
        
        self.oqs_verifier = None
        if self.algorithm not in ["ECDSA (secp256k1)", "BLS12-381"]:
            oqs_name = self._get_oqs_name(self.algorithm)
            self.oqs_verifier = oqs.Signature(oqs_name)
            
        self.received_messages: Dict[str, List[OracleMessage]] = {}
        self.verified_messages: Dict[str, List[OracleMessage]] = {}
        
        # Metrics
        self.total_verifications: int = 0
        self.failed_verifications: int = 0
        self.successful_aggregations: int = 0
        self.consensus_timeouts: int = 0
        self.verification_latencies: List[float] = []
        self.aggregation_latencies: List[float] = []
        self.e2e_latencies: List[float] = []

    def _get_oqs_name(self, alg: str) -> str:
        mapping = {
            "ML-DSA-44": "ML-DSA-44",
            "ML-DSA-65": "ML-DSA-65",
            "ML-DSA-87": "ML-DSA-87",
            "Falcon-512": "Falcon-512",
            "Falcon-1024": "Falcon-1024",
            "SLH-DSA-SHA2-128s": "SPHINCS+-SHA2-128s-simple"
        }
        return mapping.get(alg, alg)

    def verify_message_signature(self, msg: OracleMessage) -> bool:
        t0 = time.perf_counter()
        self.total_verifications += 1
        
        if msg.is_replayed:
            self.failed_verifications += 1
            return False

        payload = f"{msg.feed_id}:{msg.price}:{msg.timestamp}".encode('utf-8')
        is_valid = False

        try:
            if msg.algorithm == "ECDSA (secp256k1)":
                pub_key = serialization.load_der_public_key(msg.public_key)
                pub_key.verify(msg.signature, payload, ec.ECDSA(hashes.SHA256()))
                is_valid = True
            elif msg.algorithm == "BLS12-381":
                is_valid = bls.Verify(msg.public_key, payload, msg.signature)
            else:
                oqs_name = self._get_oqs_name(msg.algorithm)
                with oqs.Signature(oqs_name) as verifier:
                    is_valid = verifier.verify(payload, msg.signature, msg.public_key)
        except Exception:
            is_valid = False

        v_time = (time.perf_counter() - t0) * 1000.0
        self.verification_latencies.append(v_time)

        if not is_valid:
            self.failed_verifications += 1

        return is_valid

    async def handle_incoming_message(self, msg: OracleMessage) -> Optional[Dict]:
        feed_key = f"{msg.feed_id}:{msg.timestamp}"
        
        if feed_key not in self.received_messages:
            self.received_messages[feed_key] = []
            self.verified_messages[feed_key] = []

        self.received_messages[feed_key].append(msg)
        
        if self.verify_message_signature(msg):
            self.verified_messages[feed_key].append(msg)

        valid_msgs = self.verified_messages[feed_key]
        if len(valid_msgs) >= self.threshold_k and feed_key not in self.received_messages.get(f"done_{feed_key}", []):
            return self.aggregate_report(feed_key, valid_msgs)

        return None

    def aggregate_report(self, feed_key: str, valid_msgs: List[OracleMessage]) -> Dict:
        t0 = time.perf_counter()
        
        prices = [m.price for m in valid_msgs]
        prices.sort()
        median_price = prices[len(prices) // 2]

        base_sig_len = len(valid_msgs[0].signature)
        if valid_msgs[0].algorithm == "BLS12-381":
            agg_sig_bytes = 96 + (len(valid_msgs) * 4)
        elif "ML-DSA" in valid_msgs[0].algorithm:
            agg_sig_bytes = base_sig_len + int(128 * math.log2(len(valid_msgs))) + (len(valid_msgs) * 4)
        elif "Falcon" in valid_msgs[0].algorithm:
            agg_sig_bytes = base_sig_len + int(160 * math.log2(len(valid_msgs))) + (len(valid_msgs) * 4)
        elif "SLH-DSA" in valid_msgs[0].algorithm:
            agg_sig_bytes = base_sig_len + int(256 * math.log2(len(valid_msgs))) + (len(valid_msgs) * 4)
        else:
            agg_sig_bytes = len(valid_msgs) * (base_sig_len + 4)

        agg_time = (time.perf_counter() - t0) * 1000.0
        self.aggregation_latencies.append(agg_time)
        self.successful_aggregations += 1

        first_ts = valid_msgs[0].timestamp
        e2e_latency = (time.time() - first_ts) * 1000.0
        self.e2e_latencies.append(e2e_latency)

        return {
            "feed_key": feed_key,
            "median_price": median_price,
            "num_valid_signatures": len(valid_msgs),
            "threshold_k": self.threshold_k,
            "agg_payload_bytes": agg_sig_bytes,
            "aggregation_time_ms": round(agg_time, 3),
            "e2e_latency_ms": round(e2e_latency, 3)
        }

    def close(self) -> None:
        if self.oqs_verifier is not None:
            self.oqs_verifier.free()
            self.oqs_verifier = None
