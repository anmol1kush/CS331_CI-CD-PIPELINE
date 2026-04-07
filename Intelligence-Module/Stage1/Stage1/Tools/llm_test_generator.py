"""
LLM-based Tests Generator for Stage-1.

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

Tests object contract (callable_method):
{
    "strategy": str,
    "method_name": str,
    "input": list,
    "expected_output": any
}

Tests object contract (stdin_program):
{
    "strategy": str,
    "method_name": None,
    "input": str,
    "expected_output": any
}

Tests object contract (script):
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

"""
-> STRESS = "stress"
-> CONSTRAINT = "constraint"

the abv to be kept at hold as we req confirmation on the ip type to Intelligent Module
(Source Code only
or Source + Constraint File)
"""
import json
from Stage1.Providers.gemini_provider import Gemini_Provider
from Stage1.config import MAX_TESTS_PER_CALL, USER_CONTEXT_MAX_LENGTH



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
            previous_failures=None,
            user_context=None
    ):
        prompt = self.build_prompt(
            source_code,
            execution_model,
            structural_features,
            strategy,
            existing_tests,
            previous_failures,
            user_context
        )
        response = self.provider.generate(prompt)
        tests = self.parse_response(response, strategy, execution_model)


        return tests

    def build_prompt(
            self,
            source_code,
            execution_model,
            structural_features,
            strategy,
            existing_tests,
            previous_failures,
            user_context=None
    ):

        format_block = self.get_format_block(execution_model, strategy)
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
{format_block}

Comparison mode rules:
- "exact": output must match exactly (default for most problems)
- "unordered": list output where outer order does not matter (e.g., twoSum returns [0,1] or [1,0])
- "unordered_nested": nested list where both inner and outer order do not matter (e.g., threeSum, subsets)
- "float_tolerance": numeric output where minor floating point difference is acceptable (e.g., division, averages)

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

        if user_context:
            if len(user_context) > USER_CONTEXT_MAX_LENGTH:
                user_context = user_context[:USER_CONTEXT_MAX_LENGTH]
                print(f"    [LLM Generator] User context truncated to {USER_CONTEXT_MAX_LENGTH} chars")

            prompt += f"""
        Additional context from the developer:
        \"{user_context}\"
        Use this to guide which aspects of the code to focus your tests on.
        """

        return prompt

    def get_format_block(self, execution_model, strategy):
        if execution_model == "callable_method":
            return f"""
    Each test must follow this JSON format:
    [
      {{
        "strategy": "{strategy}",
        "method_name": "<the public method to test inside class Solution>",
        "input": [<arg1>, <arg2>, ...],
        "expected_output": <expected_output>,
        "comparison_mode": "<exact | unordered | unordered_nested | float_tolerance>"
      }}
    ]
    - "method_name" must be a valid method name from class Solution
    - "input" must be a list of arguments matching the method signature
    """

        elif execution_model == "stdin_program":
            return f"""
    Each test must follow this JSON format:
    [
      {{
        "strategy": "{strategy}",
        "method_name": null,
        "input": "<simulated stdin as a single string with newlines>",
        "expected_output": "<expected stdout as a string>",
        "comparison_mode": "<exact | unordered | unordered_nested | float_tolerance>"
      }}
    ]
    - "method_name" must always be null for stdin programs
    - "input" must be a string simulating what the user would type, with newlines separating inputs
    """

        elif execution_model == "script":
            return f"""
    Each test must follow this JSON format:
    [
      {{
        "strategy": "{strategy}",
        "method_name": null,
        "input": null,
        "expected_output": null,
        "comparison_mode": "exact"
      }}
    ]
    - "method_name" and "input" must always be null for scripts
    """

        else:
            raise ValueError(f"Unsupported execution model: {execution_model}")

    def parse_response(self, response, strategy,execution_model):
        try:
            data = json.loads(response)

        except json.JSONDecodeError:
            raise ValueError("LLM response is not valid JSON")

        if not isinstance(data, list):
            raise ValueError("LLM response is not a JSON list")

        normalized_tests = []

        for test in data:
            if not isinstance(test, dict):
                continue

            if not self.validate_test(test,execution_model):
                continue

            normalized_tests.append(
                {
                    "strategy": test.get("strategy", strategy),
                    "method_name": test.get("method_name"),
                    "input": test.get("input"),
                    "expected_output": test.get("expected_output"),
                    "comparison_mode": test.get("comparison_mode", "exact")
                }
            )

        return normalized_tests

    def validate_test(self, test, execution_model):
        if execution_model == "callable_method":
            method_name = test.get("method_name")
            if not isinstance(method_name, str) or not method_name:
                return False
            if not isinstance(test.get("input"), list):
                return False

        elif execution_model == "stdin_program":
            if test.get("method_name") is not None:
                return False
            if not isinstance(test.get("input"), str):
                return False

        elif execution_model == "script":
            if test.get("method_name") is not None:
                return False

        return True

