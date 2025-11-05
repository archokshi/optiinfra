"""
GCP Base Collector

Base class for all GCP collectors with common functionality.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from google.cloud import service_usage_v1
from google.oauth2 import service_account
from google.api_core import retry
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted
import os

logger = logging.getLogger(__name__)


class GCPBaseCollector:
    """Base class for GCP collectors with common functionality"""
    
    # Rate limit: 300 requests per minute per project
    MAX_REQUESTS_PER_MINUTE = 300
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize GCP base collector.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON key
            **kwargs: Additional configuration
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.credentials_path = credentials_path or os.getenv('GCP_CREDENTIALS_PATH')
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be provided")
        
        # Initialize credentials
        self.credentials = self._get_credentials()
        
        # Rate limiting tracking
        self.api_calls = []
        self.api_call_window = 60  # seconds
        
        logger.info(f"Initialized GCP collector for project: {self.project_id}")
    
    def _get_credentials(self) -> Optional[service_account.Credentials]:
        """
        Load GCP service account credentials.
        
        Returns:
            Service account credentials or None (uses ADC)
        """
        if self.credentials_path and os.path.exists(self.credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                logger.info("Loaded credentials from service account file")
                return credentials
            except Exception as e:
                logger.error(f"Failed to load credentials from {self.credentials_path}: {e}")
                raise
        else:
            # Use Application Default Credentials (ADC)
            logger.info("Using Application Default Credentials")
            return None
    
    def get_client(self, client_class, **kwargs):
        """
        Get a Google Cloud client.
        
        Args:
            client_class: Client class to instantiate
            **kwargs: Additional client arguments
        
        Returns:
            Initialized client
        """
        try:
            if self.credentials:
                client = client_class(
                    credentials=self.credentials,
                    project=self.project_id,
                    **kwargs
                )
            else:
                client = client_class(
                    project=self.project_id,
                    **kwargs
                )
            
            return client
        except Exception as e:
            logger.error(f"Failed to create client {client_class.__name__}: {e}")
            raise
    
    def handle_rate_limiting(self, func, *args, **kwargs):
        """
        Execute function with rate limit handling.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        """
        # Check rate limit
        self._check_rate_limit()
        
        # Execute with retry on rate limit errors
        @retry.Retry(
            predicate=retry.if_exception_type(ResourceExhausted),
            initial=1.0,
            maximum=60.0,
            multiplier=2.0,
            deadline=300.0
        )
        def _execute():
            self.log_api_call()
            return func(*args, **kwargs)
        
        try:
            return _execute()
        except GoogleAPIError as e:
            logger.error(f"GCP API error: {e}")
            raise
    
    def _check_rate_limit(self):
        """Check if we're within rate limits"""
        current_time = time.time()
        
        # Remove old API calls outside the window
        self.api_calls = [
            call_time for call_time in self.api_calls
            if current_time - call_time < self.api_call_window
        ]
        
        # Check if we've hit the limit
        if len(self.api_calls) >= self.MAX_REQUESTS_PER_MINUTE:
            sleep_time = self.api_call_window - (current_time - self.api_calls[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.api_calls = []
    
    def log_api_call(self):
        """Log an API call for rate limiting"""
        self.api_calls.append(time.time())
    
    def paginate_results(
        self,
        list_method,
        result_key: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Paginate through API results.
        
        Args:
            list_method: Method that returns paginated results
            result_key: Key in response containing results
            **kwargs: Arguments for list_method
        
        Returns:
            All results combined
        """
        all_results = []
        page_token = None
        
        while True:
            if page_token:
                kwargs['page_token'] = page_token
            
            try:
                response = self.handle_rate_limiting(list_method, **kwargs)
                
                # Handle different response types
                if hasattr(response, result_key):
                    results = getattr(response, result_key)
                elif isinstance(response, dict):
                    results = response.get(result_key, [])
                else:
                    # Iterator response
                    results = list(response)
                
                all_results.extend(results)
                
                # Check for next page
                if hasattr(response, 'next_page_token'):
                    page_token = response.next_page_token
                elif isinstance(response, dict):
                    page_token = response.get('nextPageToken')
                else:
                    break
                
                if not page_token:
                    break
                    
            except Exception as e:
                logger.error(f"Pagination error: {e}")
                break
        
        return all_results
    
    def get_all_projects(self) -> List[str]:
        """
        Get all accessible GCP projects.
        
        Returns:
            List of project IDs
        """
        try:
            from google.cloud import resourcemanager_v3
            
            client = self.get_client(resourcemanager_v3.ProjectsClient)
            
            projects = []
            for project in client.search_projects():
                if project.state == resourcemanager_v3.Project.State.ACTIVE:
                    projects.append(project.project_id)
            
            logger.info(f"Found {len(projects)} active projects")
            return projects
            
        except Exception as e:
            logger.warning(f"Failed to list projects: {e}")
            return [self.project_id]
    
    def _extract_labels(self, labels: Dict[str, str]) -> Dict[str, str]:
        """
        Extract and normalize GCP labels.
        
        Args:
            labels: GCP resource labels
        
        Returns:
            Normalized labels dict
        """
        return dict(labels) if labels else {}
