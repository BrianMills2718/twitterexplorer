# state_manager.py
import json
import os
import config
import importlib.util

endpoints_data = None
ontology_data_str = None

def load_initial_data():
    """Loads endpoint specs and ontology data at startup."""
    global endpoints_data, ontology_data_str
    # Only load if not already loaded
    if endpoints_data is None:
        try:
            with open(config.ENDPOINTS_FILE, 'r', encoding='utf-8') as f: # Added encoding
                endpoints_data = json.load(f)
            print(f"Loaded endpoint data from {config.ENDPOINTS_FILE}")
        except Exception as e:
            print(f"Error loading endpoint data: {e}")
            endpoints_data = [] # Ensure it's an empty list if loading fails

    if ontology_data_str is None:
        try:
            with open(config.ONTOLOGY_FILE, 'r', encoding='utf-8') as f: # Added encoding
                 ontology_data_str = f.read()
            print(f"Loaded ontology data from {config.ONTOLOGY_FILE}")
        except Exception as e:
            print(f"Error loading ontology data: {e}")
            ontology_data_str = "" # Ensure it's empty if loading fails

def get_history_for_prompt(current_llm_history, max_tokens=800000):
    """Formats history from the provided list for the LLM prompt."""
    # Operates on the list passed from st.session_state
    history_str = ""
    temp_history = []
    current_len = 0
    # Rough estimate: 1 token ~ 4 chars. Adjust multiplier as needed.
    max_len = max_tokens * 4

    turn_count = len(current_llm_history)
    for i, turn in enumerate(reversed(current_llm_history)):
        # Basic check for expected keys
        user_query = turn.get("user_query", "[missing query]")
        llm_response = turn.get("llm_response", "[missing response]")
        summary = turn.get("summary")

        turn_str = f"## Turn {turn_count - i}\n"
        turn_str += f"User: {user_query}\n"
        # Dump the structured response (plan/clarification)
        try:
            turn_str += f"Assistant Response: {json.dumps(llm_response)}\n"
        except TypeError:
             turn_str += f"Assistant Response: [Could not serialize response: {llm_response}]\n"

        if summary:
             turn_str += f"Assistant Summary: {summary}\n\n"
        else:
             turn_str += "\n"

        # Check length before adding
        if current_len + len(turn_str) > max_len and temp_history: # Avoid truncating if it's the only turn
            print("History truncated due to estimated token limit.")
            break

        temp_history.insert(0, turn_str) # Add to beginning to maintain order
        current_len += len(turn_str)

    return "".join(temp_history) if temp_history else "No history yet."

# Load data when the module is imported by the app
load_initial_data()