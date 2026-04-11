import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("Loaded key:", api_key[:10] if api_key else "NOT FOUND")