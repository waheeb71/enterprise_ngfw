"""
IPS Signatures
Signature-based detection.
"""

from typing import List, NamedTuple
import re

class Signature(NamedTuple):
    sid: int
    msg: str
    protocol: str
    pattern: bytes
    
class SignatureEngine:
    """Simple Signature Matcher"""
    
    def __init__(self):
        self.signatures: List[Signature] = []
        
    def load_defaults(self):
        # Example dummy signatures
        self.signatures.append(Signature(1001, "SQL Injection", "tcp", b"UNION SELECT"))
        self.signatures.append(Signature(1002, "Path Traversal", "http", b"../.."))
        
    def scan(self, payload: bytes) -> List[str]:
        alerts = []
        for sig in self.signatures:
            if sig.pattern in payload:
                alerts.append(f"[{sig.sid}] {sig.msg}")
        return alerts
