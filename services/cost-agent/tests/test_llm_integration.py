"""
Comprehensive tests for LLM integration.

Tests all LLM components including client, prompts, insight generation,
and integration with Analysis Engine.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import LLM components
from src.llm.llm_client import LLMClient, LLMClientFactory
from src.llm.prompt_templates import PromptTemplate
from src.llm.insight_generator import (
    generate_insights,
    enhance_recommendations,
    generate_executive_summary,
    handle_query
)
from src.llm.llm_integration import LLMIntegrationLayer


class TestLLMClient:
    """Test LLM client functionality."""
    
    def test_client_initialization(self):
        """Test LLM client initialization."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            client = LLMClient()
            assert client.model == "gpt-oss-20b"
            assert client.api_key == "test-key"
            assert client.max_retries == 3
            assert client.timeout == 30
    
    def test_client_initialization_no_api_key(self):
        """Test client initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY not found"):
                LLMClient()
    
    @pytest.mark.asyncio
    async def test_generate_response(self):
        """Test generating response from LLM."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            client = LLMClient()
            
            # Mock Groq API response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.usage.total_tokens = 100
            
            with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
                response = await client.generate(
                    prompt="Test prompt",
                    system_prompt="Test system"
                )
                
                assert response == "Test response"
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in LLM client."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            client = LLMClient()
            
            # Mock API error
            with patch.object(client.client.chat.completions, 'create', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    await client.generate(prompt="Test")
    
    def test_token_counting(self):
        """Test token counting estimation."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            client = LLMClient()
            text = "This is a test message"
            tokens = client.count_tokens(text)
            assert tokens > 0
            assert tokens == len(text) // 4
    
    def test_response_validation(self):
        """Test response validation."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            client = LLMClient()
            
            # Valid response
            assert client.validate_response("This is a valid response") is True
            
            # Invalid responses
            assert client.validate_response("") is False
            assert client.validate_response("I cannot help") is False
            assert client.validate_response("Error: something went wrong") is False
    
    def test_factory_singleton(self):
        """Test LLM client factory singleton pattern."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            LLMClientFactory.reset()
            
            client1 = LLMClientFactory.get_client()
            client2 = LLMClientFactory.get_client()
            
            assert client1 is client2


class TestPromptTemplates:
    """Test prompt template functionality."""
    
    def test_insight_prompt_rendering(self):
        """Test insight generation prompt rendering."""
        analysis_data = {
            "idle_resources": [{"resource_id": "i-123"}],
            "total_monthly_waste": 3600.00
        }
        
        prompt = PromptTemplate.render_insight_generation(analysis_data)
        
        assert "Analysis Data:" in prompt
        assert "idle_resources" in prompt
        assert "3600" in prompt
    
    def test_recommendation_prompt_rendering(self):
        """Test recommendation enhancement prompt rendering."""
        recommendation = {
            "action": "terminate",
            "resource_id": "i-123",
            "monthly_savings": 52.00
        }
        
        prompt = PromptTemplate.render_recommendation_enhancement(recommendation)
        
        assert "Technical Recommendation:" in prompt
        assert "terminate" in prompt
        assert "i-123" in prompt
    
    def test_executive_summary_prompt_rendering(self):
        """Test executive summary prompt rendering."""
        analysis_data = {"total_monthly_waste": 3600.00}
        insights = "Test insights"
        
        prompt = PromptTemplate.render_executive_summary(analysis_data, insights)
        
        assert "executive summary" in prompt.lower()
        assert "Test insights" in prompt
        assert "3600" in prompt
    
    def test_prompt_validation(self):
        """Test prompt template validation."""
        template = "Hello {name}, your {item} is ready"
        
        assert PromptTemplate.validate_template(template, ["name", "item"]) is True
        assert PromptTemplate.validate_template(template, ["name", "missing"]) is False


class TestInsightGenerator:
    """Test insight generation functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_insights(self):
        """Test generating insights from analysis report."""
        analysis_report = {
            "idle_resources": [
                {"resource_id": "i-123", "monthly_cost": 52.00}
            ],
            "total_monthly_waste": 3600.00,
            "anomalies": []
        }
        
        # Mock LLM client
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Generated insights about idle resources")
        mock_client.validate_response = Mock(return_value=True)
        
        insights = await generate_insights(analysis_report, mock_client)
        
        assert isinstance(insights, str)
        assert len(insights) > 0
        mock_client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enhance_recommendations(self):
        """Test enhancing recommendations."""
        recommendations = [
            {
                "action": "terminate",
                "resource_id": "i-123",
                "reason": "idle",
                "monthly_savings": 52.00
            }
        ]
        
        # Mock LLM client
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Enhanced recommendation with business context")
        
        enhanced = await enhance_recommendations(recommendations, mock_client)
        
        assert len(enhanced) == 1
        assert enhanced[0]["enhanced"] is True
        assert "llm_enhancement" in enhanced[0]
    
    @pytest.mark.asyncio
    async def test_generate_executive_summary(self):
        """Test generating executive summary."""
        analysis_report = {
            "total_monthly_waste": 3600.00,
            "total_annual_waste": 43200.00
        }
        insights = "Test insights"
        
        # Mock LLM client
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Executive summary for C-suite")
        mock_client.validate_response = Mock(return_value=True)
        
        summary = await generate_executive_summary(analysis_report, insights, mock_client)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        mock_client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_empty_data_handling(self):
        """Test handling of empty data."""
        mock_client = AsyncMock()
        
        with pytest.raises(ValueError):
            await generate_insights({}, mock_client)
    
    @pytest.mark.asyncio
    async def test_handle_query(self):
        """Test natural language query handling."""
        query = "What are my biggest cost wastes?"
        analysis_report = {
            "idle_resources": [{"resource_id": "i-123"}]
        }
        
        # Mock LLM client
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Your biggest waste is idle resources")
        
        answer = await handle_query(query, analysis_report, mock_client)
        
        assert isinstance(answer, str)
        assert len(answer) > 0


class TestLLMIntegrationLayer:
    """Test LLM integration layer."""
    
    @pytest.mark.asyncio
    async def test_enhance_report(self):
        """Test enhancing report with LLM."""
        technical_report = {
            "idle_resources": [{"resource_id": "i-123"}],
            "total_monthly_waste": 3600.00,
            "recommendations": []
        }
        
        # Mock LLM client
        mock_client = AsyncMock()
        mock_client.model = "gpt-oss-20b"
        mock_client.generate = AsyncMock(return_value="Generated content")
        mock_client.validate_response = Mock(return_value=True)
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key', 'LLM_ENABLED': 'true'}):
            layer = LLMIntegrationLayer(llm_client=mock_client)
            
            enhanced = await layer.enhance_report(technical_report, enable_llm=True)
            
            assert "llm_insights" in enhanced
            assert "enhanced_recommendations" in enhanced
            assert "executive_summary" in enhanced
            assert "llm_metadata" in enhanced
    
    @pytest.mark.asyncio
    async def test_feature_flag_disabled(self):
        """Test LLM enhancement when feature flag is disabled."""
        technical_report = {"test": "data"}
        
        mock_client = AsyncMock()
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            layer = LLMIntegrationLayer(llm_client=mock_client)
            
            result = await layer.enhance_report(technical_report, enable_llm=False)
            
            # Should return original report unchanged
            assert result == technical_report
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation on LLM error."""
        technical_report = {
            "idle_resources": [],
            "total_monthly_waste": 0
        }
        
        # Mock LLM client that raises error
        mock_client = AsyncMock()
        mock_client.model = "gpt-oss-20b"
        mock_client.generate = AsyncMock(side_effect=Exception("API Error"))
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key', 'LLM_ENABLED': 'true'}):
            layer = LLMIntegrationLayer(llm_client=mock_client)
            
            result = await layer.enhance_report(technical_report, enable_llm=True)
            
            # Should return report with error info
            assert "llm_error" in result
            assert result["llm_metadata"]["error"] is True
    
    @pytest.mark.asyncio
    async def test_caching(self):
        """Test response caching."""
        technical_report = {"test": "data"}
        
        mock_client = AsyncMock()
        mock_client.model = "gpt-oss-20b"
        mock_client.generate = AsyncMock(return_value="Cached response")
        mock_client.validate_response = Mock(return_value=True)
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key', 'LLM_ENABLED': 'true'}):
            layer = LLMIntegrationLayer(llm_client=mock_client, enable_caching=True)
            
            # First call
            result1 = await layer.enhance_report(technical_report, enable_llm=True)
            
            # Second call (should be cached)
            result2 = await layer.enhance_report(technical_report, enable_llm=True)
            
            # LLM should only be called once
            assert mock_client.generate.call_count == 3  # insights, recs, summary
            
            # Results should be identical
            assert result1 == result2
    
    def test_cache_stats(self):
        """Test getting cache statistics."""
        mock_client = AsyncMock()
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            layer = LLMIntegrationLayer(llm_client=mock_client)
            
            stats = layer.get_cache_stats()
            
            assert "cache_size" in stats
            assert "cache_enabled" in stats
    
    def test_clear_cache(self):
        """Test clearing cache."""
        mock_client = AsyncMock()
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            layer = LLMIntegrationLayer(llm_client=mock_client)
            layer._cache["test"] = "data"
            
            assert len(layer._cache) > 0
            
            layer.clear_cache()
            
            assert len(layer._cache) == 0


class TestAnalysisEngineIntegration:
    """Test LLM integration with Analysis Engine."""
    
    @pytest.mark.asyncio
    async def test_analysis_with_llm_enabled(self):
        """Test running analysis with LLM enhancement enabled."""
        from src.workflows.analysis_engine import AnalysisEngineWorkflow
        
        # Mock the workflow components
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key', 'LLM_ENABLED': 'true'}):
            workflow = AnalysisEngineWorkflow()
            
            # Mock LLM layer
            workflow.llm_layer = AsyncMock()
            workflow.llm_layer.enhance_report = AsyncMock(return_value={
                "llm_insights": "Test insights",
                "enhanced_recommendations": [],
                "executive_summary": "Test summary"
            })
            
            # Mock workflow execution
            workflow.workflow = Mock()
            workflow.workflow.invoke = Mock(return_value={
                "idle_resources": [],
                "anomalies": [],
                "analysis_report": {},
                "workflow_status": "complete"
            })
            
            # Mock data collection
            workflow.collect_resource_data = AsyncMock(return_value={
                "resource_data": [],
                "cost_history": []
            })
            
            result = await workflow.run_analysis(
                customer_id="test-customer",
                enable_llm=True
            )
            
            # Should have LLM enhancements
            workflow.llm_layer.enhance_report.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analysis_with_llm_disabled(self):
        """Test running analysis with LLM enhancement disabled."""
        from src.workflows.analysis_engine import AnalysisEngineWorkflow
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            workflow = AnalysisEngineWorkflow()
            
            # Mock LLM layer
            workflow.llm_layer = AsyncMock()
            workflow.llm_layer.enhance_report = AsyncMock()
            
            # Mock workflow execution
            workflow.workflow = Mock()
            workflow.workflow.invoke = Mock(return_value={
                "idle_resources": [],
                "anomalies": [],
                "analysis_report": {},
                "workflow_status": "complete"
            })
            
            # Mock data collection
            workflow.collect_resource_data = AsyncMock(return_value={
                "resource_data": [],
                "cost_history": []
            })
            
            result = await workflow.run_analysis(
                customer_id="test-customer",
                enable_llm=False
            )
            
            # LLM should not be called
            workflow.llm_layer.enhance_report.assert_not_called()


class TestMocking:
    """Test mocking and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_mock_llm_response(self):
        """Test with mocked LLM response."""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Mocked LLM response")
        
        response = await mock_client.generate("Test prompt")
        
        assert response == "Mocked LLM response"
    
    def test_no_api_key_scenario(self):
        """Test behavior when API key is missing."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError):
                LLMClient()
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            client = LLMClient(timeout=1)
            
            # Mock timeout
            with patch.object(client.client.chat.completions, 'create', side_effect=TimeoutError("Timeout")):
                with pytest.raises(TimeoutError):
                    await client.generate("Test")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
