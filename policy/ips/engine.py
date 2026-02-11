"""
Intrusion Prevention System (IPS) Engine
Coordinats Signature-based and Anomaly-based detection.
"""

import logging
from typing import List, Optional
from ..schema import IPSRule, PolicyContext, Action
from .threat_intel import ThreatIntelligence, ThreatLevel
from .reputation import ReputationEngine, ReputationLevel

# Placeholder for AI Anomaly Detector
# from ...ml.inference.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

class IPSEngine:
    """
    Intrusion Prevention System.
    Layers:
    1. Threat Intelligence (Known Bad IPs/Domains)
    2. Reputation Check
    3. Signature Matching (Snort-like rules)
    4. AI Anomaly Detection (Behavioral)
    """
    
    def __init__(self):
        self.rules: List[IPSRule] = []
        self.logger = logger
        self.threat_intel = ThreatIntelligence()
        self.reputation = ReputationEngine()
        # self.ai_detector = AnomalyDetector()
        self.default_action = Action.ALLOW

    def load_rules(self, rules: List[IPSRule]):
        self.rules = rules
        self.logger.info(f"Loaded {len(self.rules)} IPS rules")

    def evaluate(self, context: PolicyContext) -> Action:
        # 1. Threat Intelligence Check
        is_threat, threat_info = self.threat_intel.is_threat(context.src_ip, 'ip')
        if is_threat and threat_info.threat_level >= ThreatLevel.HIGH:
            self.logger.warning(f"IPS Blocked Threat: {context.src_ip} ({threat_info.source})")
            return Action.BLOCK
            
        # 2. Reputation Check
        rep = self.reputation.get_ip_reputation(context.src_ip)
        if rep.score <= ReputationLevel.MALICIOUS:
            self.logger.warning(f"IPS Blocked Low Reputation: {context.src_ip} ({rep.score})")
            return Action.BLOCK
            
        # 3. Signature/Rule Checks (Placeholder)
        # for rule in self.rules: ...
        
        # 4. AI Anomaly Detection (Future Integration)
        # if self.ai_detector.predict(context) ...
        
        return Action.ALLOW
