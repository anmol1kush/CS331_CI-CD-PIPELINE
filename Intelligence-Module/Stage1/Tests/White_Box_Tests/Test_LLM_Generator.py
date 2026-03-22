"""
White box test: LLM Tests Generator
Tests prompt building, response parsing, validation per execution model
NOTE: Does NOT make actual API calls — tests internal logic only
"""
from Stage1.Tools.llm_test_generator import LLM_Test_Generator
import json

if __name__ == '__main__':

    # ===== prompt building — callable_method =====
    print("=== Prompt Building — callable_method ===")

    gen = LLM_Test_Generator()

    prompt = gen.build_prompt(
        source_code="class Solution:\n    def add(self, a, b):\n        return a + b",
        execution_model="callable_method",
        structural_features={"function_count": 1, "branching_factor": 0},
        strategy="edge_case",
        existing_tests=None,
        previous_failures=None
    )
    print(f"  Contains source code: {'add' in prompt}")
    print(f"  Contains strategy: {'edge_case' in prompt}")
    print(f"  Contains method_name instruction: {'method_name' in prompt}")
    print(f"  Contains callable format: {'class Solution' in prompt}")
    print(f"  Contains comparison_mode: {'comparison_mode' in prompt}")

    # ===== prompt building — stdin_program =====
    print("\n=== Prompt Building — stdin_program ===")

    prompt = gen.build_prompt(
        source_code="n = int(input())\nprint(n*2)",
        execution_model="stdin_program",
        structural_features={"function_count": 0},
        strategy="branch",
        existing_tests=None,
        previous_failures=None
    )
    print(f"  Contains null method_name: {'null' in prompt}")
    print(f"  Contains stdin instruction: {'stdin' in prompt.lower() or 'input' in prompt.lower()}")

    # ===== prompt building — script =====
    print("\n=== Prompt Building — script ===")

    prompt = gen.build_prompt(
        source_code="x = 1 + 2",
        execution_model="script",
        structural_features={"function_count": 0},
        strategy="edge_case",
        existing_tests=None,
        previous_failures=None
    )
    print(f"  Contains null for script: {'null' in prompt}")

    # ===== prompt with existing tests =====
    print("\n=== Prompt With Context ===")

    existing = [{"input": [1, 2], "method_name": "add"}]
    failures = [{"error": "ZeroDivision", "input": [1, 0]}]

    prompt = gen.build_prompt(
        source_code="class Solution:\n    def add(self, a, b): pass",
        execution_model="callable_method",
        structural_features={},
        strategy="adversarial",
        existing_tests=existing,
        previous_failures=failures
    )
    print(f"  Contains existing tests: {'Existing tests' in prompt}")
    print(f"  Contains previous failures: {'Previous failures' in prompt}")

    # ===== parse_response — valid callable =====
    print("\n=== Parse Response — valid callable ===")

    response = json.dumps([
        {
            "strategy": "edge_case",
            "method_name": "add",
            "input": [1, 2],
            "expected_output": 3,
            "comparison_mode": "exact"
        },
        {
            "strategy": "edge_case",
            "method_name": "add",
            "input": [0, 0],
            "expected_output": 0,
            "comparison_mode": "exact"
        }
    ])

    tests = gen.parse_response(response, "edge_case", "callable_method")
    print(f"  Parsed count: {len(tests)}")
    print(f"  Has method_name: {tests[0].get('method_name') == 'add'}")
    print(f"  Has input: {tests[0].get('input') == [1, 2]}")
    print(f"  Has expected: {tests[0].get('expected_output') == 3}")
    print(f"  Has mode: {tests[0].get('comparison_mode') == 'exact'}")

    # ===== parse_response — invalid JSON =====
    print("\n=== Parse Response — invalid JSON ===")

    try:
        gen.parse_response("not json", "edge_case", "callable_method")
        print("  Invalid JSON accepted: FAILED")
    except ValueError:
        print("  Invalid JSON rejected: PASSED")

    # ===== parse_response — not a list =====
    print("\n=== Parse Response — not a list ===")

    try:
        gen.parse_response('{"key": "value"}', "edge_case", "callable_method")
        print("  Dict response accepted: FAILED")
    except ValueError:
        print("  Dict response rejected: PASSED")

    # ===== validate_test — callable_method =====
    print("\n=== Validate — callable_method ===")

    valid = {"method_name": "add", "input": [1, 2], "expected_output": 3}
    print(f"  Valid callable: {gen.validate_test(valid, 'callable_method')}")

    no_method = {"input": [1, 2], "expected_output": 3}
    print(f"  Missing method: {gen.validate_test(no_method, 'callable_method')}")

    null_method = {"method_name": None, "input": [1, 2], "expected_output": 3}
    print(f"  Null method: {gen.validate_test(null_method, 'callable_method')}")

    wrong_input = {"method_name": "add", "input": "not a list", "expected_output": 3}
    print(f"  String input: {gen.validate_test(wrong_input, 'callable_method')}")

    # ===== validate_test — stdin_program =====
    print("\n=== Validate — stdin_program ===")

    valid_stdin = {"method_name": None, "input": "5\n3", "expected_output": "8"}
    print(f"  Valid stdin: {gen.validate_test(valid_stdin, 'stdin_program')}")

    has_method = {"method_name": "solve", "input": "5", "expected_output": "10"}
    print(f"  Has method: {gen.validate_test(has_method, 'stdin_program')}")

    wrong_type = {"method_name": None, "input": [5], "expected_output": "10"}
    print(f"  List input: {gen.validate_test(wrong_type, 'stdin_program')}")

    # ===== validate_test — script =====
    print("\n=== Validate — script ===")

    valid_script = {"method_name": None, "input": None, "expected_output": None}
    print(f"  Valid script: {gen.validate_test(valid_script, 'script')}")

    has_method = {"method_name": "run", "input": None, "expected_output": None}
    print(f"  Has method: {gen.validate_test(has_method, 'script')}")

    # ===== parse_response — filters invalid tests =====
    print("\n=== Parse — Filters Invalid ===")

    response = json.dumps([
        {"strategy": "edge", "method_name": "add", "input": [1], "expected_output": 1, "comparison_mode": "exact"},
        {"strategy": "edge", "method_name": None, "input": [1], "expected_output": 1, "comparison_mode": "exact"},
        {"strategy": "edge", "method_name": "add", "input": "wrong", "expected_output": 1, "comparison_mode": "exact"},
        {"strategy": "edge", "method_name": "add", "input": [2], "expected_output": 2, "comparison_mode": "exact"}
    ])

    tests = gen.parse_response(response, "edge_case", "callable_method")
    print(f"  4 input, {len(tests)} valid (expected: 2)")

    # ===== comparison_mode defaults to exact =====
    print("\n=== Comparison Mode Default ===")

    response = json.dumps([
        {"strategy": "edge", "method_name": "add", "input": [1], "expected_output": 1}
    ])
    tests = gen.parse_response(response, "edge_case", "callable_method")
    print(f"  Missing mode → defaults to: {tests[0].get('comparison_mode')}")