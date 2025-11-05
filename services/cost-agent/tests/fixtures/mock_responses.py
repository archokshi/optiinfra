"""
Mock API Responses.

Provides mock responses for external API calls.
"""

import json
from typing import Dict, List


def mock_groq_analysis_response(
    analysis_type: str = "cost_spike",
    confidence: float = 0.95
) -> Dict:
    """
    Generate mock Groq API response for cost analysis.
    
    Args:
        analysis_type: Type of analysis
        confidence: Confidence score
        
    Returns:
        Mock Groq response
    """
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "mixtral-8x7b-32768",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps({
                    "analysis": f"Detected {analysis_type} in EC2 costs",
                    "severity": "high",
                    "recommendations": [
                        "Review instance usage patterns",
                        "Consider spot instances for non-critical workloads",
                        "Implement auto-scaling policies"
                    ],
                    "confidence": confidence,
                    "affected_services": ["EC2", "RDS"],
                    "estimated_impact": 1500.00
                })
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 200,
            "total_tokens": 350
        }
    }


def mock_groq_recommendation_response(
    recommendation_type: str = "spot_migration",
    savings: float = 1200.00
) -> Dict:
    """
    Generate mock Groq API response for recommendation generation.
    
    Args:
        recommendation_type: Type of recommendation
        savings: Estimated savings
        
    Returns:
        Mock Groq response
    """
    return {
        "id": "chatcmpl-456",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "mixtral-8x7b-32768",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps({
                    "recommendation_type": recommendation_type,
                    "title": "Migrate to Spot Instances",
                    "description": "Migrate non-critical workloads to spot instances",
                    "estimated_monthly_savings": savings,
                    "priority": "high",
                    "risk_level": "low",
                    "implementation_steps": [
                        "Identify non-critical workloads",
                        "Set up spot instance requests",
                        "Configure interruption handling",
                        "Monitor and validate"
                    ],
                    "confidence": 0.92
                })
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 200,
            "completion_tokens": 250,
            "total_tokens": 450
        }
    }


def mock_groq_error_response(error_type: str = "rate_limit") -> Dict:
    """
    Generate mock Groq API error response.
    
    Args:
        error_type: Type of error
        
    Returns:
        Mock error response
    """
    error_messages = {
        "rate_limit": "Rate limit exceeded. Please try again later.",
        "invalid_api_key": "Invalid API key provided.",
        "server_error": "Internal server error. Please try again.",
        "timeout": "Request timeout. Please try again."
    }
    
    return {
        "error": {
            "message": error_messages.get(error_type, "Unknown error"),
            "type": error_type,
            "code": error_type
        }
    }


def mock_aws_ec2_describe_instances() -> Dict:
    """
    Generate mock AWS EC2 describe instances response.
    
    Returns:
        Mock EC2 response
    """
    return {
        "Reservations": [{
            "Instances": [
                {
                    "InstanceId": "i-123",
                    "InstanceType": "t3.medium",
                    "State": {"Name": "running"},
                    "LaunchTime": "2025-10-01T00:00:00Z",
                    "Tags": [
                        {"Key": "Name", "Value": "test-instance-1"},
                        {"Key": "Environment", "Value": "production"}
                    ]
                },
                {
                    "InstanceId": "i-456",
                    "InstanceType": "m5.large",
                    "State": {"Name": "running"},
                    "LaunchTime": "2025-10-01T00:00:00Z",
                    "Tags": [
                        {"Key": "Name", "Value": "test-instance-2"},
                        {"Key": "Environment", "Value": "staging"}
                    ]
                }
            ]
        }]
    }


def mock_cloudwatch_metrics(metric_name: str = "CPUUtilization") -> Dict:
    """
    Generate mock CloudWatch metrics response.
    
    Args:
        metric_name: Metric name
        
    Returns:
        Mock CloudWatch response
    """
    return {
        "Label": metric_name,
        "Datapoints": [
            {"Timestamp": "2025-10-23T00:00:00Z", "Average": 18.5, "Unit": "Percent"},
            {"Timestamp": "2025-10-23T01:00:00Z", "Average": 22.3, "Unit": "Percent"},
            {"Timestamp": "2025-10-23T02:00:00Z", "Average": 15.7, "Unit": "Percent"},
            {"Timestamp": "2025-10-23T03:00:00Z", "Average": 19.2, "Unit": "Percent"},
        ]
    }
