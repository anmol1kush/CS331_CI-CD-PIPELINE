"""
GEMINI MODEL PROVIDER
"""
import os
import time
import random
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

    def generate(self, prompt: str, temperature: float = None) -> str:
        last_error = None

        for attempt in range(LLM_MAX_RETRIES):
            try:
                print(f"    [Gemini] API call attempt {attempt + 1}...")

                gen_config = {"response_mime_type": "application/json"}
                if temperature is not None:
                    gen_config["temperature"] = temperature

                response = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(**gen_config)
                )

                try:
                    raw_text = response.text
                except Exception as e:
                    raise RuntimeError(f"Gemini response has no text: {str(e)}")

                if not raw_text:
                    raise RuntimeError("Gemini returned empty response")

                print(f"    [Gemini] Response received ({len(raw_text)} chars)")
                return raw_text

            except APIError as e:
                last_error = e
                print(f"    [Gemini] API error: {e.code} — retrying...")

                if e.code in (429, 503):
                    wait = LLM_RETRY_DELAY ** (attempt + 1)
                    jitter = random.uniform(0, wait * 0.3)
                    total_wait = wait + jitter
                    print(f"    [Gemini] Waiting {total_wait:.1f}s before retry (attempt {attempt + 1}/{LLM_MAX_RETRIES})")
                    time.sleep(total_wait)
                    continue

                raise RuntimeError(f"Gemini API error: {e.message} (code: {e.code})")

            except RuntimeError:
                raise

            except Exception as e:
                print(f"    [Gemini] Unexpected error: {type(e).__name__}: {str(e)}")
                raise RuntimeError(f"Gemini unexpected error: {str(e)}")

        raise RuntimeError(f"Gemini API failed after {LLM_MAX_RETRIES} retries: {last_error}")