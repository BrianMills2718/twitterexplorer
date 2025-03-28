# Twitter API Streamlit UI

A Streamlit interface for interacting with Twitter data via the RapidAPI Twitter API. This app leverages Google's Gemini AI to interpret natural language queries, plan API call sequences, and present the results in a user-friendly format.

## Features

- Natural language query processing using Gemini AI
- Structured API call planning and execution
- Session-based conversation history
- Summarized results tailored to user queries

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/twitter-api-streamlit-ui.git
   cd twitter-api-streamlit-ui
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a Streamlit secrets file:
   
   Create a file at `.streamlit/secrets.toml` with the following contents:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   RAPIDAPI_KEY = "your-rapidapi-key"
   ```

4. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## API Keys

You'll need:
- Google Gemini API key - Get it from [Google AI Studio](https://ai.google.dev/)
- RapidAPI Twitter API key - Subscribe to [Twitter API on RapidAPI](https://rapidapi.com/Glavier/api/twitter-api45)

## Project Structure

- `app.py` - Main Streamlit application
- `llm_handler.py` - Gemini AI integration
- `api_client.py` - Twitter API client
- `config.py` - Configuration settings
- `state_manager.py` - Session state management
- `merged_endpoints.json` - API endpoint specifications
- `ontology_synonyms.py` - Mapping between common terms and API parameters

## License

MIT 