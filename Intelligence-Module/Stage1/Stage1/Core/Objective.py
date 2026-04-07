"""
B(S) = log(1 + Σ validation_confidence_i)
Where validation_confidence_i is the Bayesian posterior confidence
for each detected bug, derived from triangulation verification.

Confidence values:
    O1 (all agree, pass):       0.998 — not a bug, never reaches here
    O2 (E=I≠A, confirmed bug):  0.829
    O3 (hallucination):         0.000 — dropped by bug_detector, never reaches here
    O4 (inconclusive):          0.432
    Exceptions/timeouts:        1.0 (default — execution-level signals)

When triangulation is disabled, confidence defaults to 1.0
and B(S) reduces to log(1 + total_bugs) — identical to original behavior.

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

    exception_confidence = sum(b.get("validation_confidence", 1.0) for b in state.exceptions)
    failure_confidence = sum(b.get("validation_confidence", 1.0) for b in state.failures)
    incorrect_confidence = sum(b.get("validation_confidence", 1.0) for b in state.incorrect_outputs)

    weighted_bugs = exception_confidence + failure_confidence + incorrect_confidence
    bug_score = math.log(1 + weighted_bugs)

    objective_value = coverage_score + bug_score
    return objective_value