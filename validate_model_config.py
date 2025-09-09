#!/usr/bin/env python3
"""
Model configuration validation tool for TwitterExplorer
"""

import sys
import os
sys.path.append('twitterexplorer')

from llm_model_manager import LLMModelManager
from llm_client import get_litellm_client
import argparse

def validate_config(config_path=None):
    """Validate model configuration and test API connectivity"""
    
    try:
        # Initialize model manager
        manager = LLMModelManager(config_path)
        print("[OK] Model configuration loaded successfully")
        
        # Show configuration summary
        summary = manager.get_current_config_summary()
        print(f"\nConfiguration Summary:")
        print(f"   Source: {summary['config_source']}")
        print(f"   Default Provider: {summary['default_provider']}")
        print(f"   Providers Used: {summary['provider_count']}")
        
        print(f"\nModel Assignments:")
        for operation, model in summary['operations'].items():
            print(f"   {operation}: {model}")
        
        # Test API connectivity for each provider
        print(f"\nAPI Connectivity Tests:")
        
        # Get unique models to test
        unique_models = list(set(summary['operations'].values()))
        
        llm_client = get_litellm_client()
        
        for model in unique_models:
            try:
                # Simple test call
                response = llm_client.completion(
                    model=model,
                    messages=[{"role": "user", "content": "Hello"}]
                )
                if response and response.choices:
                    print(f"   [OK] {model} - Available")
                else:
                    print(f"   [WARN] {model} - Unexpected response format")
            except Exception as e:
                print(f"   [ERROR] {model} - Error: {str(e)}")
        
        print(f"\n[OK] Validation complete")
        return True
        
    except Exception as e:
        print(f"[ERROR] Configuration validation failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate TwitterExplorer model configuration')
    parser.add_argument('--config', help='Path to custom configuration file')
    
    args = parser.parse_args()
    
    success = validate_config(args.config)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()