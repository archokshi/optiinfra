"""
Cost Predictor Module.

Provides ML-based cost forecasting using time series analysis.
Uses simple statistical methods for MVP (can upgrade to ML models later).
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)


class CostPredictor:
    """ML-based cost prediction and forecasting."""
    
    def __init__(self):
        """Initialize cost predictor."""
        self.default_confidence = 0.95
    
    async def predict_future_costs(
        self,
        cost_history: List[Dict[str, Any]],
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Predict future costs using time series forecasting.
        
        Args:
            cost_history: Historical cost data
            forecast_days: Number of days to forecast
        
        Returns:
            Cost forecast with confidence intervals
        """
        try:
            if len(cost_history) < 7:
                logger.warning("Insufficient data for forecasting")
                return self._create_empty_forecast(forecast_days)
            
            # Extract cost values
            costs = [entry.get("cost", 0) for entry in cost_history]
            
            # Detect trend
            trend_direction, growth_rate = self._detect_trend(costs)
            
            # Choose forecasting method based on data characteristics
            if len(costs) >= 30:
                # Use linear trend for longer history
                forecast = self._linear_trend_forecast(costs, forecast_days)
                model_used = "linear_trend"
            else:
                # Use moving average for shorter history
                forecast = self._moving_average_forecast(costs, forecast_days)
                model_used = "moving_average"
            
            # Calculate confidence intervals
            lower_bound, upper_bound = self._calculate_confidence_intervals(
                costs, forecast, self.default_confidence
            )
            
            # Create weekly and monthly aggregates
            weekly_forecast = self._aggregate_weekly(forecast)
            monthly_forecast = [sum(forecast)]
            
            return {
                "customer_id": cost_history[0].get("customer_id", "unknown") if cost_history else "unknown",
                "forecast_start_date": date.today(),
                "forecast_end_date": date.today() + timedelta(days=forecast_days),
                "daily_forecast": forecast,
                "weekly_forecast": weekly_forecast,
                "monthly_forecast": monthly_forecast,
                "daily_lower_bound": lower_bound,
                "daily_upper_bound": upper_bound,
                "confidence_level": self.default_confidence,
                "trend_direction": trend_direction,
                "growth_rate_percent": growth_rate,
                "model_used": model_used,
                "forecast_accuracy": None,  # Would be calculated from historical validation
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error predicting costs: {e}", exc_info=True)
            return self._create_empty_forecast(forecast_days)
    
    async def predict_savings(
        self,
        recommendation: Dict[str, Any],
        cost_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict savings from implementing a recommendation.
        
        Args:
            recommendation: Recommendation to evaluate
            cost_history: Historical cost data
        
        Returns:
            Savings forecast
        """
        try:
            monthly_savings = recommendation.get("monthly_savings", 0)
            implementation_cost = recommendation.get("implementation_cost", 0)
            
            # Calculate savings timeline
            savings_start_date = date.today() + timedelta(days=7)  # 1 week to implement
            full_savings_date = savings_start_date + timedelta(days=30)  # Full savings after 1 month
            
            # Calculate confidence based on recommendation type
            confidence = self._calculate_savings_confidence(recommendation)
            
            # Calculate confidence interval (±20% for medium confidence)
            interval_width = monthly_savings * 0.2
            confidence_interval = (
                monthly_savings - interval_width,
                monthly_savings + interval_width
            )
            
            return {
                "recommendation_id": recommendation.get("recommendation_id"),
                "monthly_savings": monthly_savings,
                "annual_savings": monthly_savings * 12,
                "three_year_savings": monthly_savings * 36,
                "savings_start_date": savings_start_date,
                "full_savings_date": full_savings_date,
                "confidence_level": confidence,
                "confidence_interval": confidence_interval,
                "assumptions": self._get_savings_assumptions(recommendation),
                "risk_factors": recommendation.get("risk_factors", [])
            }
            
        except Exception as e:
            logger.error(f"Error predicting savings: {e}", exc_info=True)
            return {}
    
    def _detect_trend(self, costs: List[float]) -> Tuple[str, float]:
        """
        Detect cost trend direction and growth rate.
        
        Returns:
            (trend_direction, growth_rate_percent)
        """
        if len(costs) < 2:
            return "stable", 0.0
        
        # Simple linear regression
        x = np.arange(len(costs))
        y = np.array(costs)
        
        # Calculate slope
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            return "stable", 0.0
        
        slope = numerator / denominator
        
        # Calculate growth rate as percentage
        avg_cost = np.mean(costs)
        if avg_cost > 0:
            growth_rate = (slope / avg_cost) * 100
        else:
            growth_rate = 0.0
        
        # Determine trend direction
        if abs(growth_rate) < 1.0:
            trend_direction = "stable"
        elif growth_rate > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
        
        return trend_direction, growth_rate
    
    def _moving_average_forecast(
        self,
        costs: List[float],
        forecast_days: int,
        window: int = 7
    ) -> List[float]:
        """
        Forecast using moving average.
        
        Args:
            costs: Historical costs
            forecast_days: Days to forecast
            window: Moving average window size
        
        Returns:
            Forecasted costs
        """
        if len(costs) < window:
            window = len(costs)
        
        # Calculate moving average
        ma = np.mean(costs[-window:])
        
        # Simple forecast: repeat moving average
        forecast = [ma] * forecast_days
        
        return forecast
    
    def _linear_trend_forecast(
        self,
        costs: List[float],
        forecast_days: int
    ) -> List[float]:
        """
        Forecast using linear trend extrapolation.
        
        Args:
            costs: Historical costs
            forecast_days: Days to forecast
        
        Returns:
            Forecasted costs
        """
        x = np.arange(len(costs))
        y = np.array(costs)
        
        # Fit linear trend
        coefficients = np.polyfit(x, y, 1)
        slope, intercept = coefficients
        
        # Forecast future values
        future_x = np.arange(len(costs), len(costs) + forecast_days)
        forecast = slope * future_x + intercept
        
        # Ensure non-negative costs
        forecast = np.maximum(forecast, 0)
        
        return forecast.tolist()
    
    def _exponential_smoothing(
        self,
        costs: List[float],
        alpha: float = 0.3
    ) -> float:
        """
        Exponential smoothing for short-term forecast.
        
        Args:
            costs: Historical costs
            alpha: Smoothing parameter (0-1)
        
        Returns:
            Smoothed forecast value
        """
        if not costs:
            return 0.0
        
        result = costs[0]
        for cost in costs[1:]:
            result = alpha * cost + (1 - alpha) * result
        
        return result
    
    def _calculate_confidence_intervals(
        self,
        historical_costs: List[float],
        forecast: List[float],
        confidence_level: float
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate confidence intervals for forecast.
        
        Args:
            historical_costs: Historical cost data
            forecast: Forecasted values
            confidence_level: Confidence level (e.g., 0.95)
        
        Returns:
            (lower_bound, upper_bound)
        """
        # Calculate historical standard deviation
        std_dev = np.std(historical_costs)
        
        # Z-score for confidence level (approximate)
        if confidence_level >= 0.95:
            z_score = 1.96
        elif confidence_level >= 0.90:
            z_score = 1.645
        else:
            z_score = 1.0
        
        # Calculate bounds
        margin = z_score * std_dev
        lower_bound = [max(0, f - margin) for f in forecast]
        upper_bound = [f + margin for f in forecast]
        
        return lower_bound, upper_bound
    
    def _aggregate_weekly(self, daily_forecast: List[float]) -> List[float]:
        """Aggregate daily forecast into weekly totals."""
        weekly = []
        for i in range(0, len(daily_forecast), 7):
            week_total = sum(daily_forecast[i:i+7])
            weekly.append(week_total)
        return weekly
    
    def _calculate_savings_confidence(
        self,
        recommendation: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence level for savings prediction.
        
        Based on recommendation type and risk level.
        """
        rec_type = recommendation.get("recommendation_type", "")
        risk_level = recommendation.get("risk_level", "medium")
        
        # Base confidence by type
        type_confidence = {
            "terminate": 0.95,
            "hibernate": 0.85,
            "right_size": 0.75,
            "spot": 0.70,
            "ri": 0.90,
            "auto_scale": 0.70,
            "storage_optimize": 0.80,
        }.get(rec_type, 0.70)
        
        # Adjust by risk level
        risk_adjustment = {
            "low": 0.0,
            "medium": -0.05,
            "high": -0.10
        }.get(risk_level, -0.05)
        
        confidence = type_confidence + risk_adjustment
        return max(0.5, min(0.99, confidence))
    
    def _get_savings_assumptions(
        self,
        recommendation: Dict[str, Any]
    ) -> List[str]:
        """Get assumptions for savings calculation."""
        assumptions = [
            "Current usage patterns continue",
            "No significant workload changes",
            "Implementation completed as planned"
        ]
        
        rec_type = recommendation.get("recommendation_type", "")
        
        if rec_type == "spot":
            assumptions.append("Workload can tolerate interruptions")
            assumptions.append("Spot availability remains consistent")
        elif rec_type == "ri":
            assumptions.append("Commitment period is fulfilled")
            assumptions.append("No early termination")
        elif rec_type == "auto_scale":
            assumptions.append("Scaling policies are properly configured")
            assumptions.append("Application supports horizontal scaling")
        
        return assumptions
    
    def _create_empty_forecast(self, forecast_days: int) -> Dict[str, Any]:
        """Create empty forecast when data is insufficient."""
        return {
            "customer_id": "unknown",
            "forecast_start_date": date.today(),
            "forecast_end_date": date.today() + timedelta(days=forecast_days),
            "daily_forecast": [0.0] * forecast_days,
            "weekly_forecast": [0.0] * ((forecast_days + 6) // 7),
            "monthly_forecast": [0.0],
            "daily_lower_bound": [0.0] * forecast_days,
            "daily_upper_bound": [0.0] * forecast_days,
            "confidence_level": 0.0,
            "trend_direction": "unknown",
            "growth_rate_percent": 0.0,
            "model_used": "none",
            "forecast_accuracy": None,
            "generated_at": datetime.utcnow()
        }
    
    def detect_seasonality(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect seasonal patterns in cost data.
        
        Args:
            cost_history: Historical cost data
        
        Returns:
            Seasonality analysis
        """
        if len(cost_history) < 28:  # Need at least 4 weeks
            return {
                "has_daily_pattern": False,
                "has_weekly_pattern": False,
                "has_monthly_pattern": False,
                "patterns": {}
            }
        
        costs = [entry.get("cost", 0) for entry in cost_history]
        
        # Check for weekly pattern (day of week)
        weekly_pattern = self._detect_weekly_pattern(cost_history)
        
        return {
            "has_daily_pattern": False,  # Would need hourly data
            "has_weekly_pattern": weekly_pattern is not None,
            "has_monthly_pattern": False,  # Would need 12+ months
            "patterns": {
                "weekly": weekly_pattern
            }
        }
    
    def _detect_weekly_pattern(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Detect weekly patterns (weekday vs weekend)."""
        try:
            # Group by day of week
            by_day = {i: [] for i in range(7)}
            
            for entry in cost_history:
                entry_date = entry.get("date")
                if isinstance(entry_date, str):
                    entry_date = datetime.fromisoformat(entry_date).date()
                elif isinstance(entry_date, datetime):
                    entry_date = entry_date.date()
                
                if entry_date:
                    day_of_week = entry_date.weekday()
                    by_day[day_of_week].append(entry.get("cost", 0))
            
            # Calculate average by day
            pattern = {}
            for day, costs in by_day.items():
                if costs:
                    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    pattern[day_names[day]] = sum(costs) / len(costs)
            
            return pattern if pattern else None
            
        except Exception as e:
            logger.error(f"Error detecting weekly pattern: {e}")
            return None
