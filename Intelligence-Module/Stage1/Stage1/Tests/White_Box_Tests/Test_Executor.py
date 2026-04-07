"""
White box test: Tests Executor
Tests each execution model, timeout handling, crash handling, tracing
"""
from Stage1.Tools.test_executor import run_tests

if __name__ == '__main__':

    # ===== callable_method execution =====
    print("=== Callable Method ===")

    source = "class Solution:\n    def add(self, a, b):\n        return a + b"

    tests = [{"method_name": "add", "input": [2, 3], "expected_output": 5, "comparison_mode": "exact"}]
    results, lines = run_tests(source, tests, "callable_method")
    print(f"  Normal: status={results[0]['status']}, output={results[0]['output']}")
    print(f"  Lines traced: {sorted(lines)}")

    tests = [{"method_name": None, "input": [1], "expected_output": 1, "comparison_mode": "exact"}]
    results, lines = run_tests(source, tests, "callable_method")
    print(f"  No method: status={results[0]['status']}, error={results[0]['error']}")

    tests = [{"method_name": "nonexistent", "input": [1], "expected_output": 1, "comparison_mode": "exact"}]
    results, lines = run_tests(source, tests, "callable_method")
    print(f"  Wrong method: status={results[0]['status']}")

    source_bad = "class Solution:\n    def crash(self):\n        return 1/0"
    tests = [{"method_name": "crash", "input": [], "expected_output": None, "comparison_mode": "exact"}]
    results, lines = run_tests(source_bad, tests, "callable_method")
    print(f"  Division by zero: status={results[0]['status']}, error={results[0]['error']}")

    # ===== timeout handling =====
    print("\n=== Timeout ===")

    source_infinite = "class Solution:\n    def loop(self):\n        while True: pass"
    tests = [{"method_name": "loop", "input": [], "expected_output": None, "comparison_mode": "exact"}]
    results, lines = run_tests(source_infinite, tests, "callable_method")
    print(f"  Infinite loop: status={results[0]['status']}")

    # ===== stdin_program execution =====
    print("\n=== Stdin Program ===")

    source_stdin = "n = int(input())\nprint(n * 2)"
    tests = [{"method_name": None, "input": "5", "expected_output": "10\n", "comparison_mode": "exact"}]
    results, lines = run_tests(source_stdin, tests, "stdin_program")
    print(f"  Stdin: status={results[0]['status']}, output='{results[0]['output']}'")
    print(f"  Lines traced: {sorted(lines)}")

    # ===== script execution =====
    print("\n=== Script ===")

    source_script = "x = 1 + 2\ny = x * 3"
    results, lines = run_tests(source_script, [], "script")
    print(f"  Script: status={results[0]['status']}")
    print(f"  Lines traced: {sorted(lines)}")

    # ===== multiple tests cumulative lines =====
    print("\n=== Cumulative Lines ===")

    source = "class Solution:\n    def check(self, n):\n        if n > 0:\n            return 'positive'\n        else:\n            return 'negative'"
    tests = [
        {"method_name": "check", "input": [5], "expected_output": "positive", "comparison_mode": "exact"},
        {"method_name": "check", "input": [-3], "expected_output": "negative", "comparison_mode": "exact"}
    ]
    results, lines = run_tests(source, tests, "callable_method")
    print(f"  Two tests lines: {sorted(lines)}")
    print(f"  Count: {len(lines)}")

    # ===== mixed success and failure =====
    print("\n=== Mixed Results ===")

    source = "class Solution:\n    def divide(self, a, b):\n        return a / b"
    tests = [
        {"method_name": "divide", "input": [10, 2], "expected_output": 5.0, "comparison_mode": "exact"},
        {"method_name": "divide", "input": [10, 0], "expected_output": None, "comparison_mode": "exact"},
        {"method_name": "divide", "input": [6, 3], "expected_output": 2.0, "comparison_mode": "exact"}
    ]
    results, lines = run_tests(source, tests, "callable_method")
    for r in results:
        print(f"  Tests {r['test_id']}: status={r['status']}")

    # ===== unsupported execution model =====
    print("\n=== Error Cases ===")
    try:
        run_tests("x=1", [], "unknown_model")
        print("  Unknown model: FAILED (should have raised)")
    except ValueError:
        print("  Unknown model raised: PASSED")