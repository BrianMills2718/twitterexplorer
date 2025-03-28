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
GEMINI_MODEL_NAME = "gemini-1.5-pro-latest" # Or your preferred model

# --- Application Settings ---
# HISTORY_FILE = "conversation_history.json" # No longer needed for session history
ENDPOINTS_FILE = "merged_endpoints.json"
ONTOLOGY_FILE = "ontology_synonyms.py"
DEFAULT_MAX_PAGES_FALLBACK = 3
API_TIMEOUT_SECONDS = 45

# --- Prompt Templates ---
# Note: Actual ontology/endpoints data will be loaded and inserted dynamically
PLANNER_SYSTEM_PROMPT_TEMPLATE = """
You are an expert AI assistant tasked with exploring Twitter data using a specific set of API tools.
Your goal is to understand the user's request, determine if it's clear and feasible with the available tools, and either ask for clarification or create a step-by-step execution plan for the available API endpoints.

**Available Tools (API Endpoints):**
{endpoints_spec}

**Data Ontology & Synonyms:**
{ontology_spec}

**Conversation History:**
{history}

**Instructions:**
1.  Analyze the **Current User Request** based on the **Conversation History**, **Available Tools**, and **Ontology**. Identify retweets in timelines by checking for the presence of the 'retweeted_tweet' object.
2.  **Check Feasibility & Clarity:** Can the request be fulfilled with the tools? Is it specific enough?
3.  **If Vague or Unfeasible:** Respond with `response_type: CLARIFICATION` and provide a clear `message_to_user` asking for more details or explaining why it cannot be done.
4.  **If Clear and Feasible:** Respond with `response_type: PLAN`. Create a JSON list under the `api_plan` key. Each object in the list represents an API call step:
    * `step`: A sequential number (1, 2, ...).
    * `endpoint`: The exact endpoint URL suffix (e.g., "timeline.php").
    * `params`: A dictionary of required and optional parameters extracted or inferred from the request. Use the **Ontology** to map user terms to API parameter names (e.g., 'user' might map to 'screenname').
    * `reason`: Briefly explain why this step is needed.
    * `max_pages` (Optional): For endpoints that return lists (like timelines, followers, search), specify the number of pages to retrieve. Default to 5 pages if the user doesn't specify, but adjust based on their request (e.g., 'latest 10 tweets' might be 1 page, 'all followers' might need more than 5). Use the fallback default only if calculation is impossible.
    * **Data Dependencies:** How parameters get values from previous steps:
        * **Simple Dependency:** For simple dependencies (referencing a single value from a previous step), use the format `"$step<N>.<output_key>.<nested_key>..."` as the parameter value string. For accessing elements within a list, use numeric indices separated by dots (e.g., `"$step1.timeline.0.tweet_id"` to access the `tweet_id` of the first item in the `timeline` list from step 1). Do NOT use bracket notation like `[0]`. The execution engine will resolve this dot-notation path.
        * **List Dependency (IMPORTANT):** If a parameter needs multiple values extracted from a *list* in a previous step's result (e.g., getting all original author user IDs from retweets in a timeline):
            * Instead of a string value for the parameter, use a JSON object with the following structure:
                ```json
                "param_name_expecting_multiple_values": {{
                  "source_step": <N>,
                  "source_list_path": "path.to.the.list.in.stepN.result", // e.g., "timeline"
                  "extract_field": "field.to.extract.from.each.item", // e.g., "retweeted_tweet.author.rest_id"
                  "join_with": ","  // Optional: Specify separator (e.g., comma for screennames.php rest_ids). If omitted, the executor will receive a list. Ensure the correct format is generated for the target API.
                }}
                ```
            * **Example for `screennames.php` needing comma-separated `rest_ids` from retweets in a timeline:**
                ```json
                "params": {{
                   "rest_ids": {{
                      "source_step": 1,
                      "source_list_path": "timeline", // Assumes step 1 result has a 'timeline' list
                      // Use the CORRECT path based on actual API response for retweets:
                      "extract_field": "retweeted_tweet.author.rest_id",
                      "join_with": "," // Join the extracted IDs with a comma
                   }}
                }}
                ```
5.  **Output Format:** Respond ONLY with a single JSON object containing:
    * `response_type`: "CLARIFICATION", "PLAN", or "ERROR" (for internal planning issues).
    * `message_to_user`: (Optional) A message for the user (required for CLARIFICATION/ERROR, optional for PLAN status updates like "Okay, I will fetch...").
    * `api_plan`: (Required if `response_type` is "PLAN") The list of API call steps as described above.

**Current User Request:**
{user_query}

**Your JSON Response:**
"""

SUMMARIZER_SYSTEM_PROMPT_TEMPLATE = """
You are an AI assistant summarizing Twitter data retrieved via API calls.
The user asked the following question:
"{original_query}"

The following data was retrieved in sequence according to the plan:
{retrieved_data_summary}

Summarize the key findings from the retrieved data concisely and directly answer the user's original question. Focus on the most relevant information. Do not just list the data structures.
If the data indicates an error or that something wasn't found, reflect that in the summary.
"""