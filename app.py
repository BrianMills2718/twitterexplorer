# app.py
import streamlit as st
import json
import time

# Import your existing modules
import config
import state_manager # Ensure this now loads data but not file history
import llm_handler
import api_client

# --- Page Config ---
st.set_page_config(page_title="LLM Twitter Explorer", layout="wide")
st.title("🕵️ LLM Twitter Explorer")
st.caption("Ask questions about Twitter users, tweets, followers, etc.")

# --- Initialization ---
# Load static data (ontology, endpoints)
# This function is in state_manager and should ideally run only once.
# Streamlit usually handles module import caching, but @st.cache_data could be used if needed.
try:
    state_manager.load_initial_data()
    if not state_manager.endpoints_data or not state_manager.ontology_data_str:
         st.error("Failed to load endpoint or ontology data. Check file paths and content.")
         st.stop() # Halt execution if essential data is missing
except Exception as e:
    st.error(f"Error during initial data load: {e}")
    st.stop()


# Load API keys from secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    RAPIDAPI_KEY = st.secrets["RAPIDAPI_KEY"]
except KeyError as e:
    st.error(f"Missing API Key in Streamlit Secrets (secrets.toml): {e}")
    st.info("Please create a `.streamlit/secrets.toml` file with your GEMINI_API_KEY and RAPIDAPI_KEY.")
    st.stop()

# Initialize LLM Handler (call this only once per session ideally)
try:
    llm_handler.set_llm_model(GEMINI_API_KEY)
except Exception as e:
    st.error(f"Failed to initialize the LLM handler: {e}")
    st.stop()


# Initialize session state for messages (chat display) and history (LLM context)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "llm_history" not in st.session_state:
    st.session_state.llm_history = [] # This replaces the old file-based history

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle User Input ---
if prompt := st.chat_input("Ask about Twitter..."):
    # Add user message to display state
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Call Backend Logic ---
    final_summary = ""
    llm_structured_response = {} # To store the plan/clarification for history

    try:
        # Display thinking indicator
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # 1. Get Plan/Clarification from LLM
                # Format history from session state
                formatted_hist = state_manager.get_history_for_prompt(st.session_state.llm_history)
                llm_response = llm_handler.get_llm_plan(prompt, formatted_hist)
                llm_structured_response = llm_response # Save for history

                response_type = llm_response.get('response_type')
                message_to_user = llm_response.get('message_to_user')
                api_plan = llm_response.get('api_plan')

                # Display initial message from LLM (status or clarification)
                if message_to_user:
                     st.info(message_to_user) # Use st.info for status messages

                if response_type == "CLARIFICATION" or response_type == "ERROR":
                    final_summary = message_to_user # Use the clarification/error as the final message

                elif response_type == "PLAN":
                    if not api_plan:
                        final_summary = message_to_user or "I generated a plan but it was empty. Please try again."
                    else:
                        # 2. Execute API Plan
                        execution_results = []
                        execution_error_occurred = False
                        with st.status("Executing API plan...", expanded=False) as status_ui:
                            start_time = time.time()
                            sorted_plan = sorted(api_plan, key=lambda x: x.get('step', 0))
                            for step_num, step in enumerate(sorted_plan):
                                st.write(f"Step {step_num + 1}: Calling {step.get('endpoint')}...")
                                step_result = api_client.execute_api_step(
                                    step,
                                    execution_results, # Pass results from previous steps
                                    RAPIDAPI_KEY       # Pass the API key
                                )
                                # Add step number executed for clarity in summary context
                                step_result['step_executed'] = step.get('step', step_num + 1)
                                execution_results.append(step_result)

                                if 'error' in step_result:
                                    error_msg = f"Error in Step {step_num + 1} ({step.get('endpoint')}): {step_result['error']}"
                                    st.error(error_msg)
                                    final_summary = f"I encountered an error during execution and couldn't complete your request:\n```\n{error_msg}\n```"
                                    execution_error_occurred = True
                                    status_ui.update(label="Execution failed!", state="error", expanded=True)
                                    break # Stop execution
                                else:
                                     st.write(f"Step {step_num + 1} completed.")

                            if not execution_error_occurred:
                                exec_time = time.time() - start_time
                                status_ui.update(label=f"API Execution Complete ({exec_time:.2f}s)", state="complete", expanded=False)

                        # 3. Summarize Results (if execution successful)
                        if not execution_error_occurred:
                            if not execution_results or not any(res.get('data') for res in execution_results if res and 'error' not in res):
                                final_summary = "I executed the plan, but no data was retrieved to summarize."
                            else:
                                with st.spinner("Generating summary..."):
                                    # --- Check for filtering necessity ---
                                    final_data_for_summary = execution_results
                                    if "replies" in prompt.lower() and ("made by" in prompt.lower() or "from" in prompt.lower()):
                                         st.write("Filtering results for replies...") # Show filtering status
                                         filtered_results = []
                                         if execution_results and 'data' in execution_results[0] and isinstance(execution_results[0]['data'], dict) and 'timeline' in execution_results[0]['data']:
                                              timeline_data = execution_results[0]['data']['timeline']
                                              if isinstance(timeline_data, list):
                                                   actual_replies = [
                                                       item for item in timeline_data
                                                       if item and item.get('in_reply_to_status_id_str') # Check if key exists and is not None/empty
                                                   ]
                                                   if actual_replies:
                                                        filtered_step_result = execution_results[0].copy() # Copy structure
                                                        filtered_step_result['data'] = { 'timeline': actual_replies } # Replace with filtered data
                                                        filtered_results.append(filtered_step_result)
                                                        st.write(f"Found {len(actual_replies)} replies after filtering.")
                                                   else:
                                                        st.write("No actual replies found in timeline data after filtering.")
                                                        # Provide empty structure to summarizer
                                                        filtered_results.append({'endpoint': execution_results[0].get('endpoint'), 'data': {'timeline': []}})

                                              # Append results from other steps if any (e.g., search fallback)
                                              if len(execution_results) > 1:
                                                  filtered_results.extend(execution_results[1:])

                                              if filtered_results:
                                                  final_data_for_summary = filtered_results
                                              else: # Should not happen if list check passed, but as fallback
                                                   final_data_for_summary = [{'endpoint': 'filter', 'data': {'timeline': []}}]
                                         else:
                                              st.warning("Could not find 'timeline' list in first step results for filtering.")
                                    # --- End Filtering Check ---

                                    final_summary = llm_handler.get_llm_summary(prompt, final_data_for_summary)

                else: # Should not happen based on current validation, but catchall
                     final_summary = "Sorry, I received an unexpected response type from the planning module."

    except Exception as e:
        # Catch any unexpected errors during the whole process
        st.error(f"An unexpected error occurred: {e}")
        final_summary = f"Sorry, an unexpected error stopped me from completing your request: {e}"
        # Also add to LLM history for context
        llm_structured_response = {"response_type": "SYSTEM_ERROR", "message_to_user": str(e)}


    # --- Display Final AI Response and Update History ---
    # Ensure final_summary is a string
    if not isinstance(final_summary, str):
        final_summary = "Sorry, I could not generate a final response."

    with st.chat_message("assistant"):
        st.markdown(final_summary)

    # Add assistant response to display state
    st.session_state.messages.append({"role": "assistant", "content": final_summary})
    # Add turn details to LLM history state
    st.session_state.llm_history.append({
        "user_query": prompt,
        "llm_response": llm_structured_response, # The plan/clarification JSON
        "summary": final_summary # The final text shown to user
        })