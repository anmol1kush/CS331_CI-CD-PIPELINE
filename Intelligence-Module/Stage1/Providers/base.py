from abc import ABC, abstractmethod
from typing import Dict


class Base_LLM_Provider(ABC):
    """
    Base interface for all LLM providers.
    Ensures uniform behavior across Gemini, OpenAI, Claude, etc.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Accepts a fully formatted prompt string.

        Must:
        - Return the raw response string from the LLM
        - Raise an exception if generation fails
        - JSON parsing is handled by the caller (llm_test_generator)
        """
        pass