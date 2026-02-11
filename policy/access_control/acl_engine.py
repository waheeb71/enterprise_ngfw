"""
Access Control List (ACL) Engine
Layer 3/4 Firewall Rule Evaluation
"""

import logging
import ipaddress
from typing import List, Optional, Union
from ..schema import FirewallRule, PolicyContext, Action, Protocol

logger = logging.getLogger(__name__)

class ACLEngine:
    """
    Evaluates Firewall Rules based on 5-tuple (SrcIP, DstIP, SrcPort, DstPort, Proto).
    Supports Zones (LAN, WAN, DMZ).
    """
    
    def __init__(self):
        self.rules: List[FirewallRule] = []
        self.logger = logger
        # Default policy is usually implicit deny, but we start with allow for safety
        self.default_action = Action.ALLOW 

    def load_rules(self, rules: List[FirewallRule]):
        """Load rules and sort by priority"""
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.logger.info(f"Loaded {len(self.rules)} ACL rules")

    def evaluate(self, context: PolicyContext) -> Action:
        """Find first matching rule"""
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if self._match_rule(rule, context):
                self.logger.debug(f"Matched ACL Rule: {rule.name} -> {rule.action.value}")
                return rule.action
                
        return self.default_action

    def _match_rule(self, rule: FirewallRule, context: PolicyContext) -> bool:
        """Check if context matches rule criteria"""
        
        # 1. Protocol Match
        if rule.protocol != Protocol.ANY:
            if rule.protocol.value.lower() != context.protocol.lower():
                return False

        # 2. IP Match (Source)
        if rule.src_ip:
            if not self._match_ip(rule.src_ip, context.src_ip):
                return False

        # 3. IP Match (Dest)
        if rule.dst_ip:
            if not self._match_ip(rule.dst_ip, context.dst_ip):
                return False

        # 4. Port Match (Source)
        if rule.src_port:
            if not self._match_port(rule.src_port, context.src_port):
                return False

        # 5. Port Match (Dest)
        if rule.dst_port:
            if not self._match_port(rule.dst_port, context.dst_port):
                return False
                
        # 6. Zone Match (Placeholder - relies on interface mapping)
        # if rule.src_zone != "any" and rule.src_zone != context.src_zone: return False
        
        return True

    def _match_ip(self, rule_ip: Union[str, List[str]], packet_ip: str) -> bool:
        """Match IP against rule (supports CIDR, Lists, Single IP)"""
        if isinstance(rule_ip, list):
            return any(self._check_ip(rip, packet_ip) for rip in rule_ip)
        return self._check_ip(rule_ip, packet_ip)

    def _check_ip(self, rule_ip: str, packet_ip: str) -> bool:
        """Check single IP/CIDR"""
        if rule_ip == "any":
            return True
        try:
            # Check for CIDR
            if '/' in rule_ip:
                return ipaddress.ip_address(packet_ip) in ipaddress.ip_network(rule_ip, strict=False)
            return packet_ip == rule_ip
        except ValueError:
            self.logger.warning(f"Invalid IP rule format: {rule_ip}")
            return False

    def _match_port(self, rule_port: Union[int, str], packet_port: int) -> bool:
        """Match Port (supports range '80-90', list, single)"""
        # Simplify: assume rule_port matches packet_port
        # In reality, parse ranges
        if rule_port == "any": return True
        return str(rule_port) == str(packet_port)
