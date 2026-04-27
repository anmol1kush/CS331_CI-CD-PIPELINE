"""
Bug Detector for Stage-1.

Classifies test execution results into bug categories
by comparing actual outputs against expected outputs.

Input:
    - results: list of dicts from test_executor
      (each has: status, output, error, runtime, test_id)
    - tests: list of test objects from LLM test generator
      (each has: strategy, method_name, input, expected_output)

Output:
    {
        "exceptions": [...],
        "failures": [...],
        "incorrect_outputs": [...]
    }

Classification logic:
    status == "exception"  → exceptions
    status == "timeout"    → failures
    status == "crash"      → failures
    status == "success" but output != expected_output → incorrect_outputs
    status == "success" and output == expected_output → pass (not recorded)

Maps to State buckets:
    exceptions → state.exceptions
    failures → state.failures (timeout + crash combined)
    incorrect_outputs → state.incorrect_outputs

Downstream consumer: Objective function (evaluate_state)
"""
from itertools import zip_longest

def detect_bugs(results, tests):
    exceptions = []
    failures = []
    incorrect_outputs = []

    for result, test in zip_longest(results, tests,fillvalue=None):
        if result is None:
            failures.append({
                "test_id": test.get("test_id", "unknown"),
                "error": "Tests was not executed — result missing",
                "error": "Tests was not executed — result missing",
                "status": "missing",
                "input": test.get("input"),
                "strategy": test.get("strategy"),
                "validation_confidence": test.get("validation_confidence", 1.0)
            })
            continue

        status = result.get("status")

        if status == "exception":
            exceptions.append({
                "test_id": result.get("test_id"),
                "error": result.get("error"),
                "input": test.get("input"),
                "strategy": test.get("strategy"),
                "validation_confidence": test.get("validation_confidence", 1.0)
            })

        elif status in ("timeout", "crash"):
            failures.append({
                "test_id": result.get("test_id"),
                "error": result.get("error"),
                "status": status,
                "input": test.get("input"),
                "strategy": test.get("strategy"),
                "validation_confidence": test.get("validation_confidence", 1.0)
            })

        elif status == "success":
            expected = test.get("expected_output")

            if expected is None:
                continue

            actual = result.get("output")
            mode = test.get("comparison_mode", "exact")
            mode = test.get("comparison_mode", "exact")

            if not compare_outputs(actual, expected):
                verdict = test.get("verdict")
                if verdict == "likely_hallucination":
                    continue

                incorrect_outputs.append({
                    "test_id": result.get("test_id"),
                    "input": test.get("input"),
                    "expected": expected,
                    "actual": actual,
                    "strategy": test.get("strategy"),
                    "comparison_mode": mode,
                    "validation_confidence": test.get("validation_confidence", 1.0),
                    "verdict": verdict
                })

    return {
        "exceptions": exceptions,
        "failures": failures,
        "incorrect_outputs": incorrect_outputs
    }

def normalize_for_comparison(value):
    if isinstance(value, list):
        normalized = [normalize_for_comparison(item) for item in value]
        try:
            return sorted(normalized)
        except TypeError:
            return normalized
    return value

def compare_outputs(actual, expected, comparison_mode="exact"):
    if actual == expected:
        return True

    if comparison_mode == "exact":
        return False

    if comparison_mode == "unordered":
        # outer order doesn't matter, inner order matters
        if isinstance(actual, list) and isinstance(expected, list):
            if len(actual) == len(expected):
                try:
                    return sorted(actual) == sorted(expected)
                except TypeError:
                    return False
        return False

    if comparison_mode == "unordered_nested":
        # both outer and inner order don't matter
        if isinstance(actual, list) and isinstance(expected, list):
            if len(actual) == len(expected):
                return normalize_for_comparison(actual) == normalize_for_comparison(expected)
        return False

    if comparison_mode == "float_tolerance":
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            return abs(actual - expected) < 1e-6
        return False

    return False