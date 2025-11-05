"""
Recommendation Engine package.

This package provides intelligent cost optimization recommendations
with ML-based predictions, scoring, and prioritization.
"""

from src.recommendations.engine import RecommendationEngine
from src.recommendations.generator import RecommendationGenerator
from src.recommendations.predictor import CostPredictor
from src.recommendations.scorer import RecommendationScorer
from src.recommendations.trend_analyzer import TrendAnalyzer

__all__ = [
    "RecommendationEngine",
    "RecommendationGenerator",
    "CostPredictor",
    "RecommendationScorer",
    "TrendAnalyzer",
]
