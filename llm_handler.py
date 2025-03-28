# llm_handler.py
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import json
import config
# import state_manager # No longer needed for history formatting here

# Configuration should happen once in app.py using secrets
# genai.configure(api_key=config.GEMINI_API_KEY) # Remove this
model = None # Will be set by app.py

def set_llm_model(api_key):
    """Initializes the model. Call this from app.py."""
    global model
    if not model:
        try:
             genai.configure(api_key=api_key)
             model = genai.GenerativeModel(
                 config.GEMINI_MODEL_NAME,
                 # safety_settings=... # Optional
            )
             print("LLM Model Initialized.")
        except Exception as e:
             print(f"Error initializing LLM Model: {e}")
             # Potentially raise or handle appropriately in Streamlit app
             raise

def format_data_for_prompt():
    """Formats endpoints and ontology for embedding in the prompt."""
    # Need to access the loaded data from state_manager
    from state_manager import endpoints_data, ontology_data_str # Import here or pass data in

    endpoints_str = json.dumps(endpoints_data, indent=2)
    ontology_str = ontology_data_str

    # Basic truncation (improve if needed)
    MAX_ENDPOINT_CHARS = 150000
    MAX_ONTOLOGY_CHARS = 100000
    if len(endpoints_str) > MAX_ENDPOINT_CHARS:
        print("Warning: Truncating endpoints spec for prompt.")
        endpoints_str = endpoints_str[:MAX_ENDPOINT_CHARS] + "\n... (truncated)"
    if len(ontology_str) > MAX_ONTOLOGY_CHARS:
         print("Warning: Truncating ontology spec for prompt.")
         ontology_str = ontology_str[:MAX_ONTOLOGY_CHARS] + "\n... (truncated)"

    return endpoints_str, ontology_str

# --- MODIFY FUNCTION SIGNATURE ---
def get_llm_plan(user_query, formatted_history):
    """Gets the structured plan or clarification from the LLM."""
    if not model:
        raise Exception("LLM Model not initialized. Call set_llm_model first.")

    endpoints_spec, ontology_spec = format_data_for_prompt()
    # history_prompt = state_manager.get_history_for_prompt() # REMOVE THIS
    history_prompt = formatted_history # USE ARGUMENT

    prompt = config.PLANNER_SYSTEM_PROMPT_TEMPLATE.format(
        endpoints_spec=endpoints_spec,
        ontology_spec=ontology_spec,
        history=history_prompt,
        user_query=user_query
    )

    print("\n--- Sending Planning Request to LLM ---")
    # print(prompt)
    print("--- End Planning Request ---")

    generation_config = GenerationConfig(
        temperature=0.05,
        # max_output_tokens=4096
    )

    response_text = ""
    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        # Handle potential blocks or lack of content
        if not response.parts:
             block_reason = response.prompt_feedback.block_reason if hasattr(response, 'prompt_feedback') else 'Unknown'
             print(f"Warning: LLM response was empty or blocked. Reason: {block_reason}")
             error_message = f"My response generation was blocked (Reason: {block_reason}). Please modify your query or check safety settings."
             return {"response_type": "ERROR", "message_to_user": error_message}

        response_text = response.text.strip()

        # Debug: Print raw LLM response
        print("\n--- LLM Raw Planning Response ---")
        print(response_text)
        print("--- End LLM Raw Planning Response ---")

        # Clean potential markdown ```json ... ```
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse the JSON response
        llm_output = json.loads(response_text)

        # Basic validation
        if 'response_type' not in llm_output:
             raise ValueError("LLM response missing 'response_type'")
        if llm_output['response_type'] == 'PLAN' and 'api_plan' not in llm_output:
             if 'message_to_user' not in llm_output or not llm_output['message_to_user']:
                 raise ValueError("LLM PLAN response missing 'api_plan' and explanation message.")
             if 'api_plan' not in llm_output:
                 llm_output['api_plan'] = []

        return llm_output

    except json.JSONDecodeError as e:
        print(f"Error decoding LLM JSON response: {e}")
        print(f"Raw response was: {response_text}")
        return {"response_type": "ERROR", "message_to_user": "Sorry, I received an invalid response format from the planning module. Please try rephrasing."}
    except ValueError as e:
         print(f"LLM response validation error: {e}")
         return {"response_type": "ERROR", "message_to_user": f"Sorry, there was an issue with the planned response structure: {e}"}
    except Exception as e:
        print(f"Error calling/processing Gemini API: {e}")
        error_detail = str(e)
        error_message = f"Sorry, I encountered an error during planning: {type(e).__name__}. Detail: {error_detail}"
        return {"response_type": "ERROR", "message_to_user": error_message}

# --- MODIFY FUNCTION SIGNATURE ---
def get_llm_summary(original_query, retrieved_data):
    """Gets the summary from the LLM based on retrieved data."""
    if not model:
        raise Exception("LLM Model not initialized. Call set_llm_model first.")

    # Prepare data summary string
    data_summary_str = ""
    if not retrieved_data:
         data_summary_str = "No data was retrieved or provided for summarization."
    else:
        for i, result in enumerate(retrieved_data):
            step_num = result.get('step_executed', i + 1) if isinstance(result, dict) else i + 1
            endpoint = result.get('endpoint', 'N/A') if isinstance(result, dict) else 'N/A'
            data_payload = result.get('data', 'No data or error for this step') if isinstance(result, dict) else result

            data_summary_str += f"--- Step {step_num} Result (Endpoint: {endpoint}) ---\n"
            try:
                 step_data_str = json.dumps(data_payload, indent=2, ensure_ascii=False)
            except TypeError:
                 step_data_str = str(data_payload)

            MAX_STEP_DATA_CHARS = 50000
            if len(step_data_str) > MAX_STEP_DATA_CHARS:
                 step_data_str = step_data_str[:MAX_STEP_DATA_CHARS] + "\n... (truncated)"
            data_summary_str += step_data_str + "\n\n"


    prompt = config.SUMMARIZER_SYSTEM_PROMPT_TEMPLATE.format(
        original_query=original_query,
        retrieved_data_summary=data_summary_str
    )

    print("\n--- Sending Summarization Request to LLM ---")
    # print(prompt)
    print("--- End Summarization Request ---")

    generation_config = GenerationConfig(
        temperature=0.05,
        # max_output_tokens=2048
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        # Handle potential blocks or lack of content
        if not response.parts:
             block_reason = response.prompt_feedback.block_reason if hasattr(response, 'prompt_feedback') else 'Unknown'
             print(f"Warning: LLM summary response was empty or blocked. Reason: {block_reason}")
             return f"Sorry, my summary generation was blocked (Reason: {block_reason})."

        summary = response.text.strip()
        print("\n--- LLM Raw Summary Response ---")
        print(summary)
        print("--- End LLM Raw Summary Response ---")
        return summary
    except Exception as e:
        print(f"Error calling Gemini API for summarization: {e}")
        error_detail = str(e)
        return f"Sorry, I encountered an error while summarizing the results: {type(e).__name__}. Detail: {error_detail}"