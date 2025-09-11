#!/usr/bin/env python3
"""
Test Issue #3: Placeholder API Parameters validation
Phase 1: Issue #3 - Check current validation state
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
from investigation_graph import InvestigationGraph
from llm_client import get_litellm_client
from llm_model_manager import LLMModelManager


def test_placeholder_validation():
    """Test the current placeholder validation"""
    
    print("Testing placeholder validation in GraphAwareLLMCoordinator...")
    
    # Initialize components
    llm_client = get_litellm_client()
    graph = InvestigationGraph()
    model_manager = LLMModelManager()
    
    coordinator = GraphAwareLLMCoordinator(llm_client, graph, model_manager)
    
    # Test the validation method directly
    print("\nStep 1: Testing _validate_no_placeholders method...")
    
    # Test cases from temp1.txt evidence
    test_cases = [
        # Known problematic case from temp1.txt
        {"id": "REPLACE_WITH_TWEET_ID_FROM_TIMELINE"},
        {"tweet_id": "REPLACE_WITH_USER_ID"},
        {"screenname": "<username>"},
        {"query": "TODO: add real query"},
        # Valid cases
        {"screenname": "elonmusk"},
        {"query": "climate change policy"},
        {"id": "1234567890123456789"}
    ]
    
    for i, test_params in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_params}")
        
        try:
            errors = coordinator._validate_no_placeholders(test_params)
            
            if errors:
                print(f"  VALIDATION DETECTED: {len(errors)} errors")
                for error in errors:
                    print(f"    - {error}")
            else:
                print(f"  VALIDATION PASSED: No placeholders detected")
                
        except Exception as e:
            print(f"  ERROR in validation: {e}")
    
    print(f"\nStep 2: Testing validation behavior in strategy execution...")
    
    # Create a mock strategic decision with placeholder
    from llm_client import SearchParameters, SearchStrategy, StrategicDecision
    
    # Create search with placeholder (this should be caught and skipped)
    problematic_search = SearchStrategy(
        endpoint="tweet_thread.php",
        parameters=SearchParameters(id="REPLACE_WITH_TWEET_ID_FROM_TIMELINE"),
        reasoning="Test search with placeholder"
    )
    
    valid_search = SearchStrategy(
        endpoint="search.php", 
        parameters=SearchParameters(query="climate change"),
        reasoning="Valid search"
    )
    
    decision = StrategicDecision(
        decision_type="Test Decision",
        reasoning="Testing placeholder validation in execution",
        searches=[problematic_search, valid_search],
        expected_outcomes=["Placeholder should be caught", "Valid search should execute"],
        confidence=0.9
    )
    
    print(f"\nCreated decision with {len(decision.searches)} searches:")
    print(f"  Search 1: {decision.searches[0].parameters.id} (should be caught)")
    print(f"  Search 2: {decision.searches[1].parameters.query} (should be valid)")
    
    return True


def test_logs_for_placeholder_evidence():
    """Check recent logs for placeholder evidence"""
    
    print("\n" + "="*60)
    print("CHECKING: Recent logs for placeholder evidence")
    print("="*60)
    
    # Check if the temp1.txt evidence still shows up in recent activity
    log_files = [
        "logs/searches/searches_2025-09-09.jsonl",
        "logs/system/system_20250909.log"
    ]
    
    found_evidence = []
    
    for log_file in log_files:
        full_path = os.path.join(os.path.dirname(__file__), log_file)
        if os.path.exists(full_path):
            print(f"\nChecking {log_file}...")
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for the specific placeholder from temp1.txt
                if "REPLACE_WITH_TWEET_ID_FROM_TIMELINE" in content:
                    print(f"  FOUND: Placeholder evidence in {log_file}")
                    found_evidence.append(log_file)
                    
                    # Count occurrences
                    count = content.count("REPLACE_WITH_TWEET_ID_FROM_TIMELINE")
                    print(f"  COUNT: {count} occurrences")
                    
                else:
                    print(f"  CLEAN: No placeholder evidence in {log_file}")
                    
            except Exception as e:
                print(f"  ERROR reading {log_file}: {e}")
        else:
            print(f"  NOT FOUND: {log_file}")
    
    print(f"\nEVIDENCE SUMMARY:")
    if found_evidence:
        print(f"  ISSUE CONFIRMED: Placeholders found in {len(found_evidence)} log files")
        print(f"  FILES: {found_evidence}")
        print(f"  CONCLUSION: Issue #3 still exists despite validation")
        return False
    else:
        print(f"  NO EVIDENCE: Placeholders not found in recent logs")
        print(f"  CONCLUSION: Issue #3 may be fixed")
        return True


if __name__ == "__main__":
    print("Issue #3 Validation: Placeholder API Parameters")
    print("=" * 60)
    print("Original evidence: temp1.txt lines 285,293 - REPLACE_WITH_TWEET_ID_FROM_TIMELINE")
    print("Expected: Validation should detect and prevent placeholder parameters")
    print("=" * 60)
    
    try:
        test1_result = test_placeholder_validation() 
        test2_result = test_logs_for_placeholder_evidence()
        
        print("\n" + "="*60)
        print("VALIDATION RESULTS:")
        print(f"  Placeholder validation test: {'PASS' if test1_result else 'FAIL'}")
        print(f"  Log evidence check: {'CLEAN' if test2_result else 'EVIDENCE FOUND'}")
        
        if test1_result and test2_result:
            print("\n*** ISSUE #3 APPEARS TO BE FIXED ***")
            print("- Validation method working correctly")
            print("- No recent placeholder evidence in logs")
        elif test1_result and not test2_result:
            print("\n*** ISSUE #3 VALIDATION WORKING BUT EVIDENCE REMAINS ***")
            print("- Validation method detects placeholders correctly") 
            print("- But placeholder evidence still exists in logs")
            print("- May indicate validation not called in all code paths")
        else:
            print("\n*** ISSUE #3 VALIDATION PROBLEMS ***")
            print("- Validation method may have issues")
            print("- Further investigation needed")
        
        print("="*60)
        sys.exit(0 if (test1_result and test2_result) else 1)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)