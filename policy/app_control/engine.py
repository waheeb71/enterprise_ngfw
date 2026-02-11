"""
Application Control Engine
Layer 7 Policy Enforcement
"""

import logging
from typing import List

from ..schema import AppRule, PolicyContext, Action
from .signatures import EncryptedAppSignatures

logger = logging.getLogger(__name__)

class AppControlEngine:
    """
    Evaluates Application Control Rules.
    Focuses on identified applications (Facebook, WhatsApp, TikTok)
    regardless of port/protocol.
    """
    
    def __init__(self):
        self.rules: List[AppRule] = []
        self.logger = logger
        self.default_action = Action.ALLOW

    def load_rules(self, rules: List[AppRule]):
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.logger.info(f"Loaded {len(self.rules)} App Control rules")

    def evaluate(self, context: PolicyContext) -> Action:
        """Evaluate identified application against rules"""
        
        # Try to identify App ID if not present
        if not context.app_id and context.domain:
            context.app_id = EncryptedAppSignatures.identify_by_sni(context.domain)
            if context.app_id:
                self.logger.debug(f"Identified App: {context.app_id} from SNI: {context.domain}")

        if not context.app_id:
            return Action.ALLOW

        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if self._match_rule(rule, context):
                self.logger.info(f"Matched App Rule: {rule.name} [{context.app_id}] -> {rule.action.value}")
                return rule.action
                
        return self.default_action

    def _match_rule(self, rule: AppRule, context: PolicyContext) -> bool:
        # Match application name
        if rule.application != "any" and rule.application.lower() != context.app_id.lower():
            return False
            
        # Match User/Group (if user_id available)
        if rule.users and context.user_id:
            if context.user_id not in rule.users:
                # TODO: Check groups as well
                return False
        
        return True
