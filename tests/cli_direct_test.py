#!/usr/bin/env python3

# Test without setting DISABLE_STREAMLIT first
print("Testing import without DISABLE_STREAMLIT...")

import sys
import os

# Run with fresh Python process to avoid cached imports
import subprocess

# Test the actual CLI script
result = subprocess.run([
    sys.executable, 'cli_test.py', 'simple test query', '--max-searches', '1'
], capture_output=True, text=True, cwd='.')

print("RETURN CODE:", result.returncode)
print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)

# Look specifically for the Streamlit app warning
if "streamlit run cli_test.py" in result.stderr or "streamlit run cli_test.py" in result.stdout:
    print("\n❌ ISSUE STILL EXISTS: Streamlit app warning detected")
else:
    print("\n✅ ISSUE RESOLVED: No Streamlit app warnings found")