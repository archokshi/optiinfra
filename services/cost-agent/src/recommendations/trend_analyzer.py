"""
Trend Analyzer Module.

Analyzes historical cost and usage trends to identify patterns and opportunities.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes historical trends in cost and usage data."""
    
    def __init__(self, metrics_client=None):
        """
        Initialize trend analyzer.
        
        Args:
            metrics_client: ClickHouse metrics client (optional)
        """
        self.metrics_client = metrics_client
    
    async def analyze_cost_trends(
        self,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze cost trends over time.
        
        Args:
            customer_id: Customer identifier
            days: Number of days to analyze
        
        Returns:
            Trend analysis results
        """
        try:
            # Fetch historical data
            cost_history = await self._fetch_cost_history(customer_id, days)
            
            if not cost_history or len(cost_history) < 7:
                logger.warning(f"Insufficient data for trend analysis: {len(cost_history)} days")
                return self._create_empty_trend_analysis(customer_id, days)
            
            # Extract costs
            costs = [entry.get("cost", 0) for entry in cost_history]
            
            # Calculate trend metrics
            total_cost = sum(costs)
            avg_cost = total_cost / len(costs)
            std_dev = np.std(costs)
            volatility = (std_dev / avg_cost * 100) if avg_cost > 0 else 0
            
            # Detect trend direction
            trend_direction, growth_rate = self._calculate_trend(costs)
            
            # Analyze by resource type
            cost_by_resource = self._analyze_by_resource_type(cost_history)
            
            # Find cost drivers
            fastest_growing = self._find_fastest_growing_resource(cost_history)
            largest_driver = max(cost_by_resource.items(), key=lambda x: x[1])[0] if cost_by_resource else "unknown"
            
            # Detect patterns
            patterns = self._detect_patterns(cost_history)
            
            # Generate insights
            key_findings = self._generate_findings(
                trend_direction, growth_rate, volatility, cost_by_resource
            )
            
            recommendations = self._generate_trend_recommendations(
                trend_direction, growth_rate, volatility
            )
            
            return {
                "customer_id": customer_id,
                "analysis_period_days": days,
                "analysis_date": datetime.utcnow(),
                "total_cost_trend": trend_direction,
                "cost_growth_rate": growth_rate,
                "cost_volatility": volatility,
                "cost_by_resource_type": cost_by_resource,
                "fastest_growing_resource": fastest_growing,
                "largest_cost_driver": largest_driver,
                "daily_pattern": patterns.get("daily"),
                "weekly_pattern": patterns.get("weekly"),
                "monthly_pattern": patterns.get("monthly"),
                "key_findings": key_findings,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing cost trends: {e}", exc_info=True)
            return self._create_empty_trend_analysis(customer_id, days)
    
    async def analyze_usage_trends(
        self,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze usage trends (CPU, memory, network, etc.).
        
        Args:
            customer_id: Customer identifier
            days: Number of days to analyze
        
        Returns:
            Usage trend analysis
        """
        try:
            # Fetch usage data
            usage_history = await self._fetch_usage_history(customer_id, days)
            
            if not usage_history:
                return {}
            
            # Analyze CPU trends
            cpu_trend = self._analyze_metric_trend(usage_history, "cpu_utilization")
            
            # Analyze memory trends
            memory_trend = self._analyze_metric_trend(usage_history, "memory_utilization")
            
            # Analyze network trends
            network_trend = self._analyze_metric_trend(usage_history, "network_throughput")
            
            # Analyze storage trends
            storage_trend = self._analyze_metric_trend(usage_history, "storage_used")
            
            return {
                "customer_id": customer_id,
                "analysis_period_days": days,
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend,
                "network_trend": network_trend,
                "storage_trend": storage_trend,
                "analysis_date": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing usage trends: {e}", exc_info=True)
            return {}
    
    async def analyze_recommendation_effectiveness(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Analyze effectiveness of past recommendations.
        
        Args:
            customer_id: Customer identifier
        
        Returns:
            Effectiveness analysis
        """
        try:
            # Fetch implemented recommendations
            implemented_recs = await self._fetch_implemented_recommendations(customer_id)
            
            if not implemented_recs:
                return {
                    "customer_id": customer_id,
                    "total_recommendations": 0,
                    "implemented_count": 0,
                    "success_rate": 0.0,
                    "total_predicted_savings": 0.0,
                    "total_actual_savings": 0.0,
                    "accuracy": 0.0
                }
            
            # Calculate metrics
            total_recs = len(implemented_recs)
            successful = sum(1 for r in implemented_recs if r.get("actual_savings", 0) > 0)
            success_rate = (successful / total_recs * 100) if total_recs > 0 else 0
            
            total_predicted = sum(r.get("monthly_savings", 0) for r in implemented_recs)
            total_actual = sum(r.get("actual_savings", 0) for r in implemented_recs)
            
            accuracy = (total_actual / total_predicted * 100) if total_predicted > 0 else 0
            
            # Analyze by recommendation type
            by_type = {}
            for rec in implemented_recs:
                rec_type = rec.get("recommendation_type", "unknown")
                if rec_type not in by_type:
                    by_type[rec_type] = {
                        "count": 0,
                        "predicted_savings": 0.0,
                        "actual_savings": 0.0
                    }
                by_type[rec_type]["count"] += 1
                by_type[rec_type]["predicted_savings"] += rec.get("monthly_savings", 0)
                by_type[rec_type]["actual_savings"] += rec.get("actual_savings", 0)
            
            return {
                "customer_id": customer_id,
                "total_recommendations": total_recs,
                "implemented_count": total_recs,
                "success_rate": success_rate,
                "total_predicted_savings": total_predicted,
                "total_actual_savings": total_actual,
                "accuracy": accuracy,
                "by_recommendation_type": by_type,
                "analysis_date": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing recommendation effectiveness: {e}", exc_info=True)
            return {}
    
    def identify_recurring_patterns(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify recurring patterns in cost data.
        
        Args:
            cost_history: Historical cost data
        
        Returns:
            List of identified patterns
        """
        patterns = []
        
        if len(cost_history) < 7:
            return patterns
        
        # Check for daily patterns (business hours vs off-hours)
        # Would need hourly data - placeholder for now
        
        # Check for weekly patterns
        weekly_pattern = self._detect_weekly_pattern(cost_history)
        if weekly_pattern:
            patterns.append({
                "pattern_type": "weekly",
                "description": "Weekday vs weekend cost variation detected",
                "details": weekly_pattern
            })
        
        # Check for monthly patterns (month-end spikes)
        monthly_pattern = self._detect_monthly_pattern(cost_history)
        if monthly_pattern:
            patterns.append({
                "pattern_type": "monthly",
                "description": "Month-end cost spike detected",
                "details": monthly_pattern
            })
        
        return patterns
    
    async def compare_to_baseline(
        self,
        customer_id: str,
        current_period_days: int = 7,
        baseline_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare current metrics to baseline.
        
        Args:
            customer_id: Customer identifier
            current_period_days: Days for current period
            baseline_period_days: Days for baseline period
        
        Returns:
            Comparison report
        """
        try:
            # Fetch current period data
            current_data = await self._fetch_cost_history(customer_id, current_period_days)
            
            # Fetch baseline period data (excluding current period)
            baseline_data = await self._fetch_cost_history(
                customer_id,
                baseline_period_days + current_period_days
            )
            baseline_data = baseline_data[:-current_period_days] if len(baseline_data) > current_period_days else baseline_data
            
            if not current_data or not baseline_data:
                return {}
            
            # Calculate metrics
            current_avg = sum(e.get("cost", 0) for e in current_data) / len(current_data)
            baseline_avg = sum(e.get("cost", 0) for e in baseline_data) / len(baseline_data)
            
            percent_change = ((current_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0
            
            # Determine if significant
            is_significant = abs(percent_change) > 10  # >10% change is significant
            
            # Generate insights
            if percent_change > 20:
                insight = "Significant cost increase detected"
                recommendation = "Investigate cause of cost spike"
            elif percent_change < -20:
                insight = "Significant cost decrease detected"
                recommendation = "Verify optimizations are working as expected"
            elif abs(percent_change) < 5:
                insight = "Costs are stable"
                recommendation = "Continue monitoring"
            else:
                insight = "Minor cost variation"
                recommendation = "No immediate action needed"
            
            return {
                "customer_id": customer_id,
                "current_period_days": current_period_days,
                "baseline_period_days": baseline_period_days,
                "current_avg_daily_cost": current_avg,
                "baseline_avg_daily_cost": baseline_avg,
                "percent_change": percent_change,
                "is_significant": is_significant,
                "insight": insight,
                "recommendation": recommendation,
                "analysis_date": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error comparing to baseline: {e}", exc_info=True)
            return {}
    
    # Private helper methods
    
    async def _fetch_cost_history(
        self,
        customer_id: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """Fetch cost history from ClickHouse."""
        if not self.metrics_client:
            # Return mock data for testing
            return self._generate_mock_cost_history(days)
        
        try:
            # Would query ClickHouse in production
            # query = f"SELECT date, cost, resource_type FROM costs WHERE customer_id = '{customer_id}' AND date >= today() - {days}"
            # return self.metrics_client.query(query)
            return self._generate_mock_cost_history(days)
        except Exception as e:
            logger.error(f"Error fetching cost history: {e}")
            return []
    
    async def _fetch_usage_history(
        self,
        customer_id: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """Fetch usage history from ClickHouse."""
        # Placeholder - would query ClickHouse in production
        return []
    
    async def _fetch_implemented_recommendations(
        self,
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch implemented recommendations from ClickHouse."""
        # Placeholder - would query ClickHouse in production
        return []
    
    def _generate_mock_cost_history(self, days: int) -> List[Dict[str, Any]]:
        """Generate mock cost history for testing."""
        history = []
        base_cost = 1000.0
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            # Add some trend and noise
            cost = base_cost + (i * 5) + np.random.normal(0, 50)
            history.append({
                "date": date.date(),
                "cost": max(0, cost),
                "resource_type": "ec2"
            })
        
        return history
    
    def _calculate_trend(self, costs: List[float]) -> tuple:
        """Calculate trend direction and growth rate."""
        if len(costs) < 2:
            return "stable", 0.0
        
        # Linear regression
        x = np.arange(len(costs))
        y = np.array(costs)
        
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]
        
        # Calculate growth rate
        avg_cost = np.mean(costs)
        growth_rate = (slope / avg_cost * 100) if avg_cost > 0 else 0
        
        # Determine direction
        if abs(growth_rate) < 1.0:
            direction = "stable"
        elif growth_rate > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        return direction, growth_rate
    
    def _analyze_by_resource_type(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze costs by resource type."""
        by_type = {}
        
        for entry in cost_history:
            resource_type = entry.get("resource_type", "unknown")
            cost = entry.get("cost", 0)
            
            if resource_type not in by_type:
                by_type[resource_type] = 0.0
            by_type[resource_type] += cost
        
        return by_type
    
    def _find_fastest_growing_resource(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> str:
        """Find fastest growing resource type."""
        # Group by resource type
        by_type = {}
        for entry in cost_history:
            resource_type = entry.get("resource_type", "unknown")
            if resource_type not in by_type:
                by_type[resource_type] = []
            by_type[resource_type].append(entry.get("cost", 0))
        
        # Calculate growth rate for each type
        growth_rates = {}
        for resource_type, costs in by_type.items():
            if len(costs) >= 2:
                _, growth_rate = self._calculate_trend(costs)
                growth_rates[resource_type] = growth_rate
        
        if not growth_rates:
            return "unknown"
        
        return max(growth_rates.items(), key=lambda x: x[1])[0]
    
    def _detect_patterns(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect cost patterns."""
        return {
            "daily": None,  # Would need hourly data
            "weekly": self._detect_weekly_pattern(cost_history),
            "monthly": None  # Would need 12+ months
        }
    
    def _detect_weekly_pattern(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Detect weekly patterns."""
        if len(cost_history) < 14:
            return None
        
        # Group by day of week
        by_day = {i: [] for i in range(7)}
        
        for entry in cost_history:
            entry_date = entry.get("date")
            if isinstance(entry_date, str):
                entry_date = datetime.fromisoformat(entry_date).date()
            
            if entry_date:
                day_of_week = entry_date.weekday()
                by_day[day_of_week].append(entry.get("cost", 0))
        
        # Calculate average by day
        pattern = {}
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day, costs in by_day.items():
            if costs:
                pattern[day_names[day]] = sum(costs) / len(costs)
        
        return pattern if pattern else None
    
    def _detect_monthly_pattern(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Detect monthly patterns (e.g., month-end spikes)."""
        # Placeholder - would need more sophisticated analysis
        return None
    
    def _analyze_metric_trend(
        self,
        usage_history: List[Dict[str, Any]],
        metric_name: str
    ) -> Dict[str, Any]:
        """Analyze trend for a specific metric."""
        values = [entry.get(metric_name, 0) for entry in usage_history]
        
        if not values:
            return {}
        
        direction, growth_rate = self._calculate_trend(values)
        
        return {
            "metric": metric_name,
            "trend_direction": direction,
            "growth_rate": growth_rate,
            "avg_value": sum(values) / len(values),
            "min_value": min(values),
            "max_value": max(values)
        }
    
    def _generate_findings(
        self,
        trend_direction: str,
        growth_rate: float,
        volatility: float,
        cost_by_resource: Dict[str, float]
    ) -> List[str]:
        """Generate key findings from trend analysis."""
        findings = []
        
        if trend_direction == "increasing" and growth_rate > 5:
            findings.append(f"Costs are increasing at {growth_rate:.1f}% per day")
        elif trend_direction == "decreasing":
            findings.append(f"Costs are decreasing at {abs(growth_rate):.1f}% per day")
        else:
            findings.append("Costs are stable")
        
        if volatility > 30:
            findings.append(f"High cost volatility ({volatility:.1f}%) indicates variable workload")
        elif volatility < 10:
            findings.append(f"Low cost volatility ({volatility:.1f}%) indicates steady workload")
        
        if cost_by_resource:
            top_resource = max(cost_by_resource.items(), key=lambda x: x[1])
            findings.append(f"{top_resource[0]} is the largest cost driver (${top_resource[1]:.2f})")
        
        return findings
    
    def _generate_trend_recommendations(
        self,
        trend_direction: str,
        growth_rate: float,
        volatility: float
    ) -> List[str]:
        """Generate recommendations based on trends."""
        recommendations = []
        
        if trend_direction == "increasing" and growth_rate > 10:
            recommendations.append("Investigate cause of rapid cost growth")
            recommendations.append("Consider implementing cost controls")
        
        if volatility > 40:
            recommendations.append("Consider auto-scaling to handle variable workload")
        elif volatility < 15:
            recommendations.append("Consider reserved instances for steady workload")
            recommendations.append("Evaluate spot instance migration")
        
        return recommendations
    
    def _create_empty_trend_analysis(
        self,
        customer_id: str,
        days: int
    ) -> Dict[str, Any]:
        """Create empty trend analysis when data is insufficient."""
        return {
            "customer_id": customer_id,
            "analysis_period_days": days,
            "analysis_date": datetime.utcnow(),
            "total_cost_trend": "unknown",
            "cost_growth_rate": 0.0,
            "cost_volatility": 0.0,
            "cost_by_resource_type": {},
            "fastest_growing_resource": "unknown",
            "largest_cost_driver": "unknown",
            "daily_pattern": None,
            "weekly_pattern": None,
            "monthly_pattern": None,
            "key_findings": ["Insufficient data for trend analysis"],
            "recommendations": ["Collect more historical data"]
        }
