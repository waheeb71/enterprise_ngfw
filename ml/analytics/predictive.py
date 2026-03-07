"""
Enterprise NGFW - Predictive Analytics

Provides attack forecasting and trend analysis using
time-series forecasting algorithms.
"""

import logging
import time
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class ForecastResult:
    """Attack forecast result"""
    timestamp: float
    horizon_hours: int
    attack_probabilities: Dict[str, float] = field(default_factory=dict)
    expected_traffic_bps: float = 0.0
    risk_level: str = "LOW"
    confidence: float = 0.0

class TrendAnalyzer:
    """Analyzes traffic trends using simple moving averages and exponential smoothing."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.history = []
        self.max_history = 1000
        
    def add_data_point(self, value: float) -> None:
        """Add a data point to history."""
        self.history.append({
            'timestamp': time.time(),
            'value': value
        })
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
    def get_trend(self) -> float:
        """Calculate recent trend (slope of the moving average)."""
        if len(self.history) < 10:
            return 0.0
            
        recent = self.history[-10:]
        older = self.history[-20:-10]
        
        if not older:
            return 0.0
            
        recent_avg = sum(p['value'] for p in recent) / len(recent)
        older_avg = sum(p['value'] for p in older) / len(older)
        
        return (recent_avg - older_avg) / (older_avg + 1e-6)

class AttackForecaster:
    """
    Predicts future attacks based on current trends and historical data.
    In a real-world scenario, this would use LSTM or Prophet. Here we use
    a simplified heuristic model based on trends.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.trend_analyzer = TrendAnalyzer(self.logger)
        self.attack_history: Dict[str, List[float]] = {
            'DDoS': [],
            'Malware': [],
            'Scanning': [],
            'Intrusion': []
        }
        
    def record_attack(self, attack_type: str) -> None:
        """Record an attack occurrence for forecasting."""
        if attack_type not in self.attack_history:
            self.attack_history[attack_type] = []
            
        self.attack_history[attack_type].append(time.time())
        
        # Keep only last 24 hours
        cutoff = time.time() - 86400
        self.attack_history[attack_type] = [
            t for t in self.attack_history[attack_type] if t > cutoff
        ]
        
    def forecast(self, current_traffic_bps: float, horizon_hours: int = 1) -> ForecastResult:
        """Forecast future attack probabilities."""
        self.trend_analyzer.add_data_point(current_traffic_bps)
        traffic_trend = self.trend_analyzer.get_trend()
        
        result = ForecastResult(
            timestamp=time.time(),
            horizon_hours=horizon_hours,
            expected_traffic_bps=current_traffic_bps * (1.0 + traffic_trend)
        )
        
        # Heuristic rules for forecasting
        for attack_type, history in self.attack_history.items():
            # Base probability on frequency in last 24 hours
            freq = len(history)
            base_prob = min(freq / 100.0, 0.4)
            
            # Recency factor
            if history:
                time_since_last = time.time() - history[-1]
                recency_weight = math.exp(-time_since_last / 3600)  # Decay over hours
                base_prob += 0.3 * recency_weight
                
            # Traffic trend factor
            if attack_type == 'DDoS' and traffic_trend > 0.2:
                # Sudden traffic spike increases DDoS probability
                base_prob += 0.4
                
            result.attack_probabilities[attack_type] = min(max(base_prob, 0.0), 1.0)
            
        # Determine overall risk level
        max_prob = max(result.attack_probabilities.values()) if result.attack_probabilities else 0.0
        
        if max_prob > 0.8:
            result.risk_level = "CRITICAL"
        elif max_prob > 0.5:
            result.risk_level = "HIGH"
        elif max_prob > 0.3:
            result.risk_level = "MEDIUM"
        else:
            result.risk_level = "LOW"
            
        result.confidence = 0.75  # Heuristic confidence
        
        return result
