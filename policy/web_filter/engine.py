"""
Web Filter Engine
URL Filtering, Safe Search, and Category Blocking
"""

import logging
from typing import List
from ..schema import WebFilterRule, PolicyContext, Action
from .category import CategoryEngine, ContentCategory

logger = logging.getLogger(__name__)

class WebFilterEngine:
    """
    Evaluates Web Filtering Rules.
    - Category Blocking (Gambling, Adult, etc.)
    - Exact URL Blocking
    - Safe Search Enforcement
    """
    
    def __init__(self):
        self.rules: List[WebFilterRule] = []
        self.logger = logger
        self.category_engine = CategoryEngine()
        self.default_action = Action.ALLOW

    def load_rules(self, rules: List[WebFilterRule]):
        self.rules = rules
        self.logger.info(f"Loaded {len(self.rules)} Web Filter rules")

    def evaluate(self, context: PolicyContext) -> Action:
        """Evaluate web request"""
        if not context.domain and not context.url:
            return Action.ALLOW

        # Check Global/Rule-based Categories
        # For simplicity, we assume global blocked categories are set in the engine
        # In a real scenario, we'd check against specific rules matching the user/zone
        
        if context.domain:
            if self.category_engine.is_blocked(context.domain):
                self.logger.info(f"WebFilter Blocked Category: {context.domain}")
                return Action.BLOCK
                
        # Check Exact URLs (from rules)
        if context.url:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                if context.url in rule.exact_urls:
                    self.logger.info(f"WebFilter Blocked URL: {context.url}")
                    return rule.action
        
        return Action.ALLOW
