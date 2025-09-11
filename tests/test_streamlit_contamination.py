#!/usr/bin/env python3
"""
Test Streamlit import contamination - Issue #1
Test both with and without DISABLE_STREAMLIT environment variable
"""

import subprocess
import sys
import os

def test_cli_without_disable_flag():
    """Test CLI execution without DISABLE_STREAMLIT flag"""
    print("Testing CLI without DISABLE_STREAMLIT flag...")
    
    # Create a temporary test script without the DISABLE_STREAMLIT setting
    test_script = '''
import sys
import os
# Don't set DISABLE_STREAMLIT

sys.path.append('.')
try:
    from investigation_engine import InvestigationEngine
    print("SUCCESS: investigation_engine imported without DISABLE_STREAMLIT")
except Exception as e:
    print(f"ERROR: {e}")
'''
    
    with open('temp_test_no_disable.py', 'w') as f:
        f.write(test_script)
    
    try:
        result = subprocess.run([sys.executable, 'temp_test_no_disable.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        # Look for Streamlit warnings
        streamlit_warnings = []
        if "streamlit" in result.stderr.lower():
            streamlit_warnings.append("Streamlit warning in stderr")
        if "streamlit" in result.stdout.lower():
            streamlit_warnings.append("Streamlit reference in stdout")
            
        return streamlit_warnings
        
    finally:
        if os.path.exists('temp_test_no_disable.py'):
            os.remove('temp_test_no_disable.py')

def test_cli_with_disable_flag():
    """Test CLI execution with DISABLE_STREAMLIT flag"""
    print("\nTesting CLI with DISABLE_STREAMLIT flag...")
    
    test_script = '''
import sys
import os
os.environ['DISABLE_STREAMLIT'] = '1'

sys.path.append('.')
try:
    from investigation_engine import InvestigationEngine
    print("SUCCESS: investigation_engine imported with DISABLE_STREAMLIT=1")
except Exception as e:
    print(f"ERROR: {e}")
'''
    
    with open('temp_test_with_disable.py', 'w') as f:
        f.write(test_script)
    
    try:
        result = subprocess.run([sys.executable, 'temp_test_with_disable.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        # Look for Streamlit warnings
        streamlit_warnings = []
        if "streamlit" in result.stderr.lower():
            streamlit_warnings.append("Streamlit warning in stderr")
        if "streamlit" in result.stdout.lower():
            streamlit_warnings.append("Streamlit reference in stdout")
            
        return streamlit_warnings
        
    finally:
        if os.path.exists('temp_test_with_disable.py'):
            os.remove('temp_test_with_disable.py')

def test_temp1_original_evidence():
    """Check if original evidence from temp1.txt lines 43-46 still exists"""
    print("\nChecking original evidence from temp1.txt...")
    
    temp1_path = '../temp1.txt'  # One level up from twitterexplorer/
    if os.path.exists(temp1_path):
        with open(temp1_path, 'r') as f:
            lines = f.readlines()
        
        # Check lines around 43-46 for Streamlit warnings
        relevant_lines = []
        for i, line in enumerate(lines[40:50], 41):  # Lines 41-50
            if "streamlit" in line.lower():
                relevant_lines.append(f"Line {i}: {line.strip()}")
        
        print(f"Streamlit references in temp1.txt lines 41-50: {relevant_lines}")
        return relevant_lines
    else:
        print("temp1.txt not found at ../temp1.txt")
        return []

if __name__ == "__main__":
    print("=== STREAMLIT IMPORT CONTAMINATION TEST ===")
    
    # Test without disable flag
    warnings_without = test_cli_without_disable_flag()
    print(f"Streamlit warnings without DISABLE_STREAMLIT: {warnings_without}")
    
    # Test with disable flag  
    warnings_with = test_cli_with_disable_flag()
    print(f"Streamlit warnings with DISABLE_STREAMLIT: {warnings_with}")
    
    # Check original evidence
    original_evidence = test_temp1_original_evidence()
    
    print("\n=== RESULTS ===")
    if warnings_without and not warnings_with:
        print("✅ FIXED: DISABLE_STREAMLIT flag prevents Streamlit warnings")
    elif warnings_without and warnings_with:
        print("❌ NOT FIXED: DISABLE_STREAMLIT flag doesn't prevent warnings")
    elif not warnings_without and not warnings_with:
        print("? UNCLEAR: No Streamlit warnings detected in either case")
    else:
        print("? UNEXPECTED: Warnings only with DISABLE_STREAMLIT flag")
    
    if original_evidence:
        print("📍 ORIGINAL EVIDENCE: Still contains Streamlit references in temp1.txt")
    else:
        print("✅ ORIGINAL EVIDENCE: No Streamlit references found in expected location")