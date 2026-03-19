"""
Search Executor - Wraps API client for wave architecture

Simple wrapper around api_client.execute_api_step() to provide
a clean interface for the wave architecture.
"""

import time
import logging
from typing import Dict, Any, Optional
import api_client

logger = logging.getLogger(__name__)

class SearchExecutor:
    """
    Executes search queries against Twitter API

    Wraps api_client.execute_api_step() to provide consistent interface
    for wave architecture while maintaining compatibility with existing system.
    """

    def __init__(self, rapidapi_key: Optional[str] = None):
        """
        Initialize search executor

        Args:
            rapidapi_key: RapidAPI key for Twitter API calls. If None, will be loaded from config.
        """
        self.rapidapi_key = rapidapi_key

        # Load API key from config if not provided
        if not self.rapidapi_key:
            try:
                from .twitter_config import load_api_keys
                config = load_api_keys()
                self.rapidapi_key = config.get('rapidapi_key')
            except Exception as e:
                logger.warning(f"Could not load API key from config: {e}")
                self.rapidapi_key = None

    def execute_search(self, endpoint: str, params: Dict[str, Any],
                      reason: str = "Wave search") -> Dict[str, Any]:
        """
        Execute a search query

        Args:
            endpoint: API endpoint to call (e.g. 'search.php')
            params: Parameters for the API call
            reason: Description of why this search is being performed

        Returns:
            Dictionary containing:
            - data: The search results
            - error: Error message if search failed
            - execution_time: Time taken to execute search
            - results_count: Number of results returned
        """

        start_time = time.time()

        # Prepare search plan in format expected by api_client
        search_plan = {
            'endpoint': endpoint,
            'params': params,
            'reason': reason
        }

        logger.info(f"Executing search: {endpoint} with params {params}")

        try:
            # Execute the API call using existing api_client
            result = api_client.execute_api_step(
                search_plan,
                [],  # No dependencies
                self.rapidapi_key
            )

            execution_time = time.time() - start_time

            if 'error' in result:
                logger.warning(f"Search failed: {result['error']}")
                return {
                    'data': {},
                    'error': result['error'],
                    'execution_time': execution_time,
                    'results_count': 0
                }

            # Count results - check all possible keys where data might be
            data = result.get('data', {})
            results_count = self._count_results(data)

            logger.info(f"Search completed: {results_count} results in {execution_time:.2f}s")

            return {
                'data': data,
                'error': None,
                'execution_time': execution_time,
                'results_count': results_count
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Search execution failed: {str(e)}"
            logger.error(error_msg)

            return {
                'data': {},
                'error': error_msg,
                'execution_time': execution_time,
                'results_count': 0
            }

    def _count_results(self, data: Any) -> int:
        """Count results in API response data"""

        # List of possible keys where results might be stored
        possible_keys = [
            'timeline', 'followers', 'following', 'users',
            'trends', 'retweets', 'affilates', 'members',
            'sharings', 'results', 'data'
        ]

        # Try to find results in any of these keys
        if isinstance(data, dict):
            for key in possible_keys:
                if key in data and isinstance(data[key], list):
                    return len(data[key])

        # Check if data itself is a list
        if isinstance(data, list):
            return len(data)

        # Check if it's a single item (non-empty dict)
        if isinstance(data, dict) and data:
            return 1

        return 0

    def get_status(self) -> Dict[str, Any]:
        """Get executor status"""
        return {
            'api_key_configured': self.rapidapi_key is not None,
            'api_client_available': 'api_client' in globals()
        }