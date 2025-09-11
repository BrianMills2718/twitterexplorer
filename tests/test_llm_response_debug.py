"""Debug the exact LLM response format that's causing the parsing issue"""
import sys
import os
import json

from finding_evaluator_llm import LLMFindingEvaluator

def test_llm_response_debug():
    """EVIDENCE: Check what the LLM is actually returning"""
    
    print("=== LLM RESPONSE DEBUG ===")
    
    # Create evaluator
    evaluator = LLMFindingEvaluator()
    
    # Sample data
    test_results = [
        {'text': 'Promoted by The Long Walk', 'source': 'trends.php'},
        {'text': '590K posts', 'source': 'trends.php'},
        {'text': 'Onana', 'source': 'trends.php'}
    ]
    
    query = "Test query"
    
    # Patch the LLM call to capture response
    original_completion = evaluator.llm_client.completion
    captured_response = {}
    
    def debug_completion(*args, **kwargs):
        result = original_completion(*args, **kwargs)
        captured_response['raw_content'] = result.choices[0].message.content
        return result
    
    evaluator.llm_client.completion = debug_completion
    
    try:
        # Try evaluation
        assessments = evaluator.evaluate_batch(test_results, query)
        print(f"Success: Got {len(assessments)} assessments")
    except Exception as e:
        print(f"Error: {e}")
        
        # Show what we captured
        if 'raw_content' in captured_response:
            raw_content = captured_response['raw_content']
            print(f"\nRAW LLM RESPONSE:")
            print(f"Length: {len(raw_content)}")
            print(f"Content preview: {raw_content[:500]}...")
            
            # Try parsing manually
            content = raw_content.strip()
            if content.startswith('```') and content.endswith('```'):
                content = content[3:-3]
            if content.startswith('json'):
                content = content[4:]
            
            print(f"\nCLEANED CONTENT:")
            print(content[:500])
            
            try:
                parsed = json.loads(content.strip())
                print(f"\nPARSED TYPE: {type(parsed)}")
                if isinstance(parsed, list):
                    print(f"LIST LENGTH: {len(parsed)}")
                    print(f"FIRST ITEM: {parsed[0] if parsed else 'EMPTY'}")
                elif isinstance(parsed, dict):
                    print(f"DICT KEYS: {list(parsed.keys())}")
            except Exception as parse_e:
                print(f"\nPARSE ERROR: {parse_e}")

if __name__ == "__main__":
    test_llm_response_debug()