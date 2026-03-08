"""
Enterprise NGFW - Data Loss Prevention (DLP) Plugin

Scans payloads for sensitive information like Credit Cards, SSNs, and 
confidential keywords to prevent data exfiltration.
"""

import re
import logging
from dataclasses import dataclass
from typing import List
from ..framework.plugin_base import InspectorPlugin, InspectionContext, InspectionFinding, InspectionResult, InspectionAction


@dataclass
class DLPRule:
    id: str
    name: str
    pattern: re.Pattern
    severity: str   # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'
    description: str

class DLPInspectorPlugin(InspectorPlugin):
    """Inspects traffic for sensitive data leaks."""
    
    def __init__(self, block_on_match: bool = True):
        super().__init__(name="dlp_inspector", priority=60)
        self.block_on_match = block_on_match
        
        # Define basic DLP rules
        self.rules: List[DLPRule] = [
            # Visa, MasterCard, Amex patterns
            DLPRule(
                id="DLP_CREDIT_CARD",
                name="Credit Card Number",
                pattern=re.compile(rb'\b(?:\d[ -]*?){13,16}\b'),
                severity="HIGH",
                description="Potential credit card number detected in payload"
            ),
            # US Social Security Number (basic format)
            DLPRule(
                id="DLP_SSN",
                name="Social Security Number",
                pattern=re.compile(rb'\b\d{3}-\d{2}-\d{4}\b'),
                severity="HIGH",
                description="Potential US SSN detected in payload"
            ),
            DLPRule(
                id="DLP_CONFIDENTIAL",
                name="Confidential Keyword",
                pattern=re.compile(rb'(?i)\b(?:confidential|strictly private|internal use only|do not distribute)\b'),
                severity="MEDIUM",
                description="Confidential keywords detected in payload"
            )
        ]

        
    def can_inspect(self, context: InspectionContext) -> bool:
        """DLP runs on all traffic, skip inbound unless configured"""
        return True

    async def initialize(self) -> None:
        pass
        
    async def shutdown(self) -> None:
        pass
        
    def inspect(self, context: InspectionContext, data: bytes) -> InspectionResult:
        findings = []
        
        # Only inspect outbound traffic if specified, or all traffic
        if context.direction == "inbound" and not context.metadata.get("inspect_inbound_dlp", False):
            return InspectionResult(action=InspectionAction.ALLOW, findings=[])
            
        for rule in self.rules:
            matches = rule.pattern.findall(data)
            if matches:
                findings.append(
                    InspectionFinding(
                        plugin_name=self.name,
                        severity=rule.severity,
                        category="DLP",
                        description=f"{rule.description} (Matched {len(matches)} times)",
                        confidence=0.8,
                        recommends_block=self.block_on_match,
                        metadata={"rule_id": rule.id, "match_count": len(matches)}
                    )
                )
        
        should_block = self.block_on_match and bool(findings)
        action = InspectionAction.BLOCK if should_block else InspectionAction.ALLOW
        return InspectionResult(action=action, findings=findings)
