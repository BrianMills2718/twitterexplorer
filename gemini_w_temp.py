from google import genai
from google.genai import types

client = genai.Client(api_key='AIzaSyAGjt6hCpOWYbt24T-mpb6HbNSR6s-Vfw8')

response = client.models.generate_content(
    #model="gemini-2.0-flash",
    model="gemini-2.5-pro-exp-03-25",
    contents=["Explain how AI works"],
    config=types.GenerateContentConfig(
        #max_output_tokens=500,
        temperature=0.05
    )
)
print(response.text)