"""
Application Metrics Reader
Phase 6.5: Application Agent Refactor
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .clickhouse_reader import ClickHouseReader

logger = logging.getLogger(__name__)


class ApplicationReader:
    """
    Reader for application quality metrics from ClickHouse
    
    Provides methods to query quality, hallucination, and toxicity data
    """
    
    def __init__(self):
        """Initialize application reader"""
        self.reader = ClickHouseReader()
        self.logger = logging.getLogger(f"{__name__}.ApplicationReader")
    
    def get_quality_metrics(
        self,
        customer_id: str,
        provider: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        application_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get quality metrics
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            start_date: Start date for filtering
            end_date: End date for filtering
            application_id: Filter by specific application
        
        Returns:
            List of quality metrics
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        query = """
            SELECT
                timestamp,
                provider,
                application_id,
                application_name,
                metric_type,
                score,
                details,
                model_name,
                metadata
            FROM application_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND metric_type = 'quality'
              AND timestamp >= %(start_date)s
              AND timestamp <= %(end_date)s
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': start_date,
            'end_date': end_date
        }
        
        if application_id:
            query += " AND application_id = %(application_id)s"
            params['application_id'] = application_id
        
        query += " ORDER BY timestamp DESC"
        
        return self.reader.execute_query(query, params)
    
    def get_hallucination_metrics(
        self,
        customer_id: str,
        provider: str,
        hours: int = 24,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get hallucination detection metrics
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            hours: Number of hours to look back
            threshold: Minimum hallucination score to include
        
        Returns:
            List of hallucination metrics
        """
        start_date = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT
                timestamp,
                application_id,
                application_name,
                score,
                details,
                model_name,
                prompt_text,
                response_text
            FROM application_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND metric_type = 'hallucination'
              AND timestamp >= %(start_date)s
              AND score >= %(threshold)s
            ORDER BY score DESC, timestamp DESC
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': start_date,
            'threshold': threshold
        }
        
        return self.reader.execute_query(query, params)
    
    def get_toxicity_metrics(
        self,
        customer_id: str,
        provider: str,
        hours: int = 24,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Get toxicity/safety metrics
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            hours: Number of hours to look back
            threshold: Minimum toxicity score to include
        
        Returns:
            List of toxicity metrics
        """
        start_date = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT
                timestamp,
                application_id,
                application_name,
                score,
                details,
                model_name,
                response_text
            FROM application_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND metric_type = 'toxicity'
              AND timestamp >= %(start_date)s
              AND score >= %(threshold)s
            ORDER BY score DESC, timestamp DESC
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': start_date,
            'threshold': threshold
        }
        
        return self.reader.execute_query(query, params)
    
    def get_application_summary(
        self,
        customer_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Get application quality summary
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
        
        Returns:
            Summary dictionary
        """
        # Get average scores by metric type
        summary_query = """
            SELECT
                metric_type,
                AVG(score) as avg_score,
                MAX(score) as max_score,
                MIN(score) as min_score,
                COUNT(*) as count
            FROM application_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
            GROUP BY metric_type
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': datetime.now() - timedelta(hours=24)
        }
        
        metrics = self.reader.execute_query(summary_query, params)
        
        # Get application count
        app_count_query = """
            SELECT COUNT(DISTINCT application_id) as app_count
            FROM application_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
        """
        
        app_result = self.reader.execute_query(app_count_query, params)
        app_count = app_result[0]['app_count'] if app_result else 0
        
        return {
            'provider': provider,
            'application_count': app_count,
            'metrics_by_type': metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_model_performance(
        self,
        customer_id: str,
        provider: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics by model
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            hours: Number of hours to look back
        
        Returns:
            List of model performance metrics
        """
        start_date = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT
                model_name,
                metric_type,
                AVG(score) as avg_score,
                COUNT(*) as sample_count
            FROM application_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
            GROUP BY model_name, metric_type
            ORDER BY model_name, metric_type
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': start_date
        }
        
        return self.reader.execute_query(query, params)
    
    def close(self):
        """Close ClickHouse connection"""
        self.reader.close()
