"""Tests for LLM integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.llm.llm_client import LLMClient
from src.llm.insight_generator import InsightGenerator
from src.llm.llm_integration import LLMIntegrationLayer


@pytest.mark.unit
class TestLLMClient:
    """Test LLM client."""
    
    def test_client_initialization_without_api_key(self):
        """Test client initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY not found"):
                LLMClient()
    
    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key."""
        client = LLMClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "gpt-oss-20b"
    
    @pytest.mark.asyncio
    async def test_generate_mock_response(self):
        """Test generate with mocked response."""
        client = LLMClient(api_key="test-key")
        
        # Mock the Groq client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(total_tokens=100)
        
        with patch.object(client.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await client.generate("Test prompt")
            
            assert result["content"] == "Test response"
            assert result["tokens_used"] == 100
            assert "latency_ms" in result


@pytest.mark.unit
class TestInsightGenerator:
    """Test insight generator."""
    
    @pytest.mark.asyncio
    async def test_generate_insights_mock(self):
        """Test insight generation with mock."""
        mock_client = Mock(spec=LLMClient)
        mock_client.generate = AsyncMock(return_value={
            "content": "Test insights",
            "tokens_used": 100,
            "latency_ms": 500
        })
        
        generator = InsightGenerator(mock_client)
        
        metrics = {
            "request_metrics": {"success_total": 100},
            "gpu_metrics": {"cache_usage_perc": 75.0},
            "throughput_metrics": {"tokens_per_second": 500.0}
        }
        bottlenecks = [{"type": "MEMORY_PRESSURE", "severity": "HIGH"}]
        
        insights = await generator.generate_performance_insights(
            "test-instance",
            "vllm",
            metrics,
            bottlenecks
        )
        
        assert insights == "Test insights"
        assert mock_client.generate.called
    
    @pytest.mark.asyncio
    async def test_explain_bottleneck_mock(self):
        """Test bottleneck explanation with mock."""
        mock_client = Mock(spec=LLMClient)
        mock_client.generate = AsyncMock(return_value={
            "content": "Business explanation",
            "tokens_used": 50
        })
        
        generator = InsightGenerator(mock_client)
        
        bottleneck = {
            "type": "MEMORY_PRESSURE",
            "severity": "HIGH",
            "metric_name": "memory_usage",
            "current_value": 0.9,
            "threshold_value": 0.8,
            "description": "High memory usage"
        }
        
        explanation = await generator.explain_bottleneck(bottleneck)
        
        assert explanation == "Business explanation"


@pytest.mark.unit
class TestLLMIntegrationLayer:
    """Test LLM integration layer."""
    
    @pytest.mark.asyncio
    async def test_enhance_report_disabled(self):
        """Test enhancement when LLM is disabled."""
        layer = LLMIntegrationLayer(api_key="test-key")
        
        result = await layer.enhance_analysis_report(
            "test-instance",
            "vllm",
            {},
            [],
            [],
            enable_llm=False
        )
        
        assert result["llm_enhanced"] is False
        assert result["instance_id"] == "test-instance"
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test caching works."""
        layer = LLMIntegrationLayer(api_key="test-key", enable_cache=True)
        
        # Mock the insight generator
        with patch.object(layer.insight_generator, 'generate_performance_insights', new=AsyncMock(return_value="Insights")):
            with patch.object(layer.insight_generator, 'explain_bottleneck', new=AsyncMock(return_value="Explanation")):
                with patch.object(layer.insight_generator, 'enhance_optimization', new=AsyncMock(return_value={})):
                    with patch.object(layer.insight_generator, 'generate_executive_summary', new=AsyncMock(return_value="Summary")):
                        # First call - should generate
                        result1 = await layer.enhance_analysis_report(
                            "test-instance",
                            "vllm",
                            {"test": "metrics"},
                            [],
                            [],
                            enable_llm=True
                        )
                        
                        # Second call - should hit cache
                        result2 = await layer.enhance_analysis_report(
                            "test-instance",
                            "vllm",
                            {"test": "metrics"},
                            [],
                            [],
                            enable_llm=True
                        )
                        
                        assert result1["llm_enhanced"] is True
                        assert result2["cache_hit"] is True


@pytest.mark.integration
class TestLLMIntegration:
    """Integration tests (require API key)."""
    
    @pytest.mark.skip(reason="Requires Groq API key")
    @pytest.mark.asyncio
    async def test_real_llm_call(self):
        """Test real LLM API call."""
        # This test requires GROQ_API_KEY environment variable
        client = LLMClient()
        
        result = await client.generate(
            "Say 'Hello, World!' and nothing else.",
            max_tokens=50
        )
        
        assert "content" in result
        assert result["tokens_used"] > 0
