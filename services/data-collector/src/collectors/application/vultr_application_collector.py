"""
Vultr Application Collector
Phase 6.5: Application Quality Monitoring with Groq LLM
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from ..base import BaseCollector
from ...models.metrics import ApplicationMetric, CollectionResult
from .groq_client import GroqClient

logger = logging.getLogger(__name__)


class VultrApplicationCollector(BaseCollector):
    """
    Collects application quality metrics from Vultr-hosted applications
    Uses Groq LLM for quality analysis
    """
    
    def __init__(self, api_key: str, customer_id: str, groq_api_key: str):
        """
        Initialize Vultr application collector
        
        Args:
            api_key: Vultr API key (for future use)
            customer_id: Customer ID for tracking
            groq_api_key: Groq API key for LLM analysis
        """
        super().__init__(api_key, customer_id)
        self.groq_client = GroqClient(api_key=groq_api_key)
        self.application_metrics: List[ApplicationMetric] = []
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "vultr"
    
    def get_data_type(self) -> str:
        """Get data type"""
        return "application"
    
    def validate_credentials(self) -> bool:
        """
        Validate credentials
        
        Returns:
            True if credentials are valid
        """
        # For now, just check if Groq API key exists
        return bool(self.groq_client)
    
    def collect(self) -> CollectionResult:
        """
        Collect application quality metrics
        
        Returns:
            CollectionResult with collection details
        """
        started_at = datetime.now()
        self.log_collection_start()
        
        try:
            # Clear previous metrics
            self.application_metrics = []
            
            # Collect different types of metrics
            self._collect_quality_metrics()
            self._collect_hallucination_metrics()
            self._collect_toxicity_metrics()
            
            completed_at = datetime.now()
            
            result = CollectionResult(
                customer_id=self.customer_id,
                provider=self.get_provider_name(),
                data_type=self.get_data_type(),
                success=True,
                records_collected=len(self.application_metrics),
                started_at=started_at,
                completed_at=completed_at
            )
            
            self.log_collection_end(result)
            return result
            
        except Exception as e:
            return self.handle_error(e)
    
    def _collect_quality_metrics(self):
        """Collect quality metrics for sample interactions"""
        try:
            # Sample LLM interactions to analyze
            # In production, these would come from actual application logs
            sample_interactions = self._get_sample_interactions()
            
            for interaction in sample_interactions:
                app_id = interaction.get("application_id")
                app_name = interaction.get("application_name")
                model = interaction.get("model_name")
                prompt = interaction.get("prompt")
                response = interaction.get("response")
                
                # Analyze quality using Groq
                quality_scores = self.groq_client.analyze_quality(
                    prompt=prompt,
                    response=response,
                    model_name=model
                )
                
                # Create metric for overall quality
                metric = ApplicationMetric(
                    timestamp=datetime.now(),
                    customer_id=self.customer_id,
                    provider=self.get_provider_name(),
                    application_id=app_id,
                    application_name=app_name,
                    metric_type="quality",
                    score=quality_scores.get("overall_quality", 0.0),
                    details=f"Coherence: {quality_scores.get('coherence', 0):.2f}, "
                           f"Relevance: {quality_scores.get('relevance', 0):.2f}, "
                           f"Accuracy: {quality_scores.get('accuracy', 0):.2f}",
                    model_name=model,
                    prompt_text=prompt[:500],  # Truncate for storage
                    response_text=response[:500],
                    metadata=quality_scores
                )
                
                self.application_metrics.append(metric)
            
            self.logger.info(f"Collected quality metrics for {len(sample_interactions)} interactions")
            
        except Exception as e:
            self.logger.error(f"Failed to collect quality metrics: {e}", exc_info=True)
    
    def _collect_hallucination_metrics(self):
        """Collect hallucination detection metrics"""
        try:
            sample_interactions = self._get_sample_interactions()
            
            for interaction in sample_interactions:
                app_id = interaction.get("application_id")
                app_name = interaction.get("application_name")
                model = interaction.get("model_name")
                prompt = interaction.get("prompt")
                response = interaction.get("response")
                
                # Detect hallucinations using Groq
                hallucination_result = self.groq_client.detect_hallucination(
                    prompt=prompt,
                    response=response
                )
                
                metric = ApplicationMetric(
                    timestamp=datetime.now(),
                    customer_id=self.customer_id,
                    provider=self.get_provider_name(),
                    application_id=app_id,
                    application_name=app_name,
                    metric_type="hallucination",
                    score=hallucination_result.get("hallucination_score", 0.0),
                    details=hallucination_result.get("reasoning", ""),
                    model_name=model,
                    prompt_text=prompt[:500],
                    response_text=response[:500],
                    metadata=hallucination_result
                )
                
                self.application_metrics.append(metric)
            
            self.logger.info(f"Collected hallucination metrics for {len(sample_interactions)} interactions")
            
        except Exception as e:
            self.logger.error(f"Failed to collect hallucination metrics: {e}", exc_info=True)
    
    def _collect_toxicity_metrics(self):
        """Collect toxicity/safety metrics"""
        try:
            sample_interactions = self._get_sample_interactions()
            
            for interaction in sample_interactions:
                app_id = interaction.get("application_id")
                app_name = interaction.get("application_name")
                model = interaction.get("model_name")
                response = interaction.get("response")
                
                # Check toxicity using Groq
                toxicity_scores = self.groq_client.check_toxicity(text=response)
                
                metric = ApplicationMetric(
                    timestamp=datetime.now(),
                    customer_id=self.customer_id,
                    provider=self.get_provider_name(),
                    application_id=app_id,
                    application_name=app_name,
                    metric_type="toxicity",
                    score=1.0 - toxicity_scores.get("overall_safety", 1.0),  # Invert safety to toxicity
                    details=f"Toxicity: {toxicity_scores.get('toxicity', 0):.2f}, "
                           f"Hate: {toxicity_scores.get('hate_speech', 0):.2f}",
                    model_name=model,
                    prompt_text="",
                    response_text=response[:500],
                    metadata=toxicity_scores
                )
                
                self.application_metrics.append(metric)
            
            self.logger.info(f"Collected toxicity metrics for {len(sample_interactions)} interactions")
            
        except Exception as e:
            self.logger.error(f"Failed to collect toxicity metrics: {e}", exc_info=True)
    
    def _get_sample_interactions(self) -> List[Dict[str, Any]]:
        """
        Get sample LLM interactions to analyze
        
        In production, this would fetch from:
        - Application logs
        - LLM gateway/proxy
        - Monitoring systems
        
        Returns:
            List of interaction dictionaries
        """
        # Sample data for demonstration
        return [
            {
                "application_id": "app-001",
                "application_name": "Customer Support Bot",
                "model_name": "llama-3.1-70b",
                "prompt": "How do I reset my password?",
                "response": "To reset your password, go to the login page and click 'Forgot Password'. "
                           "Enter your email address and you'll receive a reset link within a few minutes."
            },
            {
                "application_id": "app-002",
                "application_name": "Code Assistant",
                "model_name": "llama-3.1-70b",
                "prompt": "Write a Python function to calculate fibonacci numbers",
                "response": "Here's a Python function to calculate Fibonacci numbers:\n\n"
                           "def fibonacci(n):\n"
                           "    if n <= 1:\n"
                           "        return n\n"
                           "    return fibonacci(n-1) + fibonacci(n-2)"
            }
        ]
    
    def get_metrics(self) -> List[ApplicationMetric]:
        """
        Get collected metrics
        
        Returns:
            List of ApplicationMetric objects
        """
        return self.application_metrics
