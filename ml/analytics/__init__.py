"""
Enterprise NGFW - Predictive Analytics Layer

Provides attack forecasting and traffic trend analysis capabilities.
"""

from .predictive import AttackForecaster, TrendAnalyzer
from .vulnerability_scorer import VulnerabilityPredictor

__all__ = [
    'AttackForecaster',
    'TrendAnalyzer',
    'VulnerabilityPredictor'
]
