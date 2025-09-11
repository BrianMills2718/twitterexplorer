#!/usr/bin/env python3
"""
Simple Issue #3 test: Check if placeholder validation is working
Phase 1: Issue #3 - Placeholder API Parameters
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
from investigation_graph import InvestigationGraph
from llm_client import get_litellm_client
from llm_model_manager import LLMModelManager


def test_issue3_status():
    """Simple test to check Issue #3 status"""
    
    print("TESTING: Issue #3 - Placeholder API Parameters")
    print("-" * 55)
    print("Original evidence: temp1.txt lines 285,293")
    print("Problem: 'REPLACE_WITH_TWEET_ID_FROM_TIMELINE' in API calls")
    print("-" * 55)
    
    # Test validation method
    print("\nStep 1: Testing placeholder validation...")
    
    llm_client = get_litellm_client()
    graph = InvestigationGraph()
    model_manager = LLMModelManager()
    
    coordinator = GraphAwareLLMCoordinator(llm_client, graph, model_manager)
    
    # Test the exact case from temp1.txt evidence
    problematic_params = {"id": "REPLACE_WITH_TWEET_ID_FROM_TIMELINE"}
    
    print(f"Testing parameters: {problematic_params}")
    
    try:
        errors = coordinator._validate_no_placeholders(problematic_params)
        
        if errors:
            print(f"VALIDATION RESULT: DETECTED {len(errors)} errors")
            for error in errors:
                print(f"  - {error}")
            print("CONCLUSION: Validation working - would prevent API call")
        else:
            print("VALIDATION RESULT: NO ERRORS DETECTED")  
            print("CONCLUSION: Validation not working - would allow bad API call")
        
        return len(errors) > 0
        
    except Exception as e:
        print(f"ERROR in validation test: {e}")
        return False


def check_recent_evidence():
    """Check if recent activity shows placeholder evidence"""
    
    print("\nStep 2: Checking for recent placeholder evidence...")
    
    # Look for recent graph files with placeholders
    graph_files = []
    try:
        for filename in os.listdir(os.path.dirname(__file__)):
            if filename.startswith("investigation_graph_") and filename.endswith(".json"):
                graph_files.append(filename)
    except Exception as e:
        print(f"Error reading directory: {e}")
    
    print(f"Found {len(graph_files)} graph files")
    
    # Check recent graph files for placeholder evidence
    evidence_count = 0
    files_with_evidence = []
    
    for graph_file in sorted(graph_files)[-3:]:  # Check last 3 files
        try:
            with open(graph_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "REPLACE_WITH_TWEET_ID_FROM_TIMELINE" in content:
                count = content.count("REPLACE_WITH_TWEET_ID_FROM_TIMELINE")
                print(f"  EVIDENCE: {graph_file} contains {count} placeholders")
                evidence_count += count
                files_with_evidence.append(graph_file)
            else:
                print(f"  CLEAN: {graph_file} contains no placeholders")
                
        except Exception as e:
            print(f"  ERROR reading {graph_file}: {e}")
    
    print(f"\nEVIDENCE SUMMARY:")
    print(f"  Total placeholders found: {evidence_count}")
    print(f"  Files with evidence: {len(files_with_evidence)}")
    
    if evidence_count > 0:
        print("CONCLUSION: Issue #3 still occurring in recent activity")
        return False
    else:
        print("CONCLUSION: No recent evidence of Issue #3")
        return True


if __name__ == "__main__":
    print("Issue #3 Status Check: Placeholder API Parameters")
    print("=" * 55)
    
    try:
        validation_works = test_issue3_status()
        no_recent_evidence = check_recent_evidence()
        
        print("\n" + "=" * 55)
        print("ISSUE #3 STATUS ASSESSMENT:")
        print(f"  Validation method works: {'YES' if validation_works else 'NO'}")
        print(f"  Recent evidence clean: {'YES' if no_recent_evidence else 'NO'}")
        
        if validation_works and no_recent_evidence:
            print("\n*** ISSUE #3 STATUS: FIXED ***")
            print("- Validation detects placeholders correctly")
            print("- No recent evidence of placeholder API calls")
            print("- Original temp1.txt evidence likely from before fix")
        elif validation_works and not no_recent_evidence:
            print("\n*** ISSUE #3 STATUS: VALIDATION WORKING BUT STILL OCCURRING ***")
            print("- Validation method works correctly")
            print("- But placeholders still appearing in recent graph files")
            print("- May indicate validation not called in all execution paths")
        elif not validation_works:
            print("\n*** ISSUE #3 STATUS: VALIDATION BROKEN ***")
            print("- Validation method not detecting placeholders")
            print("- Needs debugging and fixing")
        else:
            print("\n*** ISSUE #3 STATUS: UNCLEAR ***")
            print("- Mixed results require further investigation")
        
        print("=" * 55)
        
        overall_fixed = validation_works and no_recent_evidence
        sys.exit(0 if overall_fixed else 1)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)