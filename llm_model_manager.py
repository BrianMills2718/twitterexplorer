import yaml
import os
from typing import Dict, List, Optional
import logging
from pathlib import Path

class LLMModelManager:
    """Centralized model configuration and selection for investigation system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger("model_manager")
        
        # Configuration loading priority:
        # 1. Explicit config_path parameter
        # 2. config/models.yaml in project
        # 3. Environment variables
        # 4. Hardcoded defaults
        
        if config_path and os.path.exists(config_path):
            self.config_file = config_path
        else:
            # Look for config/models.yaml in project directory
            project_config = Path(__file__).parent / "config" / "models.yaml"
            if project_config.exists():
                self.config_file = str(project_config)
            else:
                self.config_file = None
        
        self.config = self._load_config()
        self._validate_config()
        
        self.logger.info(f"Model manager initialized with config: {self.config_file or 'defaults'}")
    
    def _load_config(self) -> Dict:
        """Load configuration from file or environment or defaults"""
        config = {
            "default_provider": "gemini",
            "models": {
                "strategic_coordinator": "gemini/gemini-2.5-flash",
                "finding_evaluator": "gemini/gemini-2.5-flash",
                "insight_synthesizer": "gemini/gemini-2.5-flash", 
                "emergent_questions": "gemini/gemini-2.5-flash",
                "cross_reference": "gpt-5-mini",
                "temporal_analysis": "gpt-5-mini",
                "fallback_primary": "gpt-5-mini",
                "fallback_secondary": "gpt-3.5-turbo"
            },
            "provider_settings": {
                "gemini": {"temperature": 0.3, "max_tokens": 8000},
                "openai": {"temperature": 0.3, "max_tokens": 4000}
            }
        }
        
        # Load from config file if available
        if self.config_file:
            try:
                with open(self.config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                    # Merge file config into defaults
                    config.update(file_config)
                    self.logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables
        env_overrides = {}
        for operation in config["models"].keys():
            env_var = f"INVESTIGATION_MODEL_{operation.upper()}"
            if env_var in os.environ:
                env_overrides[operation] = os.environ[env_var]
                self.logger.info(f"Environment override: {operation} = {os.environ[env_var]}")
        
        if env_overrides:
            config["models"].update(env_overrides)
        
        return config
    
    def _validate_config(self):
        """Validate configuration structure and model names"""
        required_operations = [
            "strategic_coordinator", "finding_evaluator", "insight_synthesizer", 
            "emergent_questions", "fallback_primary"
        ]
        
        for operation in required_operations:
            if operation not in self.config["models"]:
                raise ValueError(f"Missing required model configuration for: {operation}")
        
        # Validate model name formats
        for operation, model in self.config["models"].items():
            if not isinstance(model, str) or not model.strip():
                raise ValueError(f"Invalid model name for {operation}: {model}")
        
        self.logger.info("Configuration validation passed")
    
    def get_model_for_operation(self, operation: str) -> str:
        """Get configured model for specific operation"""
        if operation not in self.config["models"]:
            self.logger.warning(f"Unknown operation {operation}, using fallback")
            return self.config["models"]["fallback_primary"]
        
        model = self.config["models"][operation]
        self.logger.debug(f"Model for {operation}: {model}")
        return model
    
    def get_fallback_model(self, failed_model: str) -> str:
        """Get fallback model when primary fails"""
        # Simple fallback strategy
        if failed_model != self.config["models"]["fallback_primary"]:
            return self.config["models"]["fallback_primary"]
        else:
            return self.config["models"]["fallback_secondary"]
    
    def get_provider_settings(self, model: str) -> Dict:
        """Get provider-specific settings for a model"""
        # Extract provider from model name (e.g., "gemini/gemini-2.5-flash" -> "gemini")
        if "/" in model:
            provider = model.split("/")[0]
        else:
            # Default provider detection based on model name
            if model.startswith("gpt"):
                provider = "openai"
            elif model.startswith("gemini"):
                provider = "gemini"
            else:
                provider = self.config["default_provider"]
        
        return self.config["provider_settings"].get(provider, {})
    
    def list_available_operations(self) -> List[str]:
        """Show all configurable operations"""
        return list(self.config["models"].keys())
    
    def get_current_config_summary(self) -> Dict:
        """Get summary of current configuration for debugging"""
        return {
            "config_source": self.config_file or "defaults",
            "default_provider": self.config["default_provider"],
            "operations": {op: model for op, model in self.config["models"].items()},
            "provider_count": len(set(
                model.split("/")[0] if "/" in model else (
                    "openai" if model.startswith("gpt") else 
                    "gemini" if model.startswith("gemini") else 
                    "unknown"
                )
                for model in self.config["models"].values()
            ))
        }