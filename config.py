# config.py
import os
# from dotenv import load_dotenv # No longer needed here

# load_dotenv() # No longer needed here

# --- API Keys ---
# REMOVE these lines - Keys will be loaded via st.secrets in app.py
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# --- API Endpoints ---
RAPIDAPI_TWITTER_HOST = "twitter-api45.p.rapidapi.com"
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_TWITTER_HOST}"

# --- LLM Configuration ---
#GEMINI_MODEL_NAME = "gemini-1.5-pro-latest" # Or your preferred model
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# --- Application Settings ---
# HISTORY_FILE = "conversation_history.json" # No longer needed for session history
ENDPOINTS_FILE = "merged_endpoints.json"
ONTOLOGY_FILE = "ontology_synonyms.py"
DEFAULT_MAX_PAGES_FALLBACK = 3
API_TIMEOUT_SECONDS = 7

# --- Prompt Templates ---
# Prompts are now loaded from the prompts/ folder for better organization and editing

def load_prompts():
    """Load prompts from the prompts folder"""
    try:
        from prompts.investigation_prompts import PLANNER_SYSTEM_PROMPT, SUMMARIZER_SYSTEM_PROMPT
        return PLANNER_SYSTEM_PROMPT, SUMMARIZER_SYSTEM_PROMPT
    except ImportError as e:
        print(f"Failed to load prompts from prompts folder: {e}")
        # Fallback to basic prompts if folder system fails
        return get_fallback_prompts()

def get_fallback_prompts():
    """Fallback prompts if the prompts folder system fails"""
    planner = """
You are an intelligent Twitter research strategist. Design effective searches that start simple and build complexity.

**Available Tools:** {endpoints_spec}
**Data Ontology:** {ontology_spec} 
**Previous Context:** {history}

**Strategy:** Start with obvious searches, try name variations, build on what works, avoid what doesn't.

**Current Query:** {user_query}

Respond with JSON: {{"response_type": "PLAN", "message_to_user": "strategy explanation", "api_plan": [search objects]}}
"""
    
    summarizer = """
Analyze the Twitter investigation results for: "{original_query}"

**Data Found:** {retrieved_data_summary}

Provide insights that directly answer the user's question. Be analytical, not just descriptive.
"""
    
    return planner, summarizer

# Load the prompts
PLANNER_SYSTEM_PROMPT_TEMPLATE, SUMMARIZER_SYSTEM_PROMPT_TEMPLATE = load_prompts()