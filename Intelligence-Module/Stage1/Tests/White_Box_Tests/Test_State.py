"""
White box test: State
Tests construction, from_semantic_output, all mutation methods, to_dict
"""
from Stage1.Core.State import State

if __name__ == '__main__':

    # ===== from_semantic_output =====
    print("=== from_semantic_output ===")

    semantic = {
        "language": "python",
        "execution_model": "callable_method",
        "structural_features": {"function_count": 2},
        "normalized_code": "class Solution: pass"
    }
    state = State.from_semantic_output(semantic)
    print(f"  language: {state.language}")
    print(f"  execution_model: {state.execution_model}")
    print(f"  source_code: {state.source_code}")
    print(f"  structural_features: {state.structural_features}")

    semantic_none = {
        "language": "python",
        "execution_model": "script",
        "structural_features": None,
        "normalized_code": "x=1"
    }
    state = State.from_semantic_output(semantic_none)
    print(f"  None features → becomes: {state.structural_features}")

    semantic_no_code = {
        "language": "python",
        "execution_model": "script",
        "structural_features": {}
    }
    state = State.from_semantic_output(semantic_no_code)
    print(f"  Missing code → becomes: '{state.source_code}'")

    # ===== mutation methods =====
    print("\n=== Mutation Methods ===")

    state = State.from_semantic_output(semantic)

    state.add_generated_tests([{"input": [1]}, {"input": [2]}], "edge_case")
    print(f"  After add 2 tests: generated={len(state.generated_tests)}")

    state.add_generated_tests([{"input": [3]}], "branch")
    print(f"  After add 1 more: generated={len(state.generated_tests)}")

    print(f"  Strategy usage: {state.strategy_usage}")

    state.mark_tests_executed([{"input": [1]}, {"input": [2]}])
    print(f"  After mark 2 executed: executed={len(state.executed_tests)}")

    state.record_exceptions(["error1", "error2"])
    state.record_failures(["fail1"])
    state.record_incorrect_outputs(["wrong1", "wrong2", "wrong3"])
    print(f"  Exceptions: {len(state.exceptions)}")
    print(f"  Failures: {len(state.failures)}")
    print(f"  Incorrect: {len(state.incorrect_outputs)}")

    state.update_coverage(0.75, 0.85)
    print(f"  Coverage: line={state.line_coverage}, branch={state.branch_coverage}")

    state.all_executed_lines.update({1, 2, 3})
    state.all_executed_lines.update({3, 4, 5})
    print(f"  Cumulative lines: {sorted(state.all_executed_lines)}")

    state.increment_iteration()
    state.increment_iteration()
    print(f"  Iteration: {state.iteration}")

    state.stop()
    print(f"  Stop flag: {state.stop_flag}")

    # ===== to_dict completeness =====
    print("\n=== to_dict ===")
    d = state.to_dict()
    required_keys = [
        "language", "execution_model", "source_code",
        "structural_features", "generated_tests", "executed_tests",
        "strategy_usage", "failures", "exceptions", "incorrect_outputs",
        "line_coverage", "branch_coverage", "iteration", "stop_flag",
        "all_executed_lines"
    ]
    for key in required_keys:
        print(f"  '{key}' in to_dict: {key in d}")