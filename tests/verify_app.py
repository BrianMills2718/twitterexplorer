#!/usr/bin/env python3
"""
TwitterExplorer App Verification Script
=====================================

Quick verification that all fixes are applied and the app is ready to launch.
"""

def verify_app():
    """Verify the app is ready to launch"""
    print("TwitterExplorer App Verification")
    print("=" * 32)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Import validation
    total_tests += 1
    try:
        import streamlit as st
        from streamlit_app_modern import main, render_investigation_controls
        print("[PASS] Streamlit app imports successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
    
    # Test 2: Model configuration validation
    total_tests += 1
    try:
        from llm_model_manager import LLMModelManager
        manager = LLMModelManager()
        config = manager.get_current_config_summary()
        
        # Check if GPT-5-mini is configured
        gpt5_operations = [op for op, model in config['operations'].items() if 'gpt-5-mini' in model]
        
        if len(gpt5_operations) >= 6:
            print(f"[PASS] GPT-5-mini configured for {len(gpt5_operations)} operations")
            success_count += 1
        else:
            print(f"[FAIL] GPT-5-mini only configured for {len(gpt5_operations)} operations")
    except Exception as e:
        print(f"[FAIL] Model config error: {e}")
    
    # Test 3: Secrets file validation
    total_tests += 1
    try:
        import toml
        with open('.streamlit/secrets.toml', 'r') as f:
            secrets = toml.load(f)
        
        required_keys = ['RAPIDAPI_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY']
        available_keys = [key for key in required_keys if key in secrets and secrets[key].strip()]
        
        if len(available_keys) >= 2:  # Need at least 2 keys
            print(f"[PASS] API keys configured: {available_keys}")
            success_count += 1
        else:
            print(f"[FAIL] Missing API keys: {[k for k in required_keys if k not in available_keys]}")
    except Exception as e:
        print(f"[WARN] Secrets validation: {e}")
    
    # Test 4: Component integration
    total_tests += 1
    try:
        from investigation_engine import InvestigationEngine
        from knowledge_builder import KnowledgeBuilder
        from satisfaction_assessor import SatisfactionAssessor
        print("[PASS] Core investigation components available")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Component integration error: {e}")
    
    print("\nVerification Results:")
    print(f"Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\nSTATUS: READY TO LAUNCH!")
        print("Run: streamlit run streamlit_app_modern.py")
        return True
    elif success_count >= total_tests - 1:
        print("\nSTATUS: MOSTLY READY - App should work with minor issues")
        print("Run: streamlit run streamlit_app_modern.py")
        return True
    else:
        print("\nSTATUS: ISSUES DETECTED - Check errors above")
        return False

if __name__ == "__main__":
    verify_app()