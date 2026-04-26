import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is the capital of France? Just say the city name.",
    config=types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=50,
    ),
)
print(f"✅ Response: {response.text}")