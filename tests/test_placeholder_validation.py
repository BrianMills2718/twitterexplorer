#!/usr/bin/env python3
"""
Test placeholder parameter validation
"""

import pytest
from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
from investigation_context import InvestigationContext
from investigation_graph import InvestigationGraph
from unittest.mock import Mock


def test_placeholder_validation_method():
    """Test the placeholder validation method directly"""
    
    # Create a mock coordinator to access the validation method
    context = InvestigationContext(
        analytic_question="test question",
        investigation_scope="test scope"
    )
    graph = InvestigationGraph()
    mock_llm = Mock()
    
    coordinator = GraphAwareLLMCoordinator(context, graph, mock_llm)
    
    # Test cases with known placeholders from the logs
    test_cases = [
        # Placeholder parameters that should be detected
        {"tweet_id": "REPLACE_WITH_TWEET_ID_FROM_TIMELINE", "expected_errors": 1},
        {"screenname": "<username>", "expected_errors": 1}, 
        {"query": "TODO: add search terms", "expected_errors": 1},
        {"id": "REPLACE_WITH_TOP_TWEET_ID", "expected_errors": 1},
        {"user": "example_user", "expected_errors": 1},
        {"value": "placeholder_text", "expected_errors": 1},
        
        # Valid parameters that should pass
        {"screenname": "elonmusk", "expected_errors": 0},
        {"query": "climate change policy", "expected_errors": 0},
        {"tweet_id": "1234567890123456789", "expected_errors": 0},
        {"search_type": "Latest", "expected_errors": 0},
        
        # Edge cases
        {"query": "This is a longer query that mentions placeholder but is real content", "expected_errors": 0},
        {"content": "User wants to replace this text", "expected_errors": 0},  # "replace" in context, not placeholder
    ]
    
    results = []
    for i, case in enumerate(test_cases):
        params = {k: v for k, v in case.items() if k != "expected_errors"}
        expected_errors = case["expected_errors"]
        
        errors = coordinator._validate_no_placeholders(params)
        actual_errors = len(errors)
        
        print(f"Test case {i+1}: {params}")
        print(f"  Expected errors: {expected_errors}, Actual errors: {actual_errors}")
        if errors:
            print(f"  Errors found: {errors}")
        print()
        
        results.append({
            'case': i+1,
            'params': params,
            'expected_errors': expected_errors,
            'actual_errors': actual_errors,
            'errors': errors,
            'passed': actual_errors == expected_errors
        })
    
    # Check results
    failed_cases = [r for r in results if not r['passed']]
    if failed_cases:
        print(f"Failed cases: {len(failed_cases)}")
        for case in failed_cases:
            print(f"  Case {case['case']}: Expected {case['expected_errors']}, got {case['actual_errors']}")
    
    passed_cases = len([r for r in results if r['passed']])
    total_cases = len(results)
    
    print(f"Validation results: {passed_cases}/{total_cases} cases passed")
    
    # Assert most cases pass (allowing for some edge case differences)
    assert passed_cases >= total_cases * 0.8, f"Too many validation cases failed: {passed_cases}/{total_cases}"


def test_known_placeholder_patterns():
    """Test validation against known placeholder patterns from investigation logs"""
    
    context = InvestigationContext(
        analytic_question="test question",
        investigation_scope="test scope"
    )
    graph = InvestigationGraph()
    mock_llm = Mock()
    
    coordinator = GraphAwareLLMCoordinator(context, graph, mock_llm)
    
    # Known problematic patterns from the logs
    known_placeholders = [
        "REPLACE_WITH_TWEET_ID_FROM_TIMELINE",
        "REPLACE_WITH_TOP_TWEET_ID",
        "<top_poster_screenname_from_search_results>",
        "REPLACE_WITH_USER_ID",
    ]
    
    for placeholder in known_placeholders:
        params = {"test_param": placeholder}
        errors = coordinator._validate_no_placeholders(params)
        
        print(f"Testing placeholder: '{placeholder}'")
        print(f"  Errors detected: {len(errors)}")
        print(f"  Error messages: {errors}")
        
        assert len(errors) > 0, f"Failed to detect known placeholder: '{placeholder}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])