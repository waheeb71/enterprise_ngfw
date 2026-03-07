"""
Enterprise NGFW - AI Inspector Plugin

Uses Deep Learning models to classify traffic patterns and detect anomalies.
Integrates with the central DeepTrafficClassifier.
"""

import logging
import time
import math
from typing import Optional, Dict, Any

from ..framework.plugin_base import InspectorPlugin, InspectionContext, PluginPriority, InspectionFinding, InspectionResult, InspectionAction



from ml.inference.deep_learning import DeepTrafficClassifier, ThreatCategory


class AIInspector(InspectorPlugin):
    """
    AI-based Traffic Inspector
    
    Uses DeepTrafficClassifier to analyze traffic patterns.
    """
    
    def __init__(
        self,
        classifier: DeepTrafficClassifier,
        priority: PluginPriority = PluginPriority.NORMAL,
        logger: Optional[logging.Logger] = None
    ):
        super().__init__("ai_inspector", priority, logger)
        self.classifier = classifier
        self.threshold = 0.8
        
    def can_inspect(self, context: InspectionContext) -> bool:
        """Inspect all traffic, but maybe skip trusted internal flows later"""
        return True
        
    def inspect(
        self,
        context: InspectionContext,
        data: bytes
    ) -> InspectionResult:
        """
        Analyze traffic features using Deep Learning
        """
        result = InspectionResult(action=InspectionAction.ALLOW)
        
        # 1. Extract features (simplified for real-time)
        features = self._extract_features(context, data)
        
        # 2. Classify
        classification = self.classifier.classify(features)
        
        # 3. Decision
        if classification.category != ThreatCategory.NORMAL:
            # Check confidence
            if classification.confidence >= self.threshold:
                result.action = InspectionAction.BLOCK
                
                result.findings.append(InspectionFinding(
                    severity='HIGH',
                    category=classification.category.value,
                    description=f"AI detected {classification.category.value} pattern",
                    plugin_name=self.name,
                    confidence=classification.confidence,
                    evidence=classification.probabilities
                ))
                
                result.metadata['ai_model'] = classification.model_name
                result.metadata['ai_latency_ms'] = classification.latency_ms
                
        return result
        
    def _extract_features(self, context: InspectionContext, data: bytes) -> Dict[str, float]:
        """
        Extract features for the ML model.
        
        In a real scenario, this would aggregate flow statistics.
        Here we approximate some features from the single packet/chunk + context.
        """
        # Basic features
        size = len(data)
        
        # TCP/UDP ratio (mock approximation based on protocol)
        is_tcp = 1.0 if context.protocol == 'TCP' else 0.0
        is_udp = 1.0 if context.protocol == 'UDP' else 0.0
        
        # Entropy (measure of randomness/encryption)
        entropy = self._calculate_entropy(data) if size > 0 else 0.0
        
        return {
            'pps': 100.0,  # Placeholder: requires flow tracking state
            'bps': size * 8.0,
            'avg_size': float(size),
            'size_var': 0.0,  # Requires tracking
            'tcp_ratio': is_tcp,
            'udp_ratio': is_udp,
            'syn_ratio': 0.0,
            'unique_dst': 1.0,
            'unique_src': 1.0,
            'iat_mean': 0.1,  # Inter-arrival time placeholder
            'iat_var': 0.0,
            'failed_conn': 0.0,
            'conn_attempts': 1.0,
            'reputation': 100.0, # Could fetch from context.metadata if available
            'entropy': entropy
        }
        
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
            
        byte_counts = [0] * 256
        for b in data:
            byte_counts[b] += 1
            
        entropy = 0.0
        total = len(data)
        
        for count in byte_counts:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
                
        return entropy
