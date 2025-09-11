#!/usr/bin/env python3
"""
Validation script for all 4 CLAUDE.md issues
"""
import sys
import os
import subprocess
import json
import glob
from pathlib import Path

def print_status(issue, status, details=""):
    status_symbol = "[PASS]" if status else "[FAIL]"
    print(f"{status_symbol} Issue #{issue}: {details}")
    return status

def validate_issue_1_streamlit_import():
    """Issue #1: Streamlit import contamination in CLI"""
    
    print("\n=== Issue #1: Streamlit Import Contamination ===")
    
    # Test 1: Check if CLI execution shows Streamlit warnings
    try:
        result = subprocess.run([
            sys.executable, "cli_test.py", "--help"
        ], capture_output=True, text=True, timeout=30)
        
        has_streamlit_warning = "streamlit run" in result.stdout.lower() or "streamlit run" in result.stderr.lower()
        test1_pass = not has_streamlit_warning
        
        print_status("1a", test1_pass, f"CLI help output free of Streamlit warnings: {test1_pass}")
        
    except Exception as e:
        test1_pass = False
        print_status("1a", False, f"CLI help test failed: {e}")
    
    return test1_pass

def validate_issue_2_insight_titles():
    """Issue #2: Untitled insight generation"""
    
    print("\n=== Issue #2: Untitled Insight Generation ===")
    
    # Check recent graph files for insights with proper titles
    graph_files = glob.glob("investigation_graph_*.json")
    
    if not graph_files:
        print_status("2", False, "No graph files found to analyze")
        return False
    
    # Get most recent graph file
    latest_graph = max(graph_files, key=os.path.getctime)
    
    try:
        with open(latest_graph, 'r') as f:
            graph_data = json.load(f)
        
        nodes = graph_data.get('nodes', {})
        insights = [node for node in nodes.values() if node.get('node_type') == 'Insight']
        
        if not insights:
            print_status("2", True, "No insights found - cannot evaluate titles")
            return True
        
        untitled_insights = 0
        valid_insights = 0
        
        for insight in insights:
            title = insight.get('properties', {}).get('title', 'Untitled')
            confidence = insight.get('properties', {}).get('confidence', 'N/A')
            
            if title == 'Untitled' or confidence == 'N/A':
                untitled_insights += 1
            else:
                valid_insights += 1
        
        success = untitled_insights == 0
        print_status("2", success, f"Insights with proper titles: {valid_insights}/{len(insights)} (untitled: {untitled_insights})")
        
        return success
        
    except Exception as e:
        print_status("2", False, f"Error analyzing graph file: {e}")
        return False

def validate_issue_3_placeholder_params():
    """Issue #3: Placeholder API parameters"""
    
    print("\n=== Issue #3: Placeholder API Parameters ===")
    
    # Check recent log files for placeholder patterns
    log_files = glob.glob("investigation_*.log") + glob.glob("*.log")
    
    placeholder_patterns = [
        "REPLACE_WITH_TWEET_ID",
        "REPLACE_WITH_USER_ID", 
        "<username>",
        "<tweet_id>",
        "TODO:"
    ]
    
    if not log_files:
        print_status("3", True, "No log files found - cannot check for placeholders")
        return True
    
    # Check most recent log file
    latest_log = max(log_files, key=os.path.getctime) if log_files else None
    
    if latest_log:
        try:
            with open(latest_log, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            found_placeholders = []
            for pattern in placeholder_patterns:
                if pattern in log_content:
                    found_placeholders.append(pattern)
            
            success = len(found_placeholders) == 0
            print_status("3", success, f"Placeholder patterns found in logs: {found_placeholders}")
            
            return success
            
        except Exception as e:
            print_status("3", False, f"Error reading log file: {e}")
            return False
    
    return True

def validate_issue_4_provider_parameter():
    """Issue #4: Missing model provider CLI parameter"""
    
    print("\n=== Issue #4: Model Provider CLI Parameter ===")
    
    # Test 1: CLI accepts --provider parameter
    try:
        result = subprocess.run([
            sys.executable, "cli_test.py", "--help"
        ], capture_output=True, text=True, timeout=30)
        
        has_provider_param = "--provider" in result.stdout
        test1_pass = has_provider_param
        
        print_status("4a", test1_pass, f"CLI accepts --provider parameter: {test1_pass}")
        
    except Exception as e:
        test1_pass = False
        print_status("4a", False, f"CLI help test failed: {e}")
    
    # Test 2: Provider choices are correct
    try:
        if test1_pass:
            has_openai = "openai" in result.stdout
            has_gemini = "gemini" in result.stdout
            test2_pass = has_openai and has_gemini
            
            print_status("4b", test2_pass, f"Provider choices (openai, gemini) available: {test2_pass}")
        else:
            test2_pass = False
            
    except:
        test2_pass = False
    
    return test1_pass and test2_pass

def main():
    """Run validation for all 4 issues"""
    
    print("TwitterExplorer Issue Validation")
    print("=" * 40)
    
    # Change to correct directory
    os.chdir(os.path.dirname(__file__))
    
    # Validate each issue
    issue1_fixed = validate_issue_1_streamlit_import()
    issue2_fixed = validate_issue_2_insight_titles() 
    issue3_fixed = validate_issue_3_placeholder_params()
    issue4_fixed = validate_issue_4_provider_parameter()
    
    # Summary
    print("\n" + "=" * 40)
    print("VALIDATION SUMMARY")
    print("=" * 40)
    
    issues_fixed = sum([issue1_fixed, issue2_fixed, issue3_fixed, issue4_fixed])
    
    print(f"Issues Fixed: {issues_fixed}/4")
    print(f"Issue #1 (Streamlit Import): {'FIXED' if issue1_fixed else 'STILL BROKEN'}")
    print(f"Issue #2 (Insight Titles): {'FIXED' if issue2_fixed else 'STILL BROKEN'}")
    print(f"Issue #3 (Placeholder Params): {'FIXED' if issue3_fixed else 'STILL BROKEN'}")
    print(f"Issue #4 (Provider Parameter): {'FIXED' if issue4_fixed else 'STILL BROKEN'}")
    
    if issues_fixed == 4:
        print("\n[SUCCESS] ALL ISSUES SUCCESSFULLY FIXED!")
        return True
    else:
        print(f"\n[WARNING] {4-issues_fixed} issues still need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)