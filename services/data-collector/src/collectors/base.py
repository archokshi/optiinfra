"""
Base collector class for all cloud providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..models.metrics import CollectionResult


logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Base class for all data collectors
    
    All cloud provider collectors should inherit from this class
    and implement the required methods.
    """
    
    def __init__(self, api_key: str, customer_id: str):
        """
        Initialize the collector
        
        Args:
            api_key: API key for the cloud provider
            customer_id: Customer ID for tracking
        """
        self.api_key = api_key
        self.customer_id = customer_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate API credentials
        
        Returns:
            True if credentials are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def collect(self) -> CollectionResult:
        """
        Collect data from the cloud provider
        
        Returns:
            CollectionResult with collection details
        """
        pass
    
    def handle_rate_limit(self, retry_after: int = 60):
        """
        Handle rate limiting from API
        
        Args:
            retry_after: Seconds to wait before retrying
        """
        self.logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
        import time
        time.sleep(retry_after)
    
    def handle_error(self, error: Exception) -> CollectionResult:
        """
        Handle collection errors
        
        Args:
            error: Exception that occurred
        
        Returns:
            CollectionResult with error details
        """
        self.logger.error(f"Collection error: {str(error)}", exc_info=True)
        
        return CollectionResult(
            customer_id=self.customer_id,
            provider=self.get_provider_name(),
            data_type=self.get_data_type(),
            success=False,
            records_collected=0,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message=str(error)
        )
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name
        
        Returns:
            Provider name (e.g., 'vultr', 'aws', 'gcp')
        """
        pass
    
    @abstractmethod
    def get_data_type(self) -> str:
        """
        Get the data type this collector handles
        
        Returns:
            Data type (e.g., 'cost', 'performance', 'resource', 'application')
        """
        pass
    
    def log_collection_start(self):
        """Log the start of collection"""
        self.logger.info(
            f"Starting {self.get_data_type()} collection for "
            f"{self.get_provider_name()} (customer: {self.customer_id})"
        )
    
    def log_collection_end(self, result: CollectionResult):
        """
        Log the end of collection
        
        Args:
            result: Collection result
        """
        if result.success:
            self.logger.info(
                f"Completed {self.get_data_type()} collection for "
                f"{self.get_provider_name()}: {result.records_collected} records"
            )
        else:
            self.logger.error(
                f"Failed {self.get_data_type()} collection for "
                f"{self.get_provider_name()}: {result.error_message}"
            )
