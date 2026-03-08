"""
Enterprise NGFW - Web Application Firewall (WAF) Plugin

Inspects HTTP/HTTPS payloads for web-based attacks like SQLi, XSS,
and Command Injection based on OWASP Top 10.
"""

import re
import urllib.parse
import logging
from dataclasses import dataclass
from typing import List
from ..framework.plugin_base import InspectorPlugin, InspectionContext, InspectionFinding, InspectionResult, InspectionAction


@dataclass
class WAFRule:
    id: str
    name: str
    pattern: re.Pattern
    severity: str   # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'
    category: str

class WAFInspectorPlugin(InspectorPlugin):
    """Inspects HTTP traffic for web vulnerabilities."""
    
    def __init__(self, block_on_match: bool = True):
        super().__init__(name="waf_inspector", priority=50)
        self.block_on_match = block_on_match
        
        # Define basic WAF rules (Simplified for demo, in prod use ModSecurity rules)
        self.rules: List[WAFRule] = [
            # SQL Injection (Very basic)
            WAFRule(
                id="WAF_SQLI_1",
                name="Basic SQL Injection",
                pattern=re.compile(rb'(?i)(UNION\s+SELECT|SELECT\s+.*\s+FROM|INSERT\s+INTO|UPDATE\s+.*\s+SET|DROP\s+TABLE)'),
                severity="CRITICAL",
                category="SQL Injection"
            ),
            # Cross-Site Scripting (XSS)
            WAFRule(
                id="WAF_XSS_1",
                name="Basic XSS",
                pattern=re.compile(rb'(?i)(<script.*?>.*?</script>|javascript:|onerror=|onload=)'),
                severity="HIGH",
                category="Cross-Site Scripting"
            ),
            # Local File Inclusion (LFI)
            WAFRule(
                id="WAF_LFI_1",
                name="Directory Traversal / LFI",
                pattern=re.compile(rb'(?i)(\.\.\/\.\.\/|etc/passwd|windows/system32/cmd\.exe)'),
                severity="CRITICAL",
                category="Local File Inclusion"
            ),
            # Command Injection
            WAFRule(
                id="WAF_CMD_1",
                name="Command Injection",
                pattern=re.compile(rb'(?i)(;\s*ls\s+-|;\s*cat\s+|;\s*wget\s+|;\s*curl\s+|\|\s*sh\s*)'),
                severity="CRITICAL",
                category="Command Injection"
            )
        ]


    def can_inspect(self, context: InspectionContext) -> bool:
        """WAF targets HTTP/HTTPS traffic (ports 80, 443, 8080, 8443)"""
        return context.dst_port in (80, 443, 8080, 8443) or context.src_port in (80, 443, 8080, 8443)

    async def initialize(self) -> None:
        pass
        
    async def shutdown(self) -> None:
        pass
        
    def inspect(self, context: InspectionContext, data: bytes) -> InspectionResult:
        findings = []
        
        # WAF primarily targets inbound HTTP/HTTPS traffic to protected servers
        if context.direction == "outbound" and not context.metadata.get("inspect_outbound_waf", False):
            return InspectionResult(action=InspectionAction.ALLOW, findings=[])
            
        # Decode URL encoding to prevent evasion
        try:
            decoded_data = urllib.parse.unquote_to_bytes(data)
        except Exception:
            decoded_data = data
            
        for rule in self.rules:
            # Check original data
            if rule.pattern.search(data) or rule.pattern.search(decoded_data):
                findings.append(
                    InspectionFinding(
                        plugin_name=self.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=f"WAF Rule Triggered: {rule.name}",
                        confidence=0.9,
                        recommends_block=self.block_on_match,
                        metadata={"rule_id": rule.id}
                    )
                )
        
        should_block = self.block_on_match and bool(findings)
        action = InspectionAction.BLOCK if should_block else InspectionAction.ALLOW
        return InspectionResult(action=action, findings=findings)
