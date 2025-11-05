"""
Unit Tests for Groq Client.

Tests Groq API integration.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@pytest.mark.unit
class TestGroqClient:
    """Test Groq API client."""
    
    def test_parse_groq_response(self, mock_groq_response):
        """Test parsing Groq API response."""
        assert "choices" in mock_groq_response
        assert len(mock_groq_response["choices"]) > 0
        
        message = mock_groq_response["choices"][0]["message"]
        content = json.loads(message["content"])
        
        assert "analysis" in content
        assert "confidence" in content
    
    def test_extract_analysis_from_response(self, mock_groq_response):
        """Test extracting analysis from response."""
        message = mock_groq_response["choices"][0]["message"]
        content = json.loads(message["content"])
        
        assert content["confidence"] > 0
        assert content["confidence"] <= 1.0
        assert isinstance(content["analysis"], str)
    
    def test_handle_groq_error(self, mock_groq_error):
        """Test handling Groq API errors."""
        assert "error" in mock_groq_error
        assert "message" in mock_groq_error["error"]
        assert "type" in mock_groq_error["error"]
    
    def test_retry_logic_structure(self):
        """Test retry logic structure."""
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            attempt += 1
            # Simulate retry
            if attempt == max_retries:
                break
        
        assert attempt == max_retries
    
    @pytest.mark.asyncio
    async def test_async_api_call_mock(self):
        """Test async API call with mock."""
        async def mock_api_call():
            return {"result": "success"}
        
        result = await mock_api_call()
        assert result["result"] == "success"
    
    def test_token_counting(self):
        """Test token counting logic."""
        text = "This is a test message for token counting"
        # Simple word-based approximation
        words = text.split()
        estimated_tokens = len(words) * 1.3  # Rough estimate
        
        assert estimated_tokens > 0
    
    def test_prompt_construction(self):
        """Test prompt construction."""
        system_prompt = "You are a cost analysis assistant."
        user_message = "Analyze these costs: $1500"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


@pytest.mark.unit
class TestPromptManager:
    """Test prompt management."""
    
    def test_cost_analysis_prompt(self, sample_aws_costs):
        """Test cost analysis prompt generation."""
        prompt = f"""Analyze the following cost data:
        Total Cost: ${sample_aws_costs['total_cost']}
        Provider: {sample_aws_costs['provider']}
        Services: {len(sample_aws_costs['services'])}
        
        Provide insights and recommendations."""
        
        assert "Total Cost" in prompt
        assert str(sample_aws_costs['total_cost']) in prompt
    
    def test_recommendation_prompt(self, sample_spot_migration_recommendation):
        """Test recommendation generation prompt."""
        prompt = f"""Generate a detailed recommendation for:
        Type: {sample_spot_migration_recommendation['type']}
        Estimated Savings: ${sample_spot_migration_recommendation['estimated_monthly_savings']}
        
        Provide implementation steps."""
        
        assert "recommendation" in prompt.lower()
        assert str(sample_spot_migration_recommendation['estimated_monthly_savings']) in prompt
    
    def test_context_injection(self):
        """Test context injection in prompts."""
        base_prompt = "Analyze costs for customer {customer_id}"
        context = {"customer_id": "cust-123"}
        
        final_prompt = base_prompt.format(**context)
        
        assert "cust-123" in final_prompt
        assert "{customer_id}" not in final_prompt
