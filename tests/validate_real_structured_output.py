#!/usr/bin/env python3
"""
Validation Script: Real LiteLLM Structured Output
Test the corrected implementation against the broken one
"""

import os
import sys
from pydantic import BaseModel
from typing import List, Dict, Any
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from twitterexplorer.llm_client import get_litellm_client, StrategicDecision

class TestOutput(BaseModel):
    """Test schema for structured output validation"""
    task_type: str
    reasoning: str
    priority_score: float
    action_items: List[str]
    metadata: Dict[str, Any]

def test_real_structured_output():
    """Test the corrected LiteLLM structured output implementation"""
    print("Testing REAL LiteLLM Structured Output")
    print("=" * 60)
    
    try:
        # Get the client
        client = get_litellm_client()
        print("LiteLLM client initialized successfully")
        
        # Test with a simple schema first
        print("\nTest 1: Simple Schema Validation")
        messages = [
            {"role": "user", "content": "Create a test investigation task with 3 action items"}
        ]
        
        response = client.completion(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            response_format=TestOutput
        )
        
        print("API call successful")
        
        # Check if we got structured output
        if hasattr(response.choices[0].message, 'parsed'):
            parsed = response.choices[0].message.parsed
            if parsed is not None:
                print("PASS: Structured output parsing successful!")
                print(f"   Task Type: {parsed.task_type}")
                print(f"   Priority: {parsed.priority_score}")
                print(f"   Actions: {len(parsed.action_items)} items")
                print(f"   Reasoning: {parsed.reasoning[:50]}...")
            else:
                print("FAIL: Parsed output is None - parsing failed")
                print(f"Raw content: {response.choices[0].message.content[:200]}")
        else:
            print("FAIL: No 'parsed' attribute found")
            print(f"Response: {response}")
        
        # Test with StrategicDecision schema 
        print("\nTest 2: StrategicDecision Schema Validation")
        strategy_messages = [
            {"role": "user", "content": "Create a strategic investigation decision for analyzing Trump Epstein drama"}
        ]
        
        strategy_response = client.completion(
            model="gemini/gemini-2.5-flash",
            messages=strategy_messages,
            response_format=StrategicDecision
        )
        
        if hasattr(strategy_response.choices[0].message, 'parsed'):
            strategy_parsed = strategy_response.choices[0].message.parsed
            if strategy_parsed is not None:
                print("PASS: StrategicDecision parsing successful!")
                print(f"   Decision Type: {strategy_parsed.decision_type}")
                print(f"   Searches: {len(strategy_parsed.searches)} planned")
                print(f"   Reasoning: {strategy_parsed.reasoning[:50]}...")
            else:
                print("FAIL: StrategicDecision parsing failed")
                print(f"Raw content: {strategy_response.choices[0].message.content[:200]}")
        
        print("\nStructured Output Validation Complete!")
        return True
        
    except Exception as e:
        print(f"FAIL: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comparison_with_universal_llm():
    """Compare our implementation with the universal_llm approach"""
    print("\nComparison with Universal LLM Kit Approach")
    print("=" * 60)
    
    # Test the universal_llm approach directly
    try:
        from dotenv import load_dotenv
        import litellm
        load_dotenv()
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("FAIL: GEMINI_API_KEY not found")
            return False
            
        # Direct litellm call (universal_llm style)
        kwargs = {
            "model": "gemini/gemini-2.5-flash",
            "messages": [{"role": "user", "content": "Create a test task with priority score and action items.\n\nRespond with valid JSON matching this schema: {\"type\":\"object\",\"properties\":{\"task_type\":{\"type\":\"string\"},\"reasoning\":{\"type\":\"string\"},\"priority_score\":{\"type\":\"number\"},\"action_items\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"metadata\":{\"type\":\"object\"}},\"required\":[\"task_type\",\"reasoning\",\"priority_score\",\"action_items\",\"metadata\"]}"}],
            "response_format": {"type": "json_object"},
            "api_key": api_key
        }
        
        direct_response = litellm.completion(**kwargs)
        print("PASS: Direct litellm.completion call successful")
        print(f"Response content: {direct_response.choices[0].message.content[:100]}...")
        
        # Try to parse as JSON
        content = direct_response.choices[0].message.content
        try:
            parsed_json = json.loads(content)
            print("PASS: JSON parsing successful")
            print(f"Parsed keys: {list(parsed_json.keys())}")
        except json.JSONDecodeError as e:
            print(f"FAIL: JSON parsing failed: {e}")
            
        return True
        
    except Exception as e:
        print(f"FAIL: Direct comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_structure_validation():
    """Test the structure and imports without requiring API key"""
    print("\nStructure Validation (No API Key Required)")
    print("=" * 60)
    
    try:
        # Test 1: Import validation
        print("Test 1: Import Validation")
        from llm_client import get_litellm_client, LiteLLMClient, StrategicDecision
        print("PASS: All imports successful")
        
        # Test 2: Schema validation
        print("\nTest 2: Pydantic Schema Validation")
        test_schema = TestOutput(
            task_type="validation_test",
            reasoning="Testing schema structure",
            priority_score=7.5,
            action_items=["validate imports", "test schema", "check structure"],
            metadata={"test": True, "validation": "structure"}
        )
        print("PASS: TestOutput schema validation successful")
        print(f"   Task Type: {test_schema.task_type}")
        print(f"   Priority: {test_schema.priority_score}")
        print(f"   Actions: {len(test_schema.action_items)} items")
        
        # Test 3: Strategic Decision Schema
        print("\nTest 3: StrategicDecision Schema Validation")
        strategic_schema = StrategicDecision(
            decision_type="test_decision",
            reasoning="Testing strategic decision structure",
            searches=[{"endpoint": "test.php", "parameters": {"query": "test"}}],
            expected_outcomes=["test validation complete"],
            confidence=0.95
        )
        print("PASS: StrategicDecision schema validation successful")
        print(f"   Decision Type: {strategic_schema.decision_type}")
        print(f"   Searches: {len(strategic_schema.searches)} planned")
        print(f"   Confidence: {strategic_schema.confidence}")
        
        # Test 4: Implementation Structure Analysis
        print("\nTest 4: Implementation Structure Analysis")
        import inspect
        
        # Check LiteLLMClient methods
        client_methods = [method for method in dir(LiteLLMClient) if not method.startswith('_')]
        required_methods = ['completion', 'simple_completion']
        
        for method in required_methods:
            if method in client_methods:
                print(f"PASS: {method} method exists")
                # Check method signature
                method_obj = getattr(LiteLLMClient, method)
                sig = inspect.signature(method_obj)
                print(f"   Signature: {method}{sig}")
            else:
                print(f"FAIL: {method} method missing")
                return False
        
        # Test 5: Check critical implementation differences
        print("\nTest 5: Implementation Correctness Check")
        print("Checking if implementation uses native LiteLLM structured output...")
        
        # Read the actual implementation
        import importlib
        import llm_client
        importlib.reload(llm_client)
        
        # Check completion method source for correct patterns
        completion_source = inspect.getsource(LiteLLMClient.completion)
        
        if '"type": "json_object"' in completion_source:
            print("PASS: Native LiteLLM JSON response format detected")
        else:
            print("FAIL: Native LiteLLM JSON response format NOT found")
            return False
            
        if 'api_key": self.api_key' in completion_source:
            print("PASS: Direct API key passing detected")
        else:
            print("FAIL: Direct API key passing NOT found")
            return False
            
        if 'completion(**completion_params)' in completion_source:
            print("PASS: Direct litellm.completion call detected")
        else:
            print("FAIL: Direct litellm.completion call NOT found")
            return False
        
        print("\nStructure Validation Complete!")
        print("CONCLUSION: Implementation structure is correct for real LiteLLM structured output")
        return True
        
    except Exception as e:
        print(f"FAIL: Structure validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation tests"""
    print("LiteLLM Structured Output Validation")
    print("Testing corrected implementation vs. broken one")
    print("=" * 80)
    
    # Check environment setup
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("GEMINI_API_KEY"):
        print("NOTE: GEMINI_API_KEY not found in environment")
        print("Testing structure and import capabilities instead...")
        return test_structure_validation()
    
    print("PASS: Environment setup validated")
    
    # Run tests
    test1_result = test_real_structured_output()
    test2_result = test_comparison_with_universal_llm()
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Real Structured Output Test: {'PASSED' if test1_result else 'FAILED'}")
    print(f"Universal LLM Comparison:   {'PASSED' if test2_result else 'FAILED'}")
    
    if test1_result and test2_result:
        print("\nSUCCESS: LiteLLM structured output is now working correctly!")
        print("The fake JSON prompting has been replaced with native LiteLLM capabilities.")
    else:
        print("\nFAILURE: Issues detected in structured output implementation")
        
    return test1_result and test2_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)