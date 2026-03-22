"""
White box test: Bug Detector
Tests classification logic, comparison modes, zip_longest handling
"""
from Stage1.Tools.bug_detector import detect_bugs, compare_outputs, normalize_for_comparison

if __name__ == '__main__':

    # ===== classification by status =====
    print("=== Bug Classification ===")

    results = [
        {"status": "success", "output": 5, "test_id": 0},
        {"status": "exception", "output": None, "error": "ZeroDivision", "test_id": 1},
        {"status": "timeout", "output": None, "error": "exceeded 10s", "test_id": 2},
        {"status": "crash", "output": None, "error": "child died", "test_id": 3},
        {"status": "success", "output": 10, "test_id": 4}
    ]
    tests = [
        {"input": [5], "expected_output": 5, "strategy": "edge", "comparison_mode": "exact"},
        {"input": [0], "expected_output": None, "strategy": "edge", "comparison_mode": "exact"},
        {"input": [99], "expected_output": None, "strategy": "stress", "comparison_mode": "exact"},
        {"input": [1], "expected_output": None, "strategy": "adv", "comparison_mode": "exact"},
        {"input": [5], "expected_output": 99, "strategy": "branch", "comparison_mode": "exact"}
    ]

    bugs = detect_bugs(results, tests)
    print(f"  Exceptions: {len(bugs['exceptions'])}")
    print(f"  Failures: {len(bugs['failures'])}")
    print(f"  Incorrect: {len(bugs['incorrect_outputs'])}")

    # ===== None expected_output skipped =====
    print("\n=== None Expected Output ===")

    results = [{"status": "success", "output": 42, "test_id": 0}]
    tests = [{"input": [1], "expected_output": None, "strategy": "edge", "comparison_mode": "exact"}]
    bugs = detect_bugs(results, tests)
    print(f"  None expected → incorrect count: {len(bugs['incorrect_outputs'])}")

    # ===== zip_longest — more tests than results =====
    print("\n=== Unequal Lengths ===")

    results = [{"status": "success", "output": 1, "test_id": 0}]
    tests = [
        {"input": [1], "expected_output": 1, "strategy": "edge", "comparison_mode": "exact"},
        {"input": [2], "expected_output": 2, "strategy": "edge", "comparison_mode": "exact"},
        {"input": [3], "expected_output": 3, "strategy": "edge", "comparison_mode": "exact"}
    ]
    bugs = detect_bugs(results, tests)
    print(f"  3 tests, 1 result → failures: {len(bugs['failures'])}")

    # ===== empty inputs =====
    print("\n=== Empty Inputs ===")

    bugs = detect_bugs([], [])
    print(f"  Both empty → total: {len(bugs['exceptions']) + len(bugs['failures']) + len(bugs['incorrect_outputs'])}")

    bugs = detect_bugs([], [{"input": [1], "expected_output": 1, "strategy": "edge", "comparison_mode": "exact"}])
    print(f"  Empty results → failures: {len(bugs['failures'])}")

    # ===== compare_outputs — all modes =====
    print("\n=== Compare Outputs — exact ===")

    print(f"  exact match: {compare_outputs(5, 5, 'exact')}")
    print(f"  exact mismatch: {compare_outputs(5, 6, 'exact')}")
    print(f"  exact list order: {compare_outputs([1,2], [2,1], 'exact')}")

    print("\n=== Compare Outputs — unordered ===")

    print(f"  unordered match: {compare_outputs([1,2], [2,1], 'unordered')}")
    print(f"  unordered diff: {compare_outputs([1,2], [3,4], 'unordered')}")
    print(f"  unordered diff len: {compare_outputs([1,2], [1,2,3], 'unordered')}")

    print("\n=== Compare Outputs — unordered_nested ===")

    print(f"  nested outer reorder: {compare_outputs([[1,2],[3,4]], [[3,4],[1,2]], 'unordered_nested')}")
    print(f"  nested inner reorder: {compare_outputs([[2,1],[4,3]], [[3,4],[1,2]], 'unordered_nested')}")
    print(f"  nested different: {compare_outputs([[1,2],[3,4]], [[5,6],[7,8]], 'unordered_nested')}")
    print(f"  threeSum case: {compare_outputs([[-1,-1,2],[-1,0,1]], [[-1,0,1],[-1,-1,2]], 'unordered_nested')}")

    print("\n=== Compare Outputs — float_tolerance ===")

    print(f"  float close: {compare_outputs(2.50000001, 2.5, 'float_tolerance')}")
    print(f"  float far: {compare_outputs(2.6, 2.5, 'float_tolerance')}")
    print(f"  int vs float: {compare_outputs(5, 5.0, 'float_tolerance')}")

    print("\n=== Compare Outputs — default ===")

    print(f"  no mode specified: {compare_outputs(5, 5)}")
    print(f"  unknown mode: {compare_outputs(5, 5, 'unknown')}")

    # ===== normalize_for_comparison =====
    print("\n=== Normalize ===")

    result = normalize_for_comparison([[2,1],[4,3]])
    print(f"  [[2,1],[4,3]] → {result}")

    result = normalize_for_comparison([3, 1, 2])
    print(f"  [3,1,2] → {result}")

    result = normalize_for_comparison(5)
    print(f"  5 → {result}")

    result = normalize_for_comparison([[[3,1],[2,4]],[[6,5]]])
    print(f"  3-deep nested → {result}")