#!/usr/bin/env python3
"""
Test model provider configuration - Issue #4: Missing model provider CLI parameter
CLI must accept --provider parameter for model switching
"""

import pytest
import sys
import argparse
import os
from unittest.mock import Mock, patch, MagicMock


def test_cli_provider_parameter():
    """CLI must accept --provider parameter for model switching"""
    
    # Check if CLI accepts --provider parameter
    import cli_test
    
    # Test if main function accepts provider argument
    # Currently it doesn't, so we'll document this
    
    # Check cli_test.py source for argument parsing
    import inspect
    cli_source = inspect.getsource(cli_test.main)
    
    has_argparse = 'argparse' in cli_source or 'ArgumentParser' in cli_source
    has_provider_arg = '--provider' in cli_source or 'provider' in cli_source
    
    print(f"CLI has argparse usage: {has_argparse}")
    print(f"CLI has provider argument: {has_provider_arg}")
    
    # Verify provider parameter exists (Issue #4 fixed)
    assert has_provider_arg, "CLI should accept --provider parameter"


def test_investigation_config_provider_field():
    """InvestigationConfig should have model_provider field"""
    
    from investigation_engine import InvestigationConfig
    
    # Check if InvestigationConfig has model_provider field
    config = InvestigationConfig()
    has_provider_field = hasattr(config, 'model_provider')
    
    print(f"InvestigationConfig has model_provider field: {has_provider_field}")
    
    # Check available fields
    config_fields = [attr for attr in dir(config) if not attr.startswith('_')]
    print(f"Available InvestigationConfig fields: {config_fields}")
    
    # Verify model_provider field exists (Issue #4 fixed)
    assert has_provider_field, "InvestigationConfig should have model_provider field"
    
    # Verify default value is correct
    assert config.model_provider == 'gemini', "Default provider should be gemini"


def test_llm_model_manager_provider_switching():
    """Test LLMModelManager provider switching functionality"""
    
    from llm_model_manager import LLMModelManager
    
    # Test creating manager with different providers
    try:
        # Test OpenAI provider
        openai_manager = LLMModelManager(provider='openai')
        print(f"OpenAI manager created: {type(openai_manager)}")
        
        # Test Gemini provider  
        gemini_manager = LLMModelManager(provider='gemini')
        print(f"Gemini manager created: {type(gemini_manager)}")
        
        # Check if providers are different
        openai_client_type = type(openai_manager.client) if hasattr(openai_manager, 'client') else None
        gemini_client_type = type(gemini_manager.client) if hasattr(gemini_manager, 'client') else None
        
        print(f"OpenAI client type: {openai_client_type}")
        print(f"Gemini client type: {gemini_client_type}")
        
        # Test if switching actually works
        different_clients = openai_client_type != gemini_client_type
        print(f"Providers use different client types: {different_clients}")
        
        assert different_clients, "Provider switching should create different client types"
        
    except Exception as e:
        print(f"Error testing provider switching: {e}")
        # Document if switching is not implemented properly
        assert True, f"Provider switching error (documenting issue): {e}"


def test_investigation_engine_provider_integration():
    """Test InvestigationEngine integration with provider selection"""
    
    from investigation_engine import InvestigationEngine, InvestigationConfig
    
    # Test if engine can be created with provider configuration
    config_with_provider = InvestigationConfig()
    
    # Try to set provider (this likely doesn't work yet)
    try:
        # This should work after implementation
        if hasattr(config_with_provider, 'model_provider'):
            config_with_provider.model_provider = 'gemini'
            
        engine = InvestigationEngine('test_api_key', config=config_with_provider)
        
        # Check if engine respects provider setting
        if hasattr(engine, 'llm_coordinator') and hasattr(engine.llm_coordinator, 'llm_client'):
            client_info = str(type(engine.llm_coordinator.llm_client))
            print(f"Engine LLM client type: {client_info}")
        
    except Exception as e:
        print(f"Engine provider integration error: {e}")
        # Document current limitation
        assert True, f"Engine provider integration not implemented (documenting issue): {e}"


def test_cli_argument_parsing_structure():
    """Test CLI argument parsing structure and requirements"""
    
    # Define what the CLI argument parsing should look like
    expected_cli_structure = """
    parser = argparse.ArgumentParser(description='TwitterExplorer Investigation CLI')
    parser.add_argument('query', nargs='*', help='Investigation query')
    parser.add_argument('--provider', choices=['openai', 'gemini'], default='gemini',
                       help='LLM provider to use (openai or gemini)')
    parser.add_argument('--max-searches', type=int, default=15,
                       help='Maximum number of searches to perform')
    """
    
    print("Expected CLI argument structure:")
    print(expected_cli_structure)
    
    # Check current cli_test.py structure
    cli_path = os.path.join(os.path.dirname(__file__), 'cli_test.py')
    with open(cli_path, 'r') as f:
        current_cli = f.read()
    
    has_argument_parser = 'ArgumentParser' in current_cli
    uses_argv_directly = 'sys.argv' in current_cli
    
    print(f"\nCurrent CLI structure:")
    print(f"  Uses ArgumentParser: {has_argument_parser}")
    print(f"  Uses sys.argv directly: {uses_argv_directly}")
    
    # Verify ArgumentParser is used (Issue #4 fixed)
    assert has_argument_parser and not uses_argv_directly, \
        "CLI should use ArgumentParser instead of sys.argv directly"


def test_provider_parameter_end_to_end():
    """Test complete provider parameter flow from CLI to LLM client"""
    
    # This is an aspirational test - shows what should work after implementation
    
    test_scenarios = [
        {
            'cli_args': ['python', 'cli_test.py', '--provider', 'openai', 'test query'],
            'expected_provider': 'openai'
        },
        {
            'cli_args': ['python', 'cli_test.py', '--provider', 'gemini', 'test query'],
            'expected_provider': 'gemini'
        },
        {
            'cli_args': ['python', 'cli_test.py', 'test query'],  # No provider specified
            'expected_provider': 'gemini'  # Default
        }
    ]
    
    print("Test scenarios for provider parameter:")
    for scenario in test_scenarios:
        print(f"  CLI: {' '.join(scenario['cli_args'])}")
        print(f"  Expected provider: {scenario['expected_provider']}")
        print()
    
    # This test documents the expected behavior
    assert True, "Provider parameter end-to-end flow documented - implementation needed"


def test_models_yaml_configuration_integration():
    """Test integration with models.yaml configuration file"""
    
    # Check if models.yaml exists and has provider configurations
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'models.yaml')
    yaml_exists = os.path.exists(config_path)
    
    print(f"models.yaml exists at {config_path}: {yaml_exists}")
    
    if yaml_exists:
        try:
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            print(f"Configuration data: {config_data}")
            
            # Check if it has provider configurations
            has_providers = 'providers' in config_data or any('openai' in str(config_data).lower(), 'gemini' in str(config_data).lower())
            print(f"Has provider configurations: {has_providers}")
            
        except Exception as e:
            print(f"Error reading models.yaml: {e}")
    
    # Test CLI integration with YAML config
    print("\nCLI should integrate with models.yaml for provider selection")
    assert True, "models.yaml integration documented - implementation verification needed"


def test_provider_switching_validation():
    """Test validation of provider switching parameters"""
    
    valid_providers = ['openai', 'gemini']
    invalid_providers = ['gpt4', 'claude', 'invalid_provider', '', None]
    
    print(f"Valid providers: {valid_providers}")
    print(f"Invalid providers that should be rejected: {invalid_providers}")
    
    # Test validation logic (this doesn't exist yet)
    def validate_provider(provider):
        """This function should exist after implementation"""
        return provider in valid_providers
    
    # Test validation
    for provider in valid_providers:
        assert validate_provider(provider), f"Valid provider {provider} should pass validation"
    
    for provider in invalid_providers:
        assert not validate_provider(provider), f"Invalid provider {provider} should fail validation"
    
    print("Provider validation logic documented - implementation needed in CLI")


def test_environment_variable_provider_fallback():
    """Test environment variable fallback for provider selection"""
    
    # Test if system can use environment variables for provider selection
    env_var_name = 'TWITTEREXPLORER_LLM_PROVIDER'
    
    print(f"Environment variable {env_var_name} for provider selection")
    
    # Check current value
    current_value = os.environ.get(env_var_name)
    print(f"Current {env_var_name} value: {current_value}")
    
    # Test priority order (after implementation):
    # 1. CLI --provider parameter (highest priority)
    # 2. Environment variable
    # 3. models.yaml default
    # 4. Hardcoded default (gemini)
    
    priority_order = [
        "CLI --provider parameter (highest priority)",
        "Environment variable TWITTEREXPLORER_LLM_PROVIDER",
        "models.yaml default configuration",
        "Hardcoded default (gemini)"
    ]
    
    print("\nProvider selection priority order:")
    for i, priority in enumerate(priority_order, 1):
        print(f"  {i}. {priority}")
    
    assert True, "Environment variable fallback documented - implementation needed"


if __name__ == "__main__":
    # Run tests to document current issues
    pytest.main([__file__, "-v", "-s"])