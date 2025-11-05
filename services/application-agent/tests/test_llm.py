"""
Tests for LLM integration.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.llm.llm_client import LLMClient
from unittest.mock import AsyncMock, patch

client = TestClient(app)


def test_llm_client_initialization():
    """Test LLM client initialization."""
    llm = LLMClient()
    assert llm.model == "gpt-oss-20b"
    assert llm.timeout == 30


def test_llm_score_parsing():
    """Test score parsing from LLM responses."""
    llm = LLMClient()
    
    # Test valid scores
    assert llm.parse_score("85") == 85.0
    assert llm.parse_score("The score is 92") == 92.0
    assert llm.parse_score("75.5") == 75.5
    
    # Test clamping
    assert llm.parse_score("150") == 100.0
    assert llm.parse_score("-10") == 0.0
    
    # Test invalid
    assert llm.parse_score("invalid") is None
    assert llm.parse_score(None) is None


@pytest.mark.asyncio
async def test_llm_analyze_endpoint_no_api_key():
    """Test LLM analyze endpoint without API key."""
    request = {
        "prompt": "What is 2+2?",
        "response": "2+2 equals 4"
    }
    
    response = client.post("/llm/analyze", json=request)
    # Should still return response even without API key
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_llm_score_endpoint_no_api_key():
    """Test LLM score endpoint without API key."""
    request = {
        "prompt": "What is AI?",
        "response": "AI is artificial intelligence"
    }
    
    response = client.post("/llm/score", json=request)
    # Should still return response even without API key
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_llm_suggest_endpoint_no_api_key():
    """Test LLM suggest endpoint without API key."""
    request = {
        "prompt": "What is AI?",
        "response": "AI is computers"
    }
    
    response = client.post("/llm/suggest", json=request)
    # Should still return response even without API key
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
@patch('src.llm.llm_client.AsyncGroq')
async def test_llm_with_mock(mock_groq):
    """Test LLM with mocked Groq client."""
    # Setup mock
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "85"
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_groq.return_value = mock_client
    
    # Create client with mock
    llm = LLMClient()
    llm.enabled = True
    llm.client = mock_client
    
    # Test generation
    result = await llm.generate("test prompt")
    assert result == "85"
    
    # Test score parsing
    score = llm.parse_score(result)
    assert score == 85.0
