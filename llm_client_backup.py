# llm_client.py
"""
LiteLLM Integration with Structured Output for Graph-Based Investigation System

Provides LLM client with structured output capabilities using gemini-2.5-flash
for strategic decision making and analysis.
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
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
    """Initialize LiteLLM client with environment variables"""
    if not LITELLM_AVAILABLE:
        raise RuntimeError("LiteLLM not available. Install with: pip install litellm")
        
    # Try to get API key from environment first
    api_key = os.getenv("GEMINI_API_KEY")
    
    # If not in environment or is placeholder, try Streamlit secrets
    if not api_key or api_key == "your_gemini_api_key_here":
        try:
            import streamlit as st
            # Only try to access secrets if we're in a real Streamlit app
            if hasattr(st, 'secrets'):
                try:
                    if 'GEMINI_API_KEY' in st.secrets:
                        api_key = st.secrets['GEMINI_API_KEY']
                except (FileNotFoundError, AttributeError):
                    # Secrets file not found or not in Streamlit context
                    pass
        except ImportError:
            pass
            
        # Try loading from secrets.toml directly (works in tests)
        if not api_key or api_key == "your_gemini_api_key_here":
            try:
                import toml
                secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
                if os.path.exists(secrets_path):
                    secrets = toml.load(secrets_path)
                    api_key = secrets.get('GEMINI_API_KEY')
            except ImportError:
                pass
    
    # If still not found, load from .env as fallback
    if not api_key or api_key == "your_gemini_api_key_here":
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        raise RuntimeError("GEMINI_API_KEY not found. Please set it in .env file or .streamlit/secrets.toml")
    
    return LiteLLMClient(api_key)

class LiteLLMClient:
    """
    LiteLLM client wrapper with structured output support
    
    Provides completion capabilities with optional pydantic model response formatting
    for strategic investigation coordination.
    """
    
    def __init__(self, api_key: str):
        if not LITELLM_AVAILABLE:
            raise RuntimeError("LiteLLM not available. Install with: pip install litellm")
            
        self.api_key = api_key
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Verify API key format (basic validation)
        if not api_key or len(api_key) < 10:
            raise ValueError("Invalid GEMINI_API_KEY - must be a valid API key")
        
    def completion(self, model: str, messages: List[Dict[str, str]], 
                   response_format: Optional[BaseModel] = None, **kwargs):
        """
        Get completion with optional structured output using native LiteLLM capabilities
        
        Args:
            model: Model name (e.g., "gemini/gemini-2.5-flash")
            messages: List of message dicts with role and content
            response_format: Optional pydantic model for structured output
            **kwargs: Additional parameters for litellm
            
        Returns:
            LiteLLM completion response with structured output if requested
        """
        if not LITELLM_AVAILABLE:
            raise RuntimeError("LiteLLM not available")
            
        try:
            # Prepare parameters for direct litellm.completion call
            completion_params = {
                "model": model,
                "messages": messages.copy(),  # Work with copy to avoid modifying original
                "api_key": self.api_key,
                **kwargs
            }
            
            # Add native structured output support if requested
            if response_format:
                # Use LiteLLM's native structured output with Pydantic schema
                # This is the PROPER way - pass the schema directly to response_format
                completion_params["response_format"] = {
                    "type": "json_object",
                    "response_schema": response_format.model_json_schema()
                }
                
                # NO manual prompt modification needed - LiteLLM handles this internally!
            
            # Make the direct litellm API call (not through self.completion wrapper)
            response = completion(**completion_params)
            
            # If structured output requested, parse and attach the model
            if response_format and response.choices and response.choices[0].message:
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
def create_gemini_client(api_key: str) -> LiteLLMClient:
    """Create Gemini client using LiteLLM (backward compatibility)"""
    return LiteLLMClient(api_key)

def get_default_model() -> str:
    """Get default model for investigations"""
    return "gemini/gemini-2.5-flash"


# Pydantic models for common structured outputs

class SearchParameters(BaseModel):
    """Search parameters - flexible model that accepts any string fields"""
    query: Optional[str] = None
    screenname: Optional[str] = None
    country: Optional[str] = None
    rest_id: Optional[str] = None
    rest_ids: Optional[str] = None
    cursor: Optional[str] = None
    search_type: Optional[str] = None
    id: Optional[str] = None
    tweet_id: Optional[str] = None
    user: Optional[str] = None
    follows: Optional[str] = None
    list_id: Optional[str] = None

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
    confidence: Optional[float] = None

class InvestigationEvaluation(BaseModel):
    """Structured evaluation of investigation results"""
    relevance_score: float
    information_value: float
    key_insights: List[str]
    remaining_gaps: List[str]
    should_continue: bool
    continuation_strategy: Optional[str] = None

class ContextSynthesis(BaseModel):
    """Structured synthesis of investigation context"""
    current_understanding: str
    confidence_level: float
    key_findings: List[str]
    critical_gaps: List[str]
    investigation_completeness: float
    next_priorities: List[str]

class EmergentQuestions(BaseModel):
    """Structured output for emergent questions"""
    questions: List[Dict[str, str]]  # {"text": "question", "reason": "emergence reason"}
    priority_scores: List[float]
    investigation_impact: str