"""
GEMINI MODEL PROVIDER
"""
import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from .base import Base_LLM_Provider
from Stage1.config import GEMINI_MODEL, LLM_MAX_RETRIES, LLM_RETRY_DELAY



class Gemini_Provider(Base_LLM_Provider):
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        self.client = genai.Client(api_key=api_key)

        def generate(self, prompt: str) -> dict:
            last_error = None

            for attempt in range(LLM_MAX_RETRIES):
                try:
                    response = self.client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )

                    raw_text = response.text

                    if not raw_text:
                        raise RuntimeError("Gemini returned empty response")

                    # parsed = json.loads(raw_text)
                    # return parsed

                except APIError as e:
                    last_error = e

                    if e.code in (429, 503):
                        # linear
                        #time.sleep(LLM_RETRY_DELAY * (attempt + 1))

                        # exponential
                        time.sleep(LLM_RETRY_DELAY ** (attempt + 1))
                        continue

                    raise RuntimeError(f"Gemini API error: {e.message} (code: {e.code})")

                # except json.JSONDecodeError as e:
                #     raise RuntimeError(f"Gemini returned invalid JSON: {str(e)}")

            raise RuntimeError(f"Gemini API failed after {LLM_MAX_RETRIES} retries: {last_error}")

