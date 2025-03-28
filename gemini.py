from google import genai

# Your provided API key
api_key = 'AIzaSyAGjt6hCpOWYbt24T-mpb6HbNSR6s-Vfw8'

# Initialize the Gemini client
client = genai.Client(api_key=api_key)

# Define your prompt
prompt = "relevant prompt goes here"

# Generate content using the Gemini 2.0 Flash model
response = client.models.generate_content(
    #model="gemini-2.0-flash",
    model= "gemini-2.5-pro-exp-03-25",
    contents=prompt,
)

# Output the response
print(response.text)