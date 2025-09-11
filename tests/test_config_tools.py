import pytest
import tempfile
import os
import sys
import subprocess
from pathlib import Path

def test_validate_config_tool():
    """Test model configuration validation tool"""
    
    # Create valid config
    config_content = """
default_provider: gemini
models:
  strategic_coordinator: gemini/gemini-2.5-flash
  finding_evaluator: gemini/gemini-2.5-flash
  insight_synthesizer: gemini/gemini-2.5-flash
  emergent_questions: gemini/gemini-2.5-flash
  cross_reference: gpt-5-mini
  temporal_analysis: gpt-5-mini
  fallback_primary: gpt-5-mini
  fallback_secondary: gpt-3.5-turbo
provider_settings:
  gemini:
    temperature: 0.3
    max_tokens: 8000
  openai:
    temperature: 0.3
    max_tokens: 4000
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name
    
    try:
        # Test validation tool
        result = subprocess.run([
            sys.executable, "validate_model_config.py", "--config", config_path
        ], capture_output=True, text=True, cwd="twitterexplorer")
        
        # Should succeed (even if API calls fail, config should be valid)
        assert "✅ Model configuration loaded successfully" in result.stdout
        
    finally:
        os.unlink(config_path)

def test_generate_config_tool():
    """Test configuration generation tool"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "test_config.yaml")
        
        # Test generation
        result = subprocess.run([
            sys.executable, "generate_model_config.py", "balanced", 
            "--output", output_path
        ], capture_output=True, text=True, cwd="twitterexplorer")
        
        # Should succeed
        assert result.returncode == 0
        assert "✅ Configuration generated" in result.stdout
        
        # Generated file should exist and be valid
        assert os.path.exists(output_path)
        
        # Should be able to load with model manager
        from llm_model_manager import LLMModelManager
        manager = LLMModelManager(config_path=output_path)
        
        # Should have all required operations
        required_ops = ["strategic_coordinator", "finding_evaluator", "insight_synthesizer"]
        for op in required_ops:
            assert manager.get_model_for_operation(op) is not None