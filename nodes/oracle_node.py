"""
PQ-Oracle: Phase 5 Distributed Oracle Node
Independent oracle node process simulation. Each node holds an independent keypair
and signs price updates.
"""

import time
import secrets
import dataclasses
from typing import Dict, Any, Optional

import oqs
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from py_ecc.bls import G2ProofOfPossession as bls
from py_ecc.optimized_bls12_381 import curve_order as bls_curve_order

@dataclasses.dataclass
class OracleMessage:
    feed_id: str
    price: float
    timestamp: float
    node_id: int
    algorithm: str
    signature: bytes
    public_key: bytes
    is_byzantine: bool = False
    is_replayed: bool = False

class OracleNode:
    def __init__(self, node_id: int, algorithm: str = "Falcon-512"):
        self.node_id = node_id
        self.algorithm = algorithm
        self.public_key: bytes = b""
        self.private_key: Any = None
        self.signer_ctx: Any = None
        self.is_online: bool = True
        self._generate_keypair()

    def _generate_keypair(self) -> None:
        if self.algorithm == "ECDSA (secp256k1)":
            self.private_key = ec.generate_private_key(ec.SECP256K1())
            pub = self.private_key.public_key()
            from cryptography.hazmat.primitives import serialization
            self.public_key = pub.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        elif self.algorithm == "BLS12-381":
            self.private_key = secrets.randbelow(bls_curve_order - 1) + 1
            self.public_key = bls.SkToPk(self.private_key)
        else:
            # PQC Algorithm via OQS
            oqs_name = self._get_oqs_name(self.algorithm)
            self.signer_ctx = oqs.Signature(oqs_name)
            self.public_key = self.signer_ctx.generate_keypair()

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

    def generate_price(self, base_price: float = 1850.50, volatility: float = 2.0) -> float:
        delta = (secrets.randbelow(200) - 100) / 100.0 * volatility
        return round(base_price + delta, 2)

    def sign_payload(self, feed_id: str, price: float, timestamp: float, corrupt_sig: bool = False) -> OracleMessage:
        payload = f"{feed_id}:{price}:{timestamp}".encode('utf-8')
        
        if self.algorithm == "ECDSA (secp256k1)":
            sig = self.private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
        elif self.algorithm == "BLS12-381":
            sig = bls.Sign(self.private_key, payload)
        else:
            sig = self.signer_ctx.sign(payload)

        if corrupt_sig:
            sig = bytearray(sig)
            if len(sig) > 0:
                sig[0] ^= 0xFF
            sig = bytes(sig)

        return OracleMessage(
            feed_id=feed_id,
            price=price,
            timestamp=timestamp,
            node_id=self.node_id,
            algorithm=self.algorithm,
            signature=sig,
            public_key=self.public_key,
            is_byzantine=corrupt_sig
        )

    def close(self) -> None:
        if self.signer_ctx is not None:
            self.signer_ctx.free()
            self.signer_ctx = None
