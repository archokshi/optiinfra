"""
GPU Collector Tests

Tests for GPU metrics collection.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.collectors.gpu_collector import GPUCollector, PYNVML_AVAILABLE


@pytest.fixture
def mock_pynvml():
    """Mock pynvml module."""
    with patch('src.collectors.gpu_collector.pynvml') as mock:
        # Mock device handle
        mock_handle = Mock()
        mock.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        
        # Mock basic info
        mock.nvmlDeviceGetName.return_value = "NVIDIA A100"
        mock.nvmlDeviceGetUUID.return_value = "GPU-12345"
        mock.nvmlSystemGetDriverVersion.return_value = "525.60.13"
        
        # Mock utilization
        util_mock = Mock()
        util_mock.gpu = 75
        util_mock.memory = 60
        mock.nvmlDeviceGetUtilizationRates.return_value = util_mock
        
        # Mock memory
        memory_mock = Mock()
        memory_mock.total = 80 * 1024 * 1024 * 1024  # 80GB
        memory_mock.used = 40 * 1024 * 1024 * 1024   # 40GB
        memory_mock.free = 40 * 1024 * 1024 * 1024   # 40GB
        mock.nvmlDeviceGetMemoryInfo.return_value = memory_mock
        
        # Mock temperature
        mock.nvmlDeviceGetTemperature.return_value = 65
        
        # Mock power
        mock.nvmlDeviceGetPowerUsage.return_value = 300000  # 300W in mW
        mock.nvmlDeviceGetPowerManagementLimit.return_value = 400000  # 400W in mW
        
        # Mock clocks
        mock.nvmlDeviceGetClockInfo.side_effect = [1410, 1410, 1215]  # Graphics, SM, Memory
        
        # Mock processes
        mock.nvmlDeviceGetComputeRunningProcesses.return_value = []
        
        # Mock performance state
        mock.nvmlDeviceGetPerformanceState.return_value = 0  # P0
        
        # Mock fan speed
        mock.nvmlDeviceGetFanSpeed.return_value = 50
        
        # Mock device count
        mock.nvmlDeviceGetCount.return_value = 1
        
        yield mock


@pytest.mark.skipif(not PYNVML_AVAILABLE, reason="pynvml not available")
def test_gpu_collector_initialization(mock_pynvml):
    """Test GPU collector initialization."""
    with GPUCollector() as collector:
        assert collector.is_available()
        assert collector.gpu_count == 1


@pytest.mark.skipif(not PYNVML_AVAILABLE, reason="pynvml not available")
def test_collect_single_gpu_metrics(mock_pynvml):
    """Test collecting metrics from a single GPU."""
    with GPUCollector() as collector:
        metrics = collector.collect_gpu_metrics(0)
        
        assert metrics is not None
        assert metrics.gpu_id == 0
        assert metrics.gpu_name == "NVIDIA A100"
        assert metrics.utilization.gpu_percent == 75.0
        assert metrics.memory.total_mb > 0


@pytest.mark.skipif(not PYNVML_AVAILABLE, reason="pynvml not available")
def test_collect_all_gpu_metrics(mock_pynvml):
    """Test collecting metrics from all GPUs."""
    with GPUCollector() as collector:
        metrics = collector.collect(instance_id="test-instance")
        
        assert metrics is not None
        assert metrics.gpu_count == 1
        assert len(metrics.gpus) == 1
        assert metrics.average_gpu_utilization == 75.0


def test_gpu_collector_without_pynvml():
    """Test GPU collector when pynvml is not available."""
    with patch('src.collectors.gpu_collector.PYNVML_AVAILABLE', False):
        with GPUCollector() as collector:
            assert not collector.is_available()
            assert collector.gpu_count == 0
            
            metrics = collector.collect("test")
            assert metrics is None
