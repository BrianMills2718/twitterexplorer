# llm_client.py
"""
LiteLLM Integration with Structured Output for Graph-Based Investigation System

Provides LLM client with structured output capabilities using gpt-5-mini
for strategic decision making and analysis.
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import litellm with error handling
try:
    import litellm
    from litellm import completion
    # Enable client-side JSON schema validation for better compatibility
    litellm.enable_json_schema_validation = True
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    print("Warning: litellm not available. Install with: pip install litellm")

def get_litellm_client():
    """Initialize LiteLLM client with multi-provider support"""
    if not LITELLM_AVAILABLE:
        raise RuntimeError("LiteLLM not available. Install with: pip install litellm")
    
    # Load all available API keys from secrets and set environment variables
    # This allows LiteLLM to automatically detect providers based on model names
    _load_api_keys_to_environment()
    
    return LiteLLMClient()

def _load_api_keys_to_environment():
    """Load API keys from various sources into environment variables for LiteLLM auto-detection"""
    
    # API keys that LiteLLM looks for
    api_key_mappings = {
        'OPENAI_API_KEY': 'OPENAI_API_KEY',
        'GEMINI_API_KEY': 'GEMINI_API_KEY', 
        'ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY',
        'COHERE_API_KEY': 'COHERE_API_KEY',
        'TOGETHER_API_KEY': 'TOGETHER_API_KEY'
    }
    
    # Try Streamlit secrets first
    loaded_keys = {}
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            for key_name in api_key_mappings.keys():
                if key_name in st.secrets:
                    loaded_keys[key_name] = st.secrets[key_name]
    except (ImportError, FileNotFoundError, AttributeError):
        pass
    
    # Try loading from secrets.toml directly (works in tests and non-Streamlit environments)  
    if not loaded_keys:
        try:
            import toml
            secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
            if os.path.exists(secrets_path):
                secrets = toml.load(secrets_path)
                for key_name in api_key_mappings.keys():
                    if key_name in secrets:
                        loaded_keys[key_name] = secrets[key_name]
        except ImportError:
            pass
    
    # Try .env file as fallback
    if not loaded_keys:
        load_dotenv()
        for key_name in api_key_mappings.keys():
            env_value = os.getenv(key_name)
            if env_value and env_value != "your_openai_api_key_here":
                loaded_keys[key_name] = env_value
    
    # Set all found keys as environment variables for LiteLLM
    for key_name, key_value in loaded_keys.items():
        if key_value and key_value != "your_openai_api_key_here":
            os.environ[key_name] = key_value
    
    # Verify we have at least one valid API key
    if not loaded_keys:
        raise RuntimeError("No valid API keys found. Please set API keys in .streamlit/secrets.toml or environment variables")
    
    print(f"LiteLLM: Loaded {len(loaded_keys)} API keys: {list(loaded_keys.keys())}")
    return loaded_keys

class LiteLLMClient:
    """
    LiteLLM client wrapper with structured output support
    
    Provides completion capabilities with optional pydantic model response formatting
    for strategic investigation coordination. Uses LiteLLM's automatic provider detection
    based on model names and available environment variables.
    """
    
    def __init__(self):
        if not LITELLM_AVAILABLE:
            raise RuntimeError("LiteLLM not available. Install with: pip install litellm")
        
        # No API key parameter needed - LiteLLM auto-detects based on model names
        # and environment variables that were loaded by get_litellm_client()
        
    def completion(self, model: str, messages: List[Dict[str, str]], 
                   response_format: Optional[Union[BaseModel, Dict[str, Any]]] = None, **kwargs):
        """
        Get completion with optional structured output using native LiteLLM capabilities
        
        Args:
            model: Model name (e.g., "gpt-5-mini")
            messages: List of message dicts with role and content
            response_format: Optional pydantic model or dict for structured output
            **kwargs: Additional parameters for litellm
            
        Returns:
            LiteLLM completion response with structured output if requested
        """
        if not LITELLM_AVAILABLE:
            raise RuntimeError("LiteLLM not available")
            
        try:
            # Prepare parameters for direct litellm.completion call
            # LiteLLM auto-detects provider based on model name and environment variables
            completion_params = {
                "model": model,
                "messages": messages.copy(),  # Work with copy to avoid modifying original
                **kwargs
            }
            
            # Add structured output support if requested
            if response_format:
                if isinstance(response_format, dict):
                    # Direct dict format (already converted for OpenAI JSON mode)
                    completion_params["response_format"] = response_format
                elif hasattr(response_format, 'model_json_schema'):
                    # Pydantic model - convert to new structured output format
                    schema = response_format.model_json_schema()
                    
                    # Ensure additionalProperties is false and required array exists for all objects (required for structured output)
                    def fix_schema_for_structured_output(schema_obj):
                        if isinstance(schema_obj, dict):
                            if schema_obj.get("type") == "object":
                                schema_obj["additionalProperties"] = False
                                # Ensure required array exists - if missing and has properties, set to empty array
                                if "properties" in schema_obj and "required" not in schema_obj:
                                    schema_obj["required"] = []
                            # Recursively fix nested objects
                            for key, value in schema_obj.items():
                                if isinstance(value, dict):
                                    fix_schema_for_structured_output(value)
                                elif isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, dict):
                                            fix_schema_for_structured_output(item)
                    
                    fix_schema_for_structured_output(schema)
                    
                    completion_params["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": getattr(response_format, '__name__', 'structured_output'),
                            "strict": True,
                            "schema": schema
                        }
                    }
                else:
                    # Fallback to JSON mode for OpenAI
                    completion_params["response_format"] = {"type": "json_object"}
            
            # Make the direct litellm API call (not through self.completion wrapper)
            response = completion(**completion_params)
            
            # If structured output requested and it's a Pydantic model, parse and attach
            if (response_format and hasattr(response_format, 'model_json_schema') 
                and response.choices and response.choices[0].message):
                try:
                    content = response.choices[0].message.content
                    if isinstance(content, str) and content.strip():
                        # Clean up any markdown formatting
                        content = content.strip()
                        if content.startswith('```json'):
                            content = content[7:]
                        if content.endswith('```'):
                            content = content[:-3]
                        content = content.strip()
                        
                        # Parse JSON and create pydantic model
                        parsed_data = json.loads(content)
                        parsed_model = response_format(**parsed_data)
                        
                        # Attach parsed model to response (OpenAI-style interface)
                        response.choices[0].message.parsed = parsed_model
                        
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    # If parsing fails, set parsed to None but don't crash
                    print(f"Warning: Failed to parse structured output: {e}")
                    print(f"Raw content: {content[:200] if 'content' in locals() else 'None'}")
                    response.choices[0].message.parsed = None
            
            return response
            
        except Exception as e:
            # Re-raise with more context
            raise RuntimeError(f"LiteLLM completion failed: {e}")
    
    def simple_completion(self, model: str, prompt: str, **kwargs) -> str:
        """
        Simple text completion without structured output
        
        Args:
            model: Model name
            prompt: Text prompt
            **kwargs: Additional parameters
            
        Returns:
            Response text content
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.completion(model, messages, **kwargs)
        
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content or ""
        return ""


# Compatibility functions for existing code
def create_gemini_client(api_key: str = None) -> LiteLLMClient:
    """Create Gemini client using LiteLLM (backward compatibility)"""
    # API key parameter ignored - LiteLLM uses environment variables
    return LiteLLMClient()

def get_default_model() -> str:
    """Get default model for investigations"""
    try:
        from llm_model_manager import LLMModelManager
        manager = LLMModelManager()
        return manager.get_model_for_operation("fallback_primary")
    except ImportError:
        # Fallback if model manager not available
        return "gemini/gemini-2.5-flash"


# Pydantic models for common structured outputs

class SearchParameters(BaseModel):
    """Search parameters - flexible model that accepts any string fields"""
    query: Optional[str] = Field(description="Search query term")
    screenname: Optional[str] = Field(description="Twitter username")
    country: Optional[str] = Field(description="Country filter")
    rest_id: Optional[str] = Field(description="REST API ID")
    rest_ids: Optional[str] = Field(description="Multiple REST API IDs")
    cursor: Optional[str] = Field(description="Pagination cursor")
    search_type: Optional[str] = Field(description="Type of search")
    id: Optional[str] = Field(description="Generic ID field")
    tweet_id: Optional[str] = Field(description="Tweet ID")
    user: Optional[str] = Field(description="User field")
    follows: Optional[str] = Field(description="Follows relationship")
    list_id: Optional[str] = Field(description="Twitter list ID")
    
    class Config:
        extra = "forbid"  # Prevents additional properties

class SearchStrategy(BaseModel):
    """Individual search strategy within a decision"""
    endpoint: str
    parameters: SearchParameters
    reasoning: str

class StrategicDecision(BaseModel):
    """Structured decision for investigation strategy"""
    decision_type: str
    reasoning: str
    searches: List[SearchStrategy]  # Use proper nested model instead of Dict[str, Any]
    expected_outcomes: List[str]
    confidence: Optional[float] = Field(description="Confidence level for the decision")

class InvestigationEvaluation(BaseModel):
    """Structured evaluation of investigation results"""
    relevance_score: float
    information_value: float
    key_insights: List[str]
    remaining_gaps: List[str]
    should_continue: bool
    continuation_strategy: Optional[str] = Field(description="Strategy for continuing investigation if needed")

class ContextSynthesis(BaseModel):
    """Structured synthesis of investigation context"""
    current_understanding: str
    confidence_level: float
    key_findings: List[str]
    critical_gaps: List[str]
    investigation_completeness: float
    next_priorities: List[str]

class EmergentQuestion(BaseModel):
    """Individual emergent question structure"""
    text: str = Field(description="The emergent question text")
    reason: str = Field(description="Why this question emerged from the insights")

class EmergentQuestions(BaseModel):
    """Structured output for emergent questions"""
    questions: List[EmergentQuestion] = Field(description="List of emergent questions")
    priority_scores: List[float] = Field(description="Priority scores for each question")
    investigation_impact: str = Field(description="How these questions impact the investigation")