"""
Recommendation Engine Core.

Main orchestration layer that coordinates all recommendation components.
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.recommendations.generator import RecommendationGenerator
from src.recommendations.predictor import CostPredictor
from src.recommendations.scorer import RecommendationScorer
from src.recommendations.trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Main recommendation engine orchestrator."""
    
    def __init__(self, metrics_client=None):
        """
        Initialize recommendation engine.
        
        Args:
            metrics_client: ClickHouse metrics client (optional)
        """
        self.generator = RecommendationGenerator()
        self.predictor = CostPredictor()
        self.scorer = RecommendationScorer()
        self.trend_analyzer = TrendAnalyzer(metrics_client)
        self.metrics_client = metrics_client
    
    async def generate_recommendations(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for recommendation generation.
        
        Args:
            request: RecommendationEngineRequest dict
        
        Returns:
            RecommendationEngineResponse dict
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            customer_id = request.get("customer_id")
            analysis_report = request.get("analysis_report", {})
            include_predictions = request.get("include_predictions", True)
            include_trends = request.get("include_trends", True)
            forecast_days = request.get("forecast_days", 30)
            max_recommendations = request.get("max_recommendations", 50)
            min_monthly_savings = request.get("min_monthly_savings", 10.0)
            
            logger.info(f"Generating recommendations for customer {customer_id}")
            
            # Step 1: Fetch historical data
            historical_data = await self._fetch_historical_data(
                customer_id,
                forecast_days
            ) if include_trends else None
            
            # Step 2: Generate recommendations
            recommendations = self.generator.generate_recommendations(
                analysis_report,
                historical_data
            )
            
            logger.info(f"Generated {len(recommendations)} raw recommendations")
            
            # Step 3: Filter by minimum savings
            recommendations = [
                r for r in recommendations
                if r.get("monthly_savings", 0) >= min_monthly_savings
                or r.get("recommendation_type") in ["security_fix", "config_fix", "investigate"]
            ]
            
            # Step 4: Score recommendations
            scoring_weights = {
                "roi": request.get("roi_weight", 0.40),
                "risk": request.get("risk_weight", 0.20),
                "urgency": request.get("urgency_weight", 0.25),
                "impact": request.get("impact_weight", 0.15)
            }
            
            scored_recommendations = self.scorer.score_recommendations(
                recommendations,
                context={},
                weights=scoring_weights
            )
            
            # Step 5: Limit to max recommendations
            scored_recommendations = scored_recommendations[:max_recommendations]
            
            # Step 6: Predict future costs (if requested)
            cost_forecast = None
            if include_predictions and historical_data and "cost_history" in historical_data:
                cost_forecast = await self.predictor.predict_future_costs(
                    historical_data["cost_history"],
                    forecast_days
                )
            
            # Step 7: Analyze trends (if requested)
            trend_analysis = None
            if include_trends:
                trend_analysis = await self.trend_analyzer.analyze_cost_trends(
                    customer_id,
                    forecast_days
                )
            
            # Step 8: Calculate total potential savings
            total_potential_savings = sum(
                rec["recommendation"].get("monthly_savings", 0)
                for rec in scored_recommendations
            )
            
            # Step 9: Categorize recommendations
            categorized = self._categorize_recommendations(scored_recommendations)
            
            # Step 10: Build response
            processing_time = time.time() - start_time
            
            response = {
                "request_id": request_id,
                "customer_id": customer_id,
                "timestamp": datetime.utcnow(),
                "total_recommendations": len(scored_recommendations),
                "scored_recommendations": scored_recommendations,
                "cost_forecast": cost_forecast,
                "total_potential_savings": total_potential_savings,
                "trend_analysis": trend_analysis,
                "quick_wins": categorized["quick_wins"],
                "strategic_initiatives": categorized["strategic"],
                "long_term_opportunities": categorized["long_term"],
                "processing_time_seconds": processing_time,
                "success": True,
                "error_message": None
            }
            
            logger.info(
                f"Successfully generated {len(scored_recommendations)} recommendations "
                f"with ${total_potential_savings:.2f}/month potential savings "
                f"in {processing_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            
            return {
                "request_id": request_id,
                "customer_id": request.get("customer_id", "unknown"),
                "timestamp": datetime.utcnow(),
                "total_recommendations": 0,
                "scored_recommendations": [],
                "cost_forecast": None,
                "total_potential_savings": 0.0,
                "trend_analysis": None,
                "quick_wins": [],
                "strategic_initiatives": [],
                "long_term_opportunities": [],
                "processing_time_seconds": processing_time,
                "success": False,
                "error_message": str(e)
            }
    
    async def _fetch_historical_data(
        self,
        customer_id: str,
        days: int
    ) -> Dict[str, Any]:
        """
        Fetch historical cost and usage data.
        
        Args:
            customer_id: Customer identifier
            days: Number of days of history
        
        Returns:
            Historical data dict
        """
        try:
            # Fetch cost history
            cost_history = await self.trend_analyzer._fetch_cost_history(
                customer_id,
                days
            )
            
            # Fetch usage history
            usage_history = await self.trend_analyzer._fetch_usage_history(
                customer_id,
                days
            )
            
            return {
                "cost_history": cost_history,
                "usage_history": usage_history
            }
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return {}
    
    def _categorize_recommendations(
        self,
        scored_recommendations: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize recommendations into quick wins, strategic, and long-term.
        
        Args:
            scored_recommendations: List of scored recommendations
        
        Returns:
            Dict with categorized recommendations
        """
        quick_wins = []
        strategic = []
        long_term = []
        
        for rec in scored_recommendations:
            category = rec.get("category", "long_term")
            
            if category == "quick_win":
                quick_wins.append(rec)
            elif category == "strategic":
                strategic.append(rec)
            else:
                long_term.append(rec)
        
        return {
            "quick_wins": quick_wins,
            "strategic": strategic,
            "long_term": long_term
        }
