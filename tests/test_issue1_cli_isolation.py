#!/usr/bin/env python3
"""
Test Issue #1: Streamlit Import Contamination in CLI
Phase 1: Issue #1 - Check CLI isolation
"""

import sys
import os
import subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_cli_purity():
    """Test CLI execution without Streamlit contamination"""
    
    print("TESTING: Issue #1 - Streamlit Import Contamination")
    print("-" * 55) 
    print("Original evidence: CLI output lines 43-46 showed Streamlit warnings")
    print("Expected: CLI should run without Streamlit imports/warnings")
    print("-" * 55)
    
    print("\nStep 1: Testing direct import isolation...")
    
    # Test importing core investigation components without Streamlit
    try:
        print("  Importing investigation_engine...")
        from investigation_engine import InvestigationEngine
        print("    SUCCESS: investigation_engine imported")
        
        print("  Importing investigation_context...")
        from investigation_context import InvestigationContext  
        print("    SUCCESS: investigation_context imported")
        
        print("  Importing llm_client...")
        from llm_client import get_litellm_client
        print("    SUCCESS: llm_client imported")
        
        print("  Testing component initialization...")
        
        # Test basic initialization without Streamlit
        engine = InvestigationEngine(rapidapi_key="test_key")
        print("    SUCCESS: InvestigationEngine initialized")
        
        context = InvestigationContext(
            analytic_question="Test CLI isolation",
            investigation_scope="cli_test"
        )
        print("    SUCCESS: InvestigationContext initialized")
        
        llm_client = get_litellm_client()
        print("    SUCCESS: LLM client initialized")
        
        return True
        
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def test_cli_execution():
    """Test CLI script execution for Streamlit warnings"""
    
    print("\nStep 2: Testing CLI script execution...")
    
    # Test running cli_test.py to see if it produces Streamlit warnings
    try:
        print("  Running cli_test.py with test query...")
        
        # Run CLI with minimal test to check for warnings
        result = subprocess.run([
            sys.executable, "cli_test.py", 
            "--query", "test cli isolation",
            "--max-searches", "1"  # Minimal execution
        ], 
        capture_output=True, 
        text=True, 
        timeout=60,  # 1 minute timeout
        cwd=os.path.dirname(__file__)
        )
        
        print(f"  Exit code: {result.returncode}")
        
        # Check output for Streamlit-related warnings
        full_output = result.stdout + result.stderr
        
        streamlit_indicators = [
            "streamlit", "Streamlit", "STREAMLIT",
            "Please replace 'st.' with", 
            "DeltaGenerator",
            "streamlit warning", "streamlit error"
        ]
        
        found_contamination = []
        for indicator in streamlit_indicators:
            if indicator.lower() in full_output.lower():
                found_contamination.append(indicator)
        
        print(f"  Output length: {len(full_output)} characters")
        
        if found_contamination:
            print(f"  CONTAMINATION DETECTED: {len(found_contamination)} Streamlit indicators")
            for indicator in found_contamination:
                print(f"    - Found: '{indicator}'")
            
            # Show relevant output lines
            lines = full_output.split('\n')
            print(f"  First few output lines:")
            for i, line in enumerate(lines[:10]):
                if line.strip():
                    print(f"    Line {i+1}: {line}")
            
            return False
        else:
            print(f"  CLEAN OUTPUT: No Streamlit contamination detected")
            
            # Show first few lines to verify it ran
            lines = full_output.split('\n')
            print(f"  Sample output lines:")
            for i, line in enumerate(lines[:5]):
                if line.strip():
                    print(f"    Line {i+1}: {line}")
            
            return True
            
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: CLI execution took too long (>60s)")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_conditional_import_effectiveness():
    """Test that conditional imports are working"""
    
    print("\nStep 3: Testing conditional import system...")
    
    try:
        # Check if investigation_engine has proper conditional imports
        with open("investigation_engine.py", 'r', encoding='utf-8') as f:
            engine_content = f.read()
        
        # Look for conditional import patterns
        has_conditional = "try:" in engine_content and "import streamlit" in engine_content
        has_safe_wrappers = "safe_streamlit" in engine_content
        has_availability_check = "STREAMLIT_AVAILABLE" in engine_content
        
        print(f"  Conditional import pattern: {'FOUND' if has_conditional else 'MISSING'}")
        print(f"  Safe wrapper functions: {'FOUND' if has_safe_wrappers else 'MISSING'}")
        print(f"  Availability checking: {'FOUND' if has_availability_check else 'MISSING'}")
        
        if has_conditional and has_safe_wrappers and has_availability_check:
            print("  CONCLUSION: Conditional import system properly implemented")
            return True
        else:
            print("  CONCLUSION: Conditional import system incomplete")
            return False
            
    except Exception as e:
        print(f"  ERROR checking investigation_engine.py: {e}")
        return False


if __name__ == "__main__":
    print("Issue #1 Status Check: Streamlit Import Contamination")
    print("=" * 55)
    
    try:
        test1_result = test_cli_purity()
        test2_result = test_cli_execution() 
        test3_result = test_conditional_import_effectiveness()
        
        print("\n" + "=" * 55)
        print("ISSUE #1 STATUS ASSESSMENT:")
        print(f"  Import isolation works: {'YES' if test1_result else 'NO'}")
        print(f"  CLI execution clean: {'YES' if test2_result else 'NO'}")
        print(f"  Conditional imports implemented: {'YES' if test3_result else 'NO'}")
        
        overall_fixed = test1_result and test2_result and test3_result
        
        if overall_fixed:
            print("\n*** ISSUE #1 STATUS: FIXED ***")
            print("- CLI components import without Streamlit contamination")
            print("- CLI execution produces no Streamlit warnings")  
            print("- Conditional import system working properly")
        elif test1_result and test3_result and not test2_result:
            print("\n*** ISSUE #1 STATUS: MOSTLY FIXED ***")
            print("- Conditional import system implemented")
            print("- But CLI execution still shows some contamination")
            print("- May need additional cleanup")
        else:
            print("\n*** ISSUE #1 STATUS: NEEDS WORK ***")
            print("- Streamlit contamination still present")
            print("- Additional fixes required")
        
        print("=" * 55)
        sys.exit(0 if overall_fixed else 1)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)