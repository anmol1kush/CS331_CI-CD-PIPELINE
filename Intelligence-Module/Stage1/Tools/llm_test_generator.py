"""
LLM-based Test Generator for Stage-1.

Generates test cases by prompting an LLM with the source code
and structural context from the Semantic Engine.

Responsibilities:
- Receive source code and structural features
- Identify the target function/method to test
  (for callable_method: the entry method inside class Solution)
  (for stdin_program: the expected stdin format)
  (for script: no target needed)
- Generate test inputs based on the selected strategy
  (edge_case, branch, adversarial, stress, constraint)
- Return structured test objects

Test object contract (callable_method):
{
    "strategy": str,
    "method_name": str,
    "input": list,
    "expected_output": any
}

Test object contract (stdin_program):
{
    "strategy": str,
    "method_name": None,
    "input": str,
    "expected_output": any
}

Test object contract (script):
{
    "strategy": str,
    "method_name": None,
    "input": None,
    "expected_output": any
}

NOTE:
The LLM is responsible for identifying the correct entry method.
test_executor.py validates the method exists but does not
perform method detection.
"""
import json
from Stage1.Providers.gemini_provider import Gemini_Provider
from config import MAX_TESTS_PER_CALL


class LLM_Test_Generator:
    def __init__(self):
        self.provider = Gemini_Provider()

    def generate_tests(
        self,
        source_code,
        execution_model,
        structural_features,
        strategy,
        existing_tests=None,
        previous_failures=None
    ):
        prompt = self.build_prompt(
            source_code,
            execution_model,
            structural_features,
            strategy,
            existing_tests,
            previous_failures
        )
        response = self.provider.generate(prompt)
        tests = self.parse_response(response, strategy)

        return tests

    def build_prompt(
        self,
        source_code,
        execution_model,
        structural_features,
        strategy,
        existing_tests,
        previous_failures
    ):

        prompt = f"""
You are an automated software testing system.
Given the following program, generate test cases.

Execution model: {execution_model}
Strategy: {strategy}
Structural features:
{json.dumps(structural_features, indent=2)}
Program source code:
--------------------
{source_code}
--------------------

Generate at most {MAX_TESTS_PER_CALL} test cases.
Each test must follow this JSON format:

[
  {{
    "strategy": "{strategy}",
    "method_name": "<function_name>",
    "input": <input_data>,
    "expected_output": <expected_output>
  }}
]

Rules:
- Return ONLY valid JSON
- Do not include explanations
- Ensure inputs respect typical constraints
- Include edge and adversarial cases
"""

        if existing_tests:
            prompt += f"\nExisting tests:\n{json.dumps(existing_tests, indent=2)}\n"

        if previous_failures:
            prompt += f"\nPrevious failures:\n{json.dumps(previous_failures, indent=2)}\n"

        return prompt

    def parse_response(self, response, strategy):
        try:
            data = json.loads(response)

        except json.JSONDecodeError:
            raise ValueError("LLM response is not valid JSON")

        normalized_tests = []

        for test in data:
            normalized_tests.append(
                {
                    "strategy": test.get("strategy", strategy),
                    "method_name": test.get("method_name"),
                    "input": test.get("input"),
                    "expected_output": test.get("expected_output")
                }
            )

        return normalized_tests
