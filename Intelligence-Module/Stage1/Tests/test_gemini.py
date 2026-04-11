import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=api_key,
    http_options={"api_version": "v1beta"}
)

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Say hello in one short sentence. What is the real madrid position in la liga table in 2026 campaign? and in 2025?",
    config={
        'tools': [{'google_search': {}}]}
)

print(response.text)