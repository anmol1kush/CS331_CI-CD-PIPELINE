"""
White box test: Objective Function
Tests score computation with controlled state values
"""
from Stage1.Core.State import State
from Stage1.Core.Objective import evaluate_state
import math

if __name__ == '__main__':

    # ===== zero everything =====
    print("=== Score Computation ===")

    state = State("python", "callable_method", {"line_count": 10, "branching_factor": 2})
    state.source_code = ""
    state.line_coverage = 0.0
    state.branch_coverage = 0.0
    score = evaluate_state(state)
    print(f"  Zero everything: {score}")

    # ===== full coverage no bugs =====
    state.line_coverage = 1.0
    state.branch_coverage = 1.0
    score = evaluate_state(state)
    print(f"  Full coverage no bugs: {score}")

    # ===== zero coverage with bugs =====
    state.line_coverage = 0.0
    state.branch_coverage = 0.0
    state.exceptions = ["bug1", "bug2"]
    score = evaluate_state(state)
    expected = math.log(1 + 2)
    print(f"  No coverage 2 bugs: {score:.4f} (expected: {expected:.4f})")

    # ===== mixed coverage and bugs =====
    state.line_coverage = 0.8
    state.branch_coverage = 0.7
    state.exceptions = ["b1"]
    state.failures = ["b2"]
    state.incorrect_outputs = ["b3"]
    score = evaluate_state(state)
    wl = 10 / 12
    wb = 2 / 12
    coverage = wl * 0.8 + wb * 0.7
    bug = math.log(1 + 3)
    expected = coverage + bug
    print(f"  Mixed: {score:.4f} (expected: {expected:.4f})")

    # ===== weights computation =====
    print("\n=== Weight Computation ===")

    state = State("python", "callable_method", {"line_count": 0, "branching_factor": 0})
    state.source_code = ""
    state.line_coverage = 0.5
    state.branch_coverage = 0.5
    score = evaluate_state(state)
    print(f"  Zero line+branch count → equal weights: {score:.4f}")

    state = State("python", "callable_method", {"line_count": 100, "branching_factor": 0})
    state.source_code = ""
    state.line_coverage = 1.0
    state.branch_coverage = 0.0
    score = evaluate_state(state)
    print(f"  Zero branch count → line dominates: {score:.4f}")

    state = State("python", "callable_method", {"line_count": 0, "branching_factor": 100})
    state.source_code = ""
    state.line_coverage = 0.0
    state.branch_coverage = 1.0
    score = evaluate_state(state)
    print(f"  Zero line count → branch dominates: {score:.4f}")

    # ===== bug score scaling =====
    print("\n=== Bug Score Scaling ===")

    state = State("python", "callable_method", {"line_count": 10, "branching_factor": 2})
    state.source_code = ""
    state.line_coverage = 0.0
    state.branch_coverage = 0.0

    for num_bugs in [0, 1, 2, 5, 10, 20, 50]:
        state.exceptions = ["bug"] * num_bugs
        state.failures = []
        state.incorrect_outputs = []
        score = evaluate_state(state)
        print(f"  {num_bugs} bugs → score: {score:.4f} (expected: {math.log(1 + num_bugs):.4f})")