"""
Unit tests for Generic Collector
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.collectors.generic_collector import GenericCollector, GenericCollectorConfig
from src.models.metrics import Provider


@pytest.fixture
def generic_config():
    """Create a test configuration"""
    return GenericCollectorConfig(
        provider="vultr",
        customer_id="test_customer",
        prometheus_url="http://localhost:9090",
        dcgm_url="http://localhost:9400",
        api_key="test_api_key",
        timeout=10
    )


def test_generic_collector_config_validation(generic_config):
    """Test configuration validation"""
    assert generic_config.validate() == True
    assert generic_config.provider == "vultr"
    assert generic_config.customer_id == "test_customer"


def test_generic_collector_config_missing_prometheus():
    """Test configuration fails without Prometheus URL"""
    with pytest.raises(ValueError):
        config = GenericCollectorConfig(
            provider="vultr",
            customer_id="test_customer",
            prometheus_url="",  # Missing
        )
        config.validate()


def test_generic_collector_initialization(generic_config):
    """Test Generic Collector initialization"""
    collector = GenericCollector(generic_config)
    assert collector.get_provider_name() == "vultr"
    assert collector.get_data_type() == "all"
    assert collector.config.prometheus_url == "http://localhost:9090"


@pytest.mark.asyncio
async def test_query_prometheus_success(generic_config):
    """Test Prometheus query success"""
    collector = GenericCollector(generic_config)
    
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "success",
        "data": {
            "result": [
                {"value": [1234567890, "42.5"]}
            ]
        }
    }
    mock_response.raise_for_status = Mock()
    
    async with collector:
        # Mock the client.get method after client is created
        with patch.object(collector.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            value = await collector._query_prometheus("test_query")
            assert value == 42.5
            mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_query_prometheus_no_results(generic_config):
    """Test Prometheus query with no results"""
    collector = GenericCollector(generic_config)
    
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "success",
        "data": {
            "result": []
        }
    }
    mock_response.raise_for_status = Mock()
    
    with patch.object(collector, 'client') as mock_client:
        mock_client.get = AsyncMock(return_value=mock_response)
        
        async with collector:
            value = await collector._query_prometheus("test_query")
            assert value is None


def test_parse_prometheus_text(generic_config):
    """Test Prometheus text format parsing"""
    collector = GenericCollector(generic_config)
    
    metrics_text = """
# HELP test_metric A test metric
# TYPE test_metric gauge
test_metric{label="value"} 123.45
another_metric 67.89
"""
    
    metrics = collector._parse_prometheus_text(metrics_text)
    assert "test_metric" in metrics
    assert "another_metric" in metrics
    assert metrics["test_metric"] == 123.45
    assert metrics["another_metric"] == 67.89


def test_validate_credentials(generic_config):
    """Test credential validation"""
    collector = GenericCollector(generic_config)
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        assert collector.validate_credentials() == True


def test_validate_credentials_failure(generic_config):
    """Test credential validation failure"""
    collector = GenericCollector(generic_config)
    
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection failed")
        
        assert collector.validate_credentials() == False


@pytest.mark.asyncio
async def test_collect_all_metrics(generic_config):
    """Test collecting all metrics"""
    collector = GenericCollector(generic_config)
    
    with patch.object(collector, '_collect_performance_metrics', new_callable=AsyncMock) as mock_perf:
        with patch.object(collector, '_collect_resource_metrics', new_callable=AsyncMock) as mock_resource:
            with patch.object(collector, '_collect_application_metrics', new_callable=AsyncMock) as mock_app:
                with patch.object(collector, '_collect_gpu_metrics', new_callable=AsyncMock) as mock_gpu:
                    mock_perf.return_value = []
                    mock_resource.return_value = []
                    mock_app.return_value = []
                    mock_gpu.return_value = []
                    
                    result = await collector.collect_all_metrics()
                    
                    assert result.success == True
                    assert result.provider == "vultr"
                    assert result.customer_id == "test_customer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
