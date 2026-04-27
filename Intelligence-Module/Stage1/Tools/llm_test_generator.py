"""
LLM-based Tests Generator for Stage-1.
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
Tests object contract (callable_method):
{
    "strategy": str,
    "method_name": str,
    "input": list,
    "expected_output": any
}

Tests object contract (stdin_program):
Tests object contract (stdin_program):
{
    "strategy": str,
    "method_name": None,
    "input": str,
    "expected_output": any
}

Tests object contract (script):
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
            user_context=None,
            iteration=0,
            compressed_source=None,
            cluster_representatives=None,
            language="python"
    ):
        prompt = self.build_prompt(
            source_code,
            execution_model,
            structural_features,
            strategy,
            existing_tests,
            previous_failures,
            user_context,
            iteration,
            compressed_source,
            cluster_representatives,
            language
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
            user_context=None,
            iteration=0,
            compressed_source=None,
            cluster_representatives=None,
            language="python"
    ):

        format_block = self.get_format_block(execution_model, strategy, language)

        # Iteration 0: full source code
        # Iteration 1+: compressed representation
        if iteration == 0 or compressed_source is None:
            code_section = f"""Program source code:
--------------------
{source_code}
--------------------"""
        else:
            code_section = f"""Program structure (compressed):
--------------------
{compressed_source}
--------------------"""

        prompt = f"""
You are an automated software testing system.
Given the following program, generate test cases.

Language: {language}
Execution model: {execution_model}
Strategy: {strategy}
{self._language_conventions(language)}
{code_section}

Generate at most {MAX_TESTS_PER_CALL} test cases.
Each test must follow this JSON format:
{format_block}

Comparison mode rules:
- "exact": output must match exactly (default for most problems)
- "unordered": list output where outer order does not matter (e.g., twoSum returns [0,1] or [1,0])
- "unordered_nested": nested list where both inner and outer order do not matter (e.g., threeSum, subsets)
- "float_tolerance": numeric output where minor floating point difference is acceptable (e.g., division, averages)
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

        # Test history: cluster representatives (iteration 1+) or raw tests (iteration 0)
        if iteration > 0 and cluster_representatives:
            prompt += f"\nExisting tests (representative samples):\n{json.dumps(cluster_representatives, indent=2, default=str)}\n"
            prompt += "Note: above tests are representatives from clustered test history. Generate tests that cover DIFFERENT regions and behaviors.\n"
        elif existing_tests:
            prompt += f"\nExisting tests:\n{json.dumps(existing_tests, indent=2)}\n"

        if previous_failures:
            prompt += f"\nPrevious failures:\n{json.dumps(previous_failures, indent=2)}\n"

        # User context only at iteration 0 (already embedded in compressed source at iteration 1+)
        if iteration == 0 and user_context:
            if len(user_context) > USER_CONTEXT_MAX_LENGTH:
                user_context = user_context[:USER_CONTEXT_MAX_LENGTH]
                print(f"    [LLM Generator] User context truncated to {USER_CONTEXT_MAX_LENGTH} chars")

            prompt += f"""
        Additional context from the developer:
        \"{user_context}\"
        Use this to guide which aspects of the code to focus your tests on.
        """

        return prompt

    def get_format_block(self, execution_model, strategy, language="python"):
        if execution_model == "callable_method":
            method_hint = self._callable_method_hint(language)
            return f"""
    Each test must follow this JSON format:
    [
      {{
        "strategy": "{strategy}",
        "method_name": "<the public method/function to test>",
        "input": [<arg1>, <arg2>, ...],
        "expected_output": <expected_output>,
        "comparison_mode": "<exact | unordered | unordered_nested | float_tolerance>"
      }}
    ]
    {method_hint}
    - "input" must be a list of arguments matching the method/function signature
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

    def _callable_method_hint(self, language):
        """Language-specific hints for callable_method test format."""
        if language == "python":
            return '- "method_name" must be a valid method name from class Solution'
        elif language in ("javascript", "typescript"):
            return ('- "method_name" must be a valid exported function name or method from the exported class\n'
                    '- For module.exports/export default, use the primary function name')
        elif language == "java":
            return ('- "method_name" must be a valid public method from the Solution class\n'
                    '- Input types must match Java method signature (int, String, int[], etc.)')
        elif language in ("c", "cpp"):
            return ('- "method_name" must be a valid function name defined in the source\n'
                    '- Input types must match C/C++ function parameter types')
        return '- "method_name" must be a valid callable from the source'

    def _language_conventions(self, language):
        """Language-specific conventions block for the prompt."""
        if language == "python":
            return """Language conventions:
- Entry point is typically a method inside class Solution
- For stdin programs, input() reads from stdin
- Use Python-native types in test inputs (list, dict, str, int, float, bool, None)"""

        elif language in ("javascript", "typescript"):
            return """Language conventions:
- Entry point is typically an exported function (module.exports or export default)
- For stdin programs, process.stdin or readline is used
- Use JSON-compatible types in test inputs (array, object, string, number, boolean, null)
- Arrays use 0-based indexing"""

        elif language == "java":
            return """Language conventions:
- Entry point is typically a public method in the Solution class
- For stdin programs, Scanner or BufferedReader reads from System.in
- Use Java-compatible types: int, long, double, String, int[], List<Integer>, etc.
- Arrays use 0-based indexing"""

        elif language in ("c", "cpp"):
            return """Language conventions:
- Entry point is typically a function (not inside a class for C)
- For stdin programs, scanf/fgets reads from stdin
- Use C-compatible types: int, float, double, char*, arrays
- Arrays use 0-based indexing
- Strings are null-terminated char arrays"""

        return ""

    def parse_response(self, response, strategy,execution_model):
        try:
            data = json.loads(response)

        except json.JSONDecodeError:
            raise ValueError("LLM response is not valid JSON")

        if not isinstance(data, list):
            raise ValueError("LLM response is not a JSON list")

        if not isinstance(data, list):
            raise ValueError("LLM response is not a JSON list")

        normalized_tests = []

        for test in data:
            if not isinstance(test, dict):
                continue

            if not self.validate_test(test,execution_model):
                continue

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

