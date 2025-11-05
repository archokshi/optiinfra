"""
GPU Metrics Collector

Collects GPU metrics using nvidia-smi (pynvml).
"""

import logging
from typing import Optional, List
from datetime import datetime

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    logging.warning("pynvml not available - GPU metrics collection disabled")

from src.models.gpu_metrics import (
    GPUMetricsCollection,
    SingleGPUMetrics,
    GPUUtilization,
    GPUMemory,
    GPUPower,
    GPUTemperature,
    GPUClockSpeeds,
    GPUProcessInfo
)

logger = logging.getLogger("resource_agent.gpu_collector")


class GPUCollector:
    """Collector for NVIDIA GPU metrics using pynvml."""
    
    def __init__(self):
        """Initialize GPU collector."""
        self.initialized = False
        self.gpu_count = 0
        
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_count = pynvml.nvmlDeviceGetCount()
                self.initialized = True
                logger.info(f"GPU collector initialized with {self.gpu_count} GPUs")
            except Exception as e:
                logger.error(f"Failed to initialize pynvml: {e}")
                self.initialized = False
        else:
            logger.warning("pynvml not available - GPU metrics collection disabled")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
    
    def shutdown(self):
        """Shutdown pynvml."""
        if self.initialized and PYNVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
                logger.info("GPU collector shutdown")
            except Exception as e:
                logger.error(f"Error shutting down pynvml: {e}")
    
    def is_available(self) -> bool:
        """Check if GPU metrics collection is available."""
        return self.initialized and PYNVML_AVAILABLE
    
    def collect_gpu_metrics(self, gpu_index: int) -> Optional[SingleGPUMetrics]:
        """
        Collect metrics for a single GPU.
        
        Args:
            gpu_index: GPU index (0-based)
            
        Returns:
            SingleGPUMetrics or None if collection fails
        """
        if not self.is_available():
            return None
        
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
            
            # Basic info
            name = pynvml.nvmlDeviceGetName(handle)
            uuid = pynvml.nvmlDeviceGetUUID(handle)
            driver_version = pynvml.nvmlSystemGetDriverVersion()
            
            # Utilization
            utilization_rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = utilization_rates.gpu
            memory_util = utilization_rates.memory
            
            # Try to get encoder/decoder utilization (may not be available on all GPUs)
            try:
                encoder_util = pynvml.nvmlDeviceGetEncoderUtilization(handle)[0]
                decoder_util = pynvml.nvmlDeviceGetDecoderUtilization(handle)[0]
            except:
                encoder_util = None
                decoder_util = None
            
            utilization = GPUUtilization(
                gpu_percent=float(gpu_util),
                memory_percent=float(memory_util),
                encoder_percent=float(encoder_util) if encoder_util is not None else None,
                decoder_percent=float(decoder_util) if decoder_util is not None else None
            )
            
            # Memory
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory = GPUMemory(
                total_mb=memory_info.total / (1024 * 1024),
                used_mb=memory_info.used / (1024 * 1024),
                free_mb=memory_info.free / (1024 * 1024),
                utilization_percent=(memory_info.used / memory_info.total) * 100
            )
            
            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            try:
                slowdown_temp = pynvml.nvmlDeviceGetTemperatureThreshold(
                    handle, pynvml.NVML_TEMPERATURE_THRESHOLD_SLOWDOWN
                )
                shutdown_temp = pynvml.nvmlDeviceGetTemperatureThreshold(
                    handle, pynvml.NVML_TEMPERATURE_THRESHOLD_SHUTDOWN
                )
            except:
                slowdown_temp = None
                shutdown_temp = None
            
            temperature = GPUTemperature(
                current_celsius=float(temp),
                slowdown_threshold_celsius=float(slowdown_temp) if slowdown_temp else None,
                shutdown_threshold_celsius=float(shutdown_temp) if shutdown_temp else None
            )
            
            # Power
            power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW to W
            power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0  # mW to W
            power = GPUPower(
                power_draw_watts=power_draw,
                power_limit_watts=power_limit,
                power_usage_percent=(power_draw / power_limit) * 100 if power_limit > 0 else 0.0
            )
            
            # Clock speeds
            graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
            sm_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
            memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            clocks = GPUClockSpeeds(
                graphics_clock_mhz=float(graphics_clock),
                sm_clock_mhz=float(sm_clock),
                memory_clock_mhz=float(memory_clock)
            )
            
            # Processes
            processes = []
            try:
                compute_processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                for proc in compute_processes:
                    try:
                        proc_name = pynvml.nvmlSystemGetProcessName(proc.pid)
                        processes.append(GPUProcessInfo(
                            pid=proc.pid,
                            process_name=proc_name,
                            used_memory_mb=proc.usedGpuMemory / (1024 * 1024) if proc.usedGpuMemory else 0.0
                        ))
                    except:
                        pass
            except:
                pass
            
            # Performance state
            try:
                perf_state = pynvml.nvmlDeviceGetPerformanceState(handle)
                perf_state_str = f"P{perf_state}"
            except:
                perf_state_str = "Unknown"
            
            # Fan speed
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except:
                fan_speed = None
            
            return SingleGPUMetrics(
                gpu_id=gpu_index,
                gpu_name=name,
                gpu_uuid=uuid,
                driver_version=driver_version,
                utilization=utilization,
                memory=memory,
                temperature=temperature,
                power=power,
                clocks=clocks,
                processes=processes,
                performance_state=perf_state_str,
                fan_speed_percent=float(fan_speed) if fan_speed is not None else None
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics for GPU {gpu_index}: {e}")
            return None
    
    def collect(self, instance_id: str) -> Optional[GPUMetricsCollection]:
        """
        Collect metrics from all GPUs.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            GPUMetricsCollection or None if collection fails
        """
        if not self.is_available():
            logger.warning("GPU metrics collection not available")
            return None
        
        try:
            gpus = []
            total_memory_used = 0.0
            total_memory_total = 0.0
            total_gpu_util = 0.0
            total_memory_util = 0.0
            total_temp = 0.0
            total_power = 0.0
            
            for i in range(self.gpu_count):
                gpu_metrics = self.collect_gpu_metrics(i)
                if gpu_metrics:
                    gpus.append(gpu_metrics)
                    total_memory_used += gpu_metrics.memory.used_mb
                    total_memory_total += gpu_metrics.memory.total_mb
                    total_gpu_util += gpu_metrics.utilization.gpu_percent
                    total_memory_util += gpu_metrics.utilization.memory_percent
                    total_temp += gpu_metrics.temperature.current_celsius
                    total_power += gpu_metrics.power.power_draw_watts
            
            if not gpus:
                return None
            
            # Calculate averages
            gpu_count = len(gpus)
            avg_gpu_util = total_gpu_util / gpu_count if gpu_count > 0 else 0.0
            avg_memory_util = total_memory_util / gpu_count if gpu_count > 0 else 0.0
            avg_temp = total_temp / gpu_count if gpu_count > 0 else 0.0
            
            return GPUMetricsCollection(
                instance_id=instance_id,
                gpu_count=gpu_count,
                gpus=gpus,
                total_memory_used_mb=total_memory_used,
                total_memory_total_mb=total_memory_total,
                average_gpu_utilization=avg_gpu_util,
                average_memory_utilization=avg_memory_util,
                average_temperature=avg_temp,
                total_power_draw_watts=total_power
            )
            
        except Exception as e:
            logger.error(f"Failed to collect GPU metrics: {e}")
            return None
