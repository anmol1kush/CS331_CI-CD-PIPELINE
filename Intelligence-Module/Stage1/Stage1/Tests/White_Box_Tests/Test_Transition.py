"""
White box test: Transition
Tests apply_action, generate_tests, run_test_suite, cumulative coverage, test filtering
"""
from Stage1.Core.State import State
from Stage1.Core.Actions import Action, Action_Type, Test_Strategy
from Stage1.Core.Transition import apply_action, run_test_suite

if __name__ == '__main__':
    semantic = {
        "language": "python",
        "execution_model": "callable_method",
        "structural_features": {"line_count": 7, "branching_factor": 1},
        "normalized_code": "class Solution:\n    def add(self, a, b):\n        if a > 0:\n            return a + b\n        return b"
    }

    # ===== apply_action — GENERATE_TESTS =====
    print("=== apply_action — GENERATE_TESTS ===")

    state = State.from_semantic_output(semantic)
    action = Action(action_type=Action_Type.GENERATE_TESTS, strategy=Test_Strategy.EDGE_CASE)
    apply_action(state, action)
    print(f"  After GENERATE_TESTS: iteration={state.iteration}")
    print(f"  Generated tests: {len(state.generated_tests)}")
    print(f"  Executed tests: {len(state.executed_tests)}")

    # ===== apply_action — STOP =====
    print("\n=== apply_action — STOP ===")

    state = State.from_semantic_output(semantic)
    action = Action(action_type=Action_Type.STOP)
    apply_action(state, action)
    print(f"  After STOP: stop_flag={state.stop_flag}")
    print(f"  Iteration incremented: {state.iteration}")

    # ===== iteration increments each action =====
    print("\n=== Iteration Counting ===")

    state = State.from_semantic_output(semantic)
    action = Action(action_type=Action_Type.GENERATE_TESTS, strategy=Test_Strategy.EDGE_CASE)
    apply_action(state, action)
    apply_action(state, action)
    apply_action(state, action)
    print(f"  After 3 actions: iteration={state.iteration}")

    # ===== run_test_suite — empty pending =====
    print("\n=== run_test_suite — empty pending ===")

    state = State.from_semantic_output(semantic)
    state.generated_tests = [{"input": [1, 2], "method_name": "add", "expected_output": 3, "comparison_mode": "exact"}]
    state.executed_tests = [{"input": [1, 2], "method_name": "add", "expected_output": 3, "comparison_mode": "exact"}]
    coverage_before = state.line_coverage
    run_test_suite(state)
    print(f"  No pending tests: coverage unchanged={state.line_coverage == coverage_before}")

    # ===== run_test_suite — cumulative coverage =====
    print("\n=== Cumulative Coverage ===")

    state = State.from_semantic_output(semantic)

    state.generated_tests = [
        {"input": [5, 3], "method_name": "add", "expected_output": 8, "comparison_mode": "exact"}
    ]
    run_test_suite(state)
    lines_after_first = len(state.all_executed_lines)
    coverage_after_first = state.line_coverage
    print(f"  After first test suite: lines={lines_after_first}, coverage={coverage_after_first:.2f}")

    state.generated_tests.append(
        {"input": [-1, 3], "method_name": "add", "expected_output": 3, "comparison_mode": "exact"}
    )
    run_test_suite(state)
    lines_after_second = len(state.all_executed_lines)
    coverage_after_second = state.line_coverage
    print(f"  After second test suite: lines={lines_after_second}, coverage={coverage_after_second:.2f}")
    print(f"  Lines grew: {lines_after_second >= lines_after_first}")
    print(f"  Coverage grew: {coverage_after_second >= coverage_after_first}")

    # ===== run_test_suite — index-based filtering =====
    print("\n=== Index-Based Filtering ===")

    state = State.from_semantic_output(semantic)
    test1 = {"input": [1, 2], "method_name": "add", "expected_output": 3, "comparison_mode": "exact"}
    test2 = {"input": [5, 3], "method_name": "add", "expected_output": 8, "comparison_mode": "exact"}

    state.generated_tests = [test1]
    run_test_suite(state)
    executed_after_first = len(state.executed_tests)
    print(f"  After first batch: executed={executed_after_first}")

    state.generated_tests.append(test2)
    run_test_suite(state)
    executed_after_second = len(state.executed_tests)
    print(f"  After second batch: executed={executed_after_second}")
    print(f"  Only new test executed: {executed_after_second == executed_after_first + 1}")

    # ===== run_test_suite — bugs recorded =====
    print("\n=== Bug Recording ===")

    state = State.from_semantic_output(semantic)
    state.generated_tests = [
        {"input": [1, 2], "method_name": "add", "expected_output": 999, "comparison_mode": "exact"}
    ]
    run_test_suite(state)
    total_bugs = len(state.exceptions) + len(state.failures) + len(state.incorrect_outputs)
    print(f"  Wrong expected output: bugs={total_bugs}")

    # ===== run_test_suite — exception handling =====
    print("\n=== Exception in Tests ===")

    semantic_bad = {
        "language": "python",
        "execution_model": "callable_method",
        "structural_features": {"line_count": 3, "branching_factor": 0},
        "normalized_code": "class Solution:\n    def crash(self):\n        return 1/0"
    }
    state = State.from_semantic_output(semantic_bad)
    state.generated_tests = [
        {"input": [], "method_name": "crash", "expected_output": None, "comparison_mode": "exact"}
    ]
    run_test_suite(state)
    print(f"  Exception recorded: {len(state.exceptions)}")