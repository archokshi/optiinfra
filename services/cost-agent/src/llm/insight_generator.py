"""
Insight Generator for LLM-powered cost optimization insights.

Generates natural language insights, enhances recommendations,
and creates executive summaries from technical analysis data.
"""

import logging
from typing import Dict, List, Any, Optional
from src.llm.llm_client import LLMClient
from src.llm.prompt_templates import (
    PromptTemplate,
    COST_OPTIMIZATION_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)


async def generate_insights(
    analysis_report: Dict[str, Any],
    llm_client: LLMClient
) -> str:
    """
    Generate natural language insights from analysis report.
    
    Args:
        analysis_report: Technical analysis report
        llm_client: LLM client instance
    
    Returns:
        Natural language insights
    
    Raises:
        ValueError: If analysis report is invalid
    """
    if not analysis_report:
        raise ValueError("Analysis report cannot be empty")
    
    logger.info("Generating insights from analysis report")
    
    try:
        # Prepare analysis data for prompt
        analysis_data = _prepare_analysis_data(analysis_report)
        
        # Render prompt
        prompt = PromptTemplate.render_insight_generation(analysis_data)
        
        # Generate insights
        insights = await llm_client.generate(
            prompt=prompt,
            system_prompt=COST_OPTIMIZATION_SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Validate response
        if not llm_client.validate_response(insights, min_length=100):
            logger.warning("Generated insights may be low quality")
        
        logger.info("Insights generated successfully")
        return insights
        
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise


async def enhance_recommendations(
    recommendations: List[Dict[str, Any]],
    llm_client: LLMClient,
    max_recommendations: int = 10
) -> List[Dict[str, Any]]:
    """
    Enhance recommendations with business context.
    
    Args:
        recommendations: List of technical recommendations
        llm_client: LLM client instance
        max_recommendations: Maximum recommendations to enhance
    
    Returns:
        List of enhanced recommendations
    """
    if not recommendations:
        logger.warning("No recommendations to enhance")
        return []
    
    logger.info(f"Enhancing {len(recommendations)} recommendations")
    
    enhanced = []
    
    # Limit number of recommendations to enhance (cost control)
    recommendations_to_enhance = recommendations[:max_recommendations]
    
    for idx, rec in enumerate(recommendations_to_enhance):
        try:
            # Render prompt
            prompt = PromptTemplate.render_recommendation_enhancement(rec)
            
            # Generate enhancement
            enhancement = await llm_client.generate(
                prompt=prompt,
                system_prompt=COST_OPTIMIZATION_SYSTEM_PROMPT,
                max_tokens=1500,
                temperature=0.7
            )
            
            # Add enhancement to recommendation
            enhanced_rec = {
                **rec,
                "llm_enhancement": enhancement,
                "enhanced": True
            }
            
            enhanced.append(enhanced_rec)
            logger.debug(f"Enhanced recommendation {idx + 1}/{len(recommendations_to_enhance)}")
            
        except Exception as e:
            logger.error(f"Failed to enhance recommendation {idx}: {e}")
            # Keep original recommendation
            enhanced.append({**rec, "enhanced": False})
    
    # Add remaining recommendations without enhancement
    if len(recommendations) > max_recommendations:
        for rec in recommendations[max_recommendations:]:
            enhanced.append({**rec, "enhanced": False})
    
    logger.info(f"Enhanced {len(enhanced)} recommendations")
    return enhanced


async def generate_executive_summary(
    analysis_report: Dict[str, Any],
    insights: str,
    llm_client: LLMClient
) -> str:
    """
    Generate executive summary for C-suite.
    
    Args:
        analysis_report: Technical analysis report
        insights: Generated insights
        llm_client: LLM client instance
    
    Returns:
        Executive summary
    
    Raises:
        ValueError: If inputs are invalid
    """
    if not analysis_report or not insights:
        raise ValueError("Analysis report and insights are required")
    
    logger.info("Generating executive summary")
    
    try:
        # Prepare analysis data
        analysis_data = _prepare_analysis_data(analysis_report)
        
        # Render prompt
        prompt = PromptTemplate.render_executive_summary(
            analysis_data=analysis_data,
            insights=insights
        )
        
        # Generate summary
        summary = await llm_client.generate(
            prompt=prompt,
            system_prompt=COST_OPTIMIZATION_SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Validate response
        if not llm_client.validate_response(summary, min_length=200):
            logger.warning("Generated summary may be low quality")
        
        logger.info("Executive summary generated successfully")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate executive summary: {e}")
        raise


async def handle_query(
    query: str,
    analysis_report: Dict[str, Any],
    llm_client: LLMClient
) -> str:
    """
    Handle natural language query about analysis.
    
    Args:
        query: User query
        analysis_report: Analysis report data
        llm_client: LLM client instance
    
    Returns:
        Answer to query
    
    Raises:
        ValueError: If query is empty
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    logger.info(f"Handling query: {query[:50]}...")
    
    try:
        # Prepare analysis data
        analysis_data = _prepare_analysis_data(analysis_report)
        
        # Render prompt
        prompt = PromptTemplate.render_query_handling(
            query=query,
            analysis_data=analysis_data
        )
        
        # Generate answer
        answer = await llm_client.generate(
            prompt=prompt,
            system_prompt=COST_OPTIMIZATION_SYSTEM_PROMPT,
            max_tokens=1000,
            temperature=0.7
        )
        
        logger.info("Query answered successfully")
        return answer
        
    except Exception as e:
        logger.error(f"Failed to handle query: {e}")
        raise


async def explain_anomaly(
    anomaly: Dict[str, Any],
    context: Dict[str, Any],
    llm_client: LLMClient
) -> str:
    """
    Explain cost anomaly in business-friendly terms.
    
    Args:
        anomaly: Anomaly details
        context: Additional context
        llm_client: LLM client instance
    
    Returns:
        Anomaly explanation
    """
    logger.info(f"Explaining anomaly: {anomaly.get('anomaly_type', 'unknown')}")
    
    try:
        # Render prompt
        prompt = PromptTemplate.render_anomaly_explanation(
            anomaly=anomaly,
            context=context
        )
        
        # Generate explanation
        explanation = await llm_client.generate(
            prompt=prompt,
            system_prompt=COST_OPTIMIZATION_SYSTEM_PROMPT,
            max_tokens=1000,
            temperature=0.7
        )
        
        logger.info("Anomaly explained successfully")
        return explanation
        
    except Exception as e:
        logger.error(f"Failed to explain anomaly: {e}")
        raise


async def assess_risk(
    change_description: str,
    current_state: Dict[str, Any],
    llm_client: LLMClient
) -> Dict[str, Any]:
    """
    Assess risk of proposed infrastructure change.
    
    Args:
        change_description: Description of proposed change
        current_state: Current infrastructure state
        llm_client: LLM client instance
    
    Returns:
        Risk assessment with level and mitigation strategies
    """
    logger.info("Assessing risk for proposed change")
    
    try:
        # Render prompt
        prompt = PromptTemplate.render_risk_assessment(
            change_description=change_description,
            current_state=current_state
        )
        
        # Generate assessment
        assessment = await llm_client.generate(
            prompt=prompt,
            system_prompt=COST_OPTIMIZATION_SYSTEM_PROMPT,
            max_tokens=1500,
            temperature=0.7
        )
        
        # Parse risk level from response
        risk_level = _extract_risk_level(assessment)
        
        logger.info(f"Risk assessment complete: {risk_level}")
        
        return {
            "risk_level": risk_level,
            "assessment": assessment,
            "timestamp": _get_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to assess risk: {e}")
        raise


def _prepare_analysis_data(analysis_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare analysis data for LLM prompt.
    
    Extracts key metrics and formats them for LLM consumption.
    
    Args:
        analysis_report: Raw analysis report
    
    Returns:
        Formatted analysis data
    """
    return {
        "idle_resources": analysis_report.get("idle_resources", []),
        "total_monthly_waste": analysis_report.get("total_monthly_waste", 0),
        "total_annual_waste": analysis_report.get("total_annual_waste", 0),
        "anomalies": analysis_report.get("anomalies", []),
        "recommendations": analysis_report.get("recommendations", []),
        "summary": analysis_report.get("summary", {}),
        "resource_count": len(analysis_report.get("idle_resources", [])),
        "anomaly_count": len(analysis_report.get("anomalies", [])),
        "critical_findings": _extract_critical_findings(analysis_report)
    }


def _extract_critical_findings(analysis_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract critical findings from analysis report.
    
    Args:
        analysis_report: Analysis report
    
    Returns:
        List of critical findings
    """
    critical = []
    
    # Critical idle resources (high cost)
    idle_resources = analysis_report.get("idle_resources", [])
    for resource in idle_resources:
        if resource.get("idle_severity") == "critical":
            critical.append({
                "type": "idle_resource",
                "resource_id": resource.get("resource_id"),
                "monthly_cost": resource.get("monthly_cost", 0),
                "severity": "critical"
            })
    
    # Critical anomalies
    anomalies = analysis_report.get("anomalies", [])
    for anomaly in anomalies:
        if anomaly.get("severity") in ["critical", "high"]:
            critical.append({
                "type": "anomaly",
                "anomaly_type": anomaly.get("anomaly_type"),
                "severity": anomaly.get("severity"),
                "details": anomaly.get("details", {})
            })
    
    return critical


def _extract_risk_level(assessment_text: str) -> str:
    """
    Extract risk level from assessment text.
    
    Args:
        assessment_text: Risk assessment text
    
    Returns:
        Risk level (LOW, MEDIUM, HIGH, CRITICAL)
    """
    text_upper = assessment_text.upper()
    
    if "CRITICAL" in text_upper:
        return "CRITICAL"
    elif "HIGH" in text_upper:
        return "HIGH"
    elif "MEDIUM" in text_upper:
        return "MEDIUM"
    else:
        return "LOW"


def _get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat()
