"""
Objective function for Stage-1.

Current design (incremental version):
O(S) = C(S) + B(S)
Where
C(S) = wl * line_coverage + wb * branch_coverage
wl = line_count / (line_count + branch_count)
wb = branch_count / (line_count + branch_count)

B(S) = log(1 + total_bugs)
total_bugs = exceptions + failures + incorrect_outputs

NOTE:
For the current iteration all bug types are treated equally.
In future iterations bug severity weights may be introduced.
"""
import math

def evaluate_state(state):
    features = state.structural_features

    line_count = features.get("line_count", 0)
    branch_count = features.get("branching_factor", 0)

    total_structure = line_count + branch_count

    if total_structure == 0:
        wl = 0.5
        wb = 0.5
    else:
        wl = line_count / total_structure
        wb = branch_count / total_structure

    line_cov = state.line_coverage
    branch_cov = state.branch_coverage

    coverage_score = wl * line_cov + wb * branch_cov

    exceptions = len(state.exceptions)
    failures = len(state.failures)
    incorrect_outputs = len(state.incorrect_outputs)

    total_bugs = exceptions + failures + incorrect_outputs
    bug_score = math.log(1 + total_bugs)

    objective_value = coverage_score + bug_score
    return objective_value