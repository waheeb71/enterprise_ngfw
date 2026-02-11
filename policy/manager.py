"""
Enterprise NGFW Policy Manager
Central orchestrator for all policy decisions.
"""

import logging
from typing import Optional, List, Dict
from dataclasses import dataclass
from .schema import PolicyContext, Action
from .access_control.acl_engine import ACLEngine
from .app_control.engine import AppControlEngine
from .web_filter.engine import WebFilterEngine
from .ips.engine import IPSEngine

logger = logging.getLogger(__name__)

class PolicyManager:
    """
    Central Policy Decision Point (PDP).
    Aggregates decisions from ACL, AppControl, IPS, WebFilter.
    """
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
        # Initialize specialized engines
        self.acl_engine = ACLEngine()
        self.app_engine = AppControlEngine()
        self.web_engine = WebFilterEngine()
        self.ips_engine = IPSEngine()
        
        # Load policies (Mock)
        self.load_policies()
        
        logger.info("Policy Manager initialized with all engines")

    def load_policies(self):
        """Load policies from database/file"""
        logger.info("Loading policies...")
        # TODO: Load from JSON/DB and pass to engines
        # self.acl_engine.load_rules(...)
        # self.app_engine.load_rules(...)
        pass

    def evaluate(self, context: PolicyContext) -> Action:
        """
        Evaluate a flow against all active policies.
        Order of operations:
        1. Access Control (L3/L4) -> Fast path
        2. IPS Inspection (Threat Intel/Reputation)
        3. App Control & Web Filter (L7)
        """
        
        # 1. Access Control (L3/L4)
        acl_action = self.acl_engine.evaluate(context)
        if acl_action == Action.BLOCK:
            return Action.BLOCK
        
        # 2. Intrusion Prevention (L7/Reputation)
        ips_action = self.ips_engine.evaluate(context)
        if ips_action == Action.BLOCK:
            return Action.BLOCK
            
        # 3. Deep Inspection (L7)
        # App Control
        # App Control
        # Always call App Control - it might resolve App ID from SNI
        app_action = self.app_engine.evaluate(context)
        if app_action == Action.BLOCK:
            return Action.BLOCK
            
        # Web Filter
        if context.domain or context.url:
            web_action = self.web_engine.evaluate(context)
            if web_action == Action.BLOCK:
                return Action.BLOCK
                
        # Default action
        return Action.ALLOW

    def reload(self):
        """Reload all policies"""
        self.load_policies()
