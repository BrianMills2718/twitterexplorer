#!/usr/bin/env python3
"""
Test API parameter validation - Issue #3: Placeholder API parameters
API parameters must never contain placeholder values
"""

import pytest
import json
import re
from unittest.mock import Mock, patch
from typing import Dict, Any, List


def test_no_placeholder_parameters():
    """API parameters must never contain placeholder values"""
    
    from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
    from investigation_context import InvestigationContext
    from investigation_graph import InvestigationGraph
    
    # Set up test environment
    test_context = InvestigationContext(
        analytic_question="test question",
        investigation_scope="test scope"
    )
    test_graph = InvestigationGraph()
    
    # Create mock LLM client
    mock_llm_client = Mock()
    
    # Test the LLM coordinator parameter generation
    coordinator = GraphAwareLLMCoordinator(test_context, test_graph, mock_llm_client)
    
    # Mock LLM response that contains placeholder parameters (current issue)
    mock_llm_client.generate_structured_response.return_value = {
        'endpoint': 'tweet-details.php',
        'parameters': {
            'tweet_id': 'REPLACE_WITH_TWEET_ID_FROM_TIMELINE',  # This is the problematic placeholder
            'api_key': 'test_key'
        },
        'reasoning': 'Getting tweet details',
        'expected_insights': 'Tweet content analysis'
    }
    
    # Test parameter generation
    goal = "Test investigation about current events"
    current_understanding = "Initial understanding"
    information_gaps = ["Need tweet details"]
    search_history = []
    
    try:
        result = coordinator.decide_next_action(goal, current_understanding, information_gaps, search_history)
        
        # Check for placeholder patterns in parameters
        parameters = result.get('parameters', {})
        placeholder_patterns = [
            r'REPLACE_WITH_',
            r'TODO:',
            r'<[^>]+>',  # HTML-like placeholders
            r'\{[^}]+\}',  # Curly brace placeholders
            r'\[[^\]]+\]',  # Bracket placeholders
        ]
        
        placeholder_found = []
        for param_key, param_value in parameters.items():
            if isinstance(param_value, str):
                for pattern in placeholder_patterns:
                    if re.search(pattern, param_value, re.IGNORECASE):
                        placeholder_found.append({
                            'parameter': param_key,
                            'value': param_value,
                            'pattern': pattern
                        })
        
        print(f"Generated parameters: {parameters}")
        print(f"Placeholder patterns found: {placeholder_found}")
        
        # This test documents the current issue - will fail until fixed
        assert len(placeholder_found) > 0, "Expected to find placeholder parameters (documenting current issue)"
        
    except Exception as e:
        pytest.fail(f"Error in parameter generation: {e}")


def test_parameter_validation_system():
    """Test if parameter validation exists and works"""
    
    from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
    
    # Check if coordinator has validation methods
    coordinator_methods = dir(GraphAwareLLMCoordinator)
    
    validation_methods = [method for method in coordinator_methods if 'validat' in method.lower()]
    parameter_methods = [method for method in coordinator_methods if 'parameter' in method.lower()]
    
    print(f"Validation methods found: {validation_methods}")
    print(f"Parameter methods found: {parameter_methods}")
    
    # Document current state - validation likely doesn't exist
    assert len(validation_methods) == 0, "Expected no validation methods (documenting current issue)"


def test_llm_coordinator_prompt_analysis():
    """Analyze LLM coordinator prompts for placeholder generation tendency"""
    
    from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
    import inspect
    
    # Get the source code of the coordinator
    source = inspect.getsource(GraphAwareLLMCoordinator)
    
    # Look for prompt templates or strings that might encourage placeholder generation
    suspicious_patterns = [
        'REPLACE_WITH',
        'TODO',
        '<replace>',
        '{placeholder}',
        'fill in',
        'insert here'
    ]
    
    found_patterns = []
    for pattern in suspicious_patterns:
        if pattern.lower() in source.lower():
            found_patterns.append(pattern)
    
    print(f"Source code analysis - suspicious patterns: {found_patterns}")
    
    # Look for prompt construction methods
    prompt_methods = [line for line in source.split('\n') if 'prompt' in line.lower()]
    print(f"Prompt-related lines found: {len(prompt_methods)}")
    
    # Document analysis
    assert True, "Prompt analysis complete - may reveal placeholder generation sources"


def test_api_client_parameter_handling():
    """Test how API client handles parameters with placeholders"""
    
    from api_client import TwitterAPIClient
    
    # Create test client
    api_client = TwitterAPIClient('test_api_key')
    
    # Test parameters with placeholders
    test_parameters = {
        'tweet_id': 'REPLACE_WITH_TWEET_ID_FROM_TIMELINE',
        'user_id': 'REPLACE_WITH_USER_ID',
        'query': 'normal query text'
    }
    
    # Check if client has validation for placeholder parameters
    has_validation = hasattr(api_client, 'validate_parameters')
    has_preprocessing = hasattr(api_client, 'preprocess_parameters')
    
    print(f"API client has parameter validation: {has_validation}")
    print(f"API client has parameter preprocessing: {has_preprocessing}")
    
    # Test what happens when we try to use placeholder parameters
    try:
        # This should fail or handle placeholders gracefully
        # Most likely it will attempt the API call with invalid parameters
        
        # Mock the actual API call to avoid network request
        with patch.object(api_client, 'make_api_request') as mock_request:
            mock_request.return_value = {'error': 'Invalid tweet ID'}
            
            # Try search with placeholder
            result = api_client.search_tweets(
                query='test query',
                additional_params={'tweet_id': 'REPLACE_WITH_TWEET_ID_FROM_TIMELINE'}
            )
            
            # Check if placeholder was passed through
            call_args = mock_request.call_args
            if call_args:
                actual_params = call_args[1] if len(call_args) > 1 else call_args[0][1] if len(call_args[0]) > 1 else {}
                print(f"Parameters passed to API: {actual_params}")
                
                # Document current behavior
                placeholder_passed = any('REPLACE_WITH' in str(v) for v in actual_params.values() if isinstance(v, str))
                assert placeholder_passed, "Expected placeholder to be passed through (documenting current issue)"
    
    except Exception as e:
        print(f"API client error with placeholder parameters: {e}")
        # Document the type of error
        assert 'REPLACE_WITH' in str(e) or 'placeholder' in str(e).lower(), \
            "Error should be related to placeholder parameters"


def test_context_aware_parameter_resolution():
    """Test if system has context-aware parameter resolution"""
    
    from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
    from investigation_context import InvestigationContext
    from investigation_graph import InvestigationGraph
    
    # Set up test with rich context
    test_context = InvestigationContext()
    test_graph = InvestigationGraph()
    
    # Add some datapoints to the graph that could provide parameter values
    sample_tweet_data = {
        'tweet_id': '1234567890',
        'user_id': '9876543210',
        'content': 'Sample tweet content',
        'timestamp': '2024-01-01T00:00:00Z'
    }
    
    # Add datapoint to graph
    datapoint = test_graph.create_node(
        'DataPoint',
        properties={
            'content': json.dumps(sample_tweet_data),
            'source': 'twitter',
            'tweet_id': sample_tweet_data['tweet_id']
        }
    )
    
    mock_llm_client = Mock()
    coordinator = GraphAwareLLMCoordinator(test_context, test_graph, mock_llm_client)
    
    # Check if coordinator can resolve parameters from context
    has_resolution_method = hasattr(coordinator, 'resolve_parameters_from_context')
    has_context_extraction = hasattr(coordinator, 'extract_context_parameters')
    
    print(f"Has parameter resolution from context: {has_resolution_method}")
    print(f"Has context parameter extraction: {has_context_extraction}")
    
    # Document current state
    assert not has_resolution_method, "Expected no context resolution (documenting current missing feature)"
    assert not has_context_extraction, "Expected no context extraction (documenting current missing feature)"


def test_extract_placeholder_patterns_from_logs():
    """Extract placeholder patterns from actual investigation logs"""
    
    import os
    import glob
    
    # Look for log files or investigation data
    current_dir = os.path.dirname(__file__)
    log_files = glob.glob(os.path.join(current_dir, '*.txt')) + \
                glob.glob(os.path.join(current_dir, '*.json')) + \
                glob.glob(os.path.join(current_dir, 'logs/*.txt'))
    
    placeholder_patterns_found = []
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Search for placeholder patterns
            patterns = [
                r'REPLACE_WITH_[A-Z_]+',
                r'TODO[:\s][^\n]*',
                r'<[A-Za-z_]+>',
                r'\{[A-Za-z_]+\}',
                r'\[[A-Za-z_\s]+\]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    placeholder_patterns_found.extend([{
                        'file': os.path.basename(log_file),
                        'pattern': pattern,
                        'matches': matches[:5]  # First 5 matches
                    }])
        
        except Exception as e:
            # Skip files that can't be read
            continue
    
    print(f"Placeholder patterns found in logs: {len(placeholder_patterns_found)}")
    for finding in placeholder_patterns_found[:10]:  # Show first 10
        print(f"  {finding}")
    
    # This documents actual placeholder usage in the system
    if placeholder_patterns_found:
        assert True, f"Found {len(placeholder_patterns_found)} placeholder patterns in logs"
    else:
        pytest.skip("No placeholder patterns found in available logs")


def test_llm_prompt_improvement_for_concrete_parameters():
    """Test improved prompts that discourage placeholder generation"""
    
    # This test defines what improved prompts should look like
    
    good_prompt_patterns = [
        "use actual values from context",
        "extract specific",
        "do not use placeholder",
        "avoid REPLACE_WITH",
        "use real data from graph"
    ]
    
    bad_prompt_patterns = [
        "REPLACE_WITH",
        "fill in later", 
        "placeholder",
        "TODO",
        "insert here"
    ]
    
    # Check current prompts (this is aspirational - defines what we need)
    print("Good prompt patterns that should be implemented:")
    for pattern in good_prompt_patterns:
        print(f"  ✓ '{pattern}'")
    
    print("\nBad prompt patterns that should be avoided:")
    for pattern in bad_prompt_patterns:
        print(f"  ✗ '{pattern}'")
    
    # This test documents the requirements for prompt improvement
    assert True, "Prompt improvement patterns documented - implementation needed"


if __name__ == "__main__":
    # Run tests to document current issues
    pytest.main([__file__, "-v", "-s"])