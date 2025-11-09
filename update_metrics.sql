UPDATE cloud_credentials 
SET metadata = '{"prometheus_metrics": {"gpu_utilization": "gpu_utilization_percent", "gpu_memory": "gpu_memory_utilization_percent", "gpu_temperature": "gpu_temperature_celsius", "gpu_power": "gpu_power_draw_watts", "throughput": "vllm_throughput_prompts_per_second", "tokens_generated": "vllm_tokens_generated_total", "request_latency": "vllm_request_latency_seconds", "requests_total": "vllm_requests_total", "quality_score": "vllm_quality_score"}}' 
WHERE provider = 'runpod' 
  AND customer_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' 
  AND credential_name = 'RunPod L4 with Cost Tracking';
