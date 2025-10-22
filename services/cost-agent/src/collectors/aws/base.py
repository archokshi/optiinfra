"""
Base AWS Collector

Provides common functionality for all AWS collectors including:
- Session management
- Credential handling
- Retry logic with exponential backoff
- Rate limit handling
- Connection pooling
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class AWSBaseCollector:
    """Base class for all AWS collectors with common functionality"""
    
    # Cost Explorer rate limit: 400 requests/hour
    COST_EXPLORER_RATE_LIMIT = 400
    RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
    
    def __init__(
        self,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        session_name: str = "optiinfra-collector"
    ):
        """
        Initialize AWS base collector.
        
        Args:
            access_key_id: AWS access key (or use env var AWS_ACCESS_KEY_ID)
            secret_access_key: AWS secret key (or use env var AWS_SECRET_ACCESS_KEY)
            region: AWS region (default: us-east-1)
            session_name: Session name for logging
        """
        self.access_key_id = access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_access_key = secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.session_name = session_name
        
        # API call tracking for rate limiting
        self.api_calls: Dict[str, List[float]] = {}
        
        # Session cache
        self._session: Optional[boto3.Session] = None
        self._clients: Dict[str, Any] = {}
        
        logger.info(f"Initialized {self.__class__.__name__} for region {self.region}")
    
    def get_session(self) -> boto3.Session:
        """
        Get or create boto3 session.
        
        Returns:
            boto3.Session: Configured session
        
        Raises:
            NoCredentialsError: If credentials not found
        """
        if self._session is None:
            try:
                if self.access_key_id and self.secret_access_key:
                    self._session = boto3.Session(
                        aws_access_key_id=self.access_key_id,
                        aws_secret_access_key=self.secret_access_key,
                        region_name=self.region
                    )
                else:
                    # Use default credential chain (env vars, ~/.aws, IAM role)
                    self._session = boto3.Session(region_name=self.region)
                
                logger.info(f"Created boto3 session for region {self.region}")
            except Exception as e:
                logger.error(f"Failed to create boto3 session: {e}")
                raise
        
        return self._session
    
    def get_client(
        self,
        service_name: str,
        region: Optional[str] = None
    ) -> Any:
        """
        Get boto3 client with retry configuration.
        
        Args:
            service_name: AWS service name (e.g., 'ec2', 'ce', 'cloudwatch')
            region: Optional region override
        
        Returns:
            boto3 client with retry config
        """
        region = region or self.region
        cache_key = f"{service_name}:{region}"
        
        if cache_key not in self._clients:
            session = self.get_session()
            
            # Configure retries and timeouts
            config = Config(
                region_name=region,
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                connect_timeout=10,
                read_timeout=60
            )
            
            try:
                self._clients[cache_key] = session.client(
                    service_name,
                    config=config
                )
                logger.debug(f"Created {service_name} client for region {region}")
            except Exception as e:
                logger.error(f"Failed to create {service_name} client: {e}")
                raise
        
        return self._clients[cache_key]
    
    def paginate_results(
        self,
        client: Any,
        method_name: str,
        result_key: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Helper for paginated API calls.
        
        Args:
            client: boto3 client
            method_name: API method name
            result_key: Key in response containing results
            **kwargs: Arguments to pass to API method
        
        Returns:
            List of all results across pages
        """
        results = []
        
        try:
            paginator = client.get_paginator(method_name)
            page_iterator = paginator.paginate(**kwargs)
            
            for page in page_iterator:
                if result_key in page:
                    results.extend(page[result_key])
            
            logger.debug(f"Paginated {method_name}: {len(results)} results")
        except Exception as e:
            logger.error(f"Pagination failed for {method_name}: {e}")
            raise
        
        return results
    
    @retry(
        retry=retry_if_exception_type(ClientError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def handle_throttling(self, func, *args, **kwargs):
        """
        Execute function with automatic retry on throttling.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            ClientError: If error is not throttling or max retries exceeded
        """
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            if error_code in ['ThrottlingException', 'RequestLimitExceeded', 'TooManyRequestsException']:
                logger.warning(f"Throttled, retrying: {error_code}")
                raise  # Will be retried by @retry decorator
            else:
                logger.error(f"AWS API error: {error_code} - {e}")
                raise
    
    def log_api_call(self, service: str, operation: str):
        """
        Track API call for rate limiting.
        
        Args:
            service: AWS service name
            operation: API operation name
        """
        key = f"{service}:{operation}"
        current_time = time.time()
        
        # Initialize if needed
        if key not in self.api_calls:
            self.api_calls[key] = []
        
        # Add current call
        self.api_calls[key].append(current_time)
        
        # Clean up old calls (outside rate limit window)
        cutoff_time = current_time - self.RATE_LIMIT_WINDOW
        self.api_calls[key] = [
            t for t in self.api_calls[key]
            if t > cutoff_time
        ]
        
        # Log warning if approaching rate limit
        call_count = len(self.api_calls[key])
        if service == 'cost_explorer' and call_count > self.COST_EXPLORER_RATE_LIMIT * 0.8:
            logger.warning(
                f"Approaching Cost Explorer rate limit: "
                f"{call_count}/{self.COST_EXPLORER_RATE_LIMIT} calls in last hour"
            )
    
    def check_rate_limit(self, service: str, operation: str) -> bool:
        """
        Check if we're within rate limits.
        
        Args:
            service: AWS service name
            operation: API operation name
        
        Returns:
            True if within limits, False if limit exceeded
        """
        key = f"{service}:{operation}"
        
        if key not in self.api_calls:
            return True
        
        current_time = time.time()
        cutoff_time = current_time - self.RATE_LIMIT_WINDOW
        
        # Count recent calls
        recent_calls = [
            t for t in self.api_calls[key]
            if t > cutoff_time
        ]
        
        if service == 'cost_explorer':
            return len(recent_calls) < self.COST_EXPLORER_RATE_LIMIT
        
        return True
    
    def get_account_id(self) -> str:
        """
        Get AWS account ID.
        
        Returns:
            AWS account ID
        """
        try:
            sts_client = self.get_client('sts')
            response = sts_client.get_caller_identity()
            account_id = response['Account']
            logger.info(f"AWS Account ID: {account_id}")
            return account_id
        except Exception as e:
            logger.error(f"Failed to get account ID: {e}")
            raise
    
    def validate_credentials(self) -> bool:
        """
        Validate AWS credentials.
        
        Returns:
            True if credentials are valid
        """
        try:
            self.get_account_id()
            return True
        except NoCredentialsError:
            logger.error("No AWS credentials found")
            return False
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return False
    
    def get_regions(self, service: str = 'ec2') -> List[str]:
        """
        Get list of available AWS regions for a service.
        
        Args:
            service: AWS service name (default: ec2)
        
        Returns:
            List of region names
        """
        try:
            session = self.get_session()
            regions = session.get_available_regions(service)
            logger.debug(f"Found {len(regions)} regions for {service}")
            return regions
        except Exception as e:
            logger.error(f"Failed to get regions: {e}")
            return [self.region]  # Fallback to default region
    
    def close(self):
        """Close all clients and cleanup resources"""
        self._clients.clear()
        self._session = None
        logger.info(f"Closed {self.__class__.__name__}")
