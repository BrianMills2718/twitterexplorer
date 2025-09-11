import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, Mock
from llm_model_manager import LLMModelManager

def test_model_manager_default_config():
    """Test model manager loads default configuration"""
    manager = LLMModelManager()
    
    # Should have all required operations
    required_ops = ["strategic_coordinator", "finding_evaluator", "insight_synthesizer", "emergent_questions"]
    for op in required_ops:
        assert manager.get_model_for_operation(op) is not None
    
    # Should have fallback models
    assert manager.get_fallback_model("test") is not None

def test_model_manager_config_file():
    """Test model manager loads from config file"""
    
    # Create temporary config file
    config = {
        "default_provider": "openai",
        "models": {
            "strategic_coordinator": "gpt-4",
            "finding_evaluator": "gpt-5-mini",
            "insight_synthesizer": "gpt-5-mini",
            "emergent_questions": "gpt-5-mini",
            "fallback_primary": "gpt-3.5-turbo",
            "fallback_secondary": "gpt-3.5-turbo"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    try:
        manager = LLMModelManager(config_path=config_path)
        
        # Should load from config file
        assert manager.get_model_for_operation("strategic_coordinator") == "gpt-4"
        assert manager.get_model_for_operation("finding_evaluator") == "gpt-5-mini"
        
    finally:
        os.unlink(config_path)

def test_model_manager_environment_overrides():
    """Test environment variable overrides"""
    
    with patch.dict(os.environ, {
        'INVESTIGATION_MODEL_FINDING_EVALUATOR': 'custom-model'
    }):
        manager = LLMModelManager()
        
        # Environment should override default
        assert manager.get_model_for_operation("finding_evaluator") == "custom-model"

def test_model_manager_validation():
    """Test configuration validation"""
    
    # Test missing required operation
    config = {
        "models": {
            "strategic_coordinator": "gpt-4"
            # Missing required operations
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Missing required model configuration"):
            LLMModelManager(config_path=config_path)
    finally:
        os.unlink(config_path)

def test_provider_settings_extraction():
    """Test provider settings extraction from model names"""
    manager = LLMModelManager()
    
    # Test Gemini model
    settings = manager.get_provider_settings("gemini/gemini-2.5-flash")
    assert "temperature" in settings
    
    # Test OpenAI model
    settings = manager.get_provider_settings("gpt-4")
    assert "temperature" in settings

def test_config_summary():
    """Test configuration summary generation"""
    manager = LLMModelManager()
    
    summary = manager.get_current_config_summary()
    
    assert "config_source" in summary
    assert "default_provider" in summary
    assert "operations" in summary
    assert "provider_count" in summary
    assert isinstance(summary["provider_count"], int)