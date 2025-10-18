"""
Workflow nodes for cost optimization.
"""

from src.nodes.analyze import analyze_resources
from src.nodes.recommend import generate_recommendations
from src.nodes.spot_analyze import analyze_spot_opportunities
from src.nodes.spot_coordinate import coordinate_with_agents
from src.nodes.spot_execute import execute_migration
from src.nodes.spot_monitor import monitor_quality
from src.nodes.summarize import create_summary

__all__ = [
    "analyze_resources",
    "generate_recommendations",
    "create_summary",
    "analyze_spot_opportunities",
    "coordinate_with_agents",
    "execute_migration",
    "monitor_quality",
]
