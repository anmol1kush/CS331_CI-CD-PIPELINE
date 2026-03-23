"""
State transition system for the Stage-1 agent.

Defines how the state evolves after an action is applied.

S_{t+1} = T(S_t, a)

The transition layer connects the agent logic with the
execution tools (test runner, coverage tracker, bug detector).
"""

from Stage1.Core.Actions import Action_Type
from Stage1.Tools.test_executor import run_tests
from Stage1.Tools.coverage_analyzer import compute_coverage
from Stage1.Tools.bug_detector import detect_bugs
from Stage1.Tools.llm_test_generator import LLM_Test_Generator


def apply_action(state, action):
    if action.action_type == Action_Type.GENERATE_TESTS:
        generate_tests(state, action.strategy)

    elif action.action_type == Action_Type.STOP:
        stop_agent(state)

    state.increment_iteration()

    return state


llm_generator = LLM_Test_Generator()

def generate_tests(state, strategy):
    try:
        tests = llm_generator.generate_tests(
            source_code=state.source_code,
            execution_model=state.execution_model,
            structural_features=state.structural_features,
            strategy=strategy.value,
            existing_tests=state.executed_tests if state.executed_tests else None,
            previous_failures=state.exceptions if state.exceptions else None
        )
    except (ValueError, RuntimeError) as e:
        print(f"  [Transition] LLM error: {e} — skipping this iteration")
        return

    if not tests:
        return

    state.add_generated_tests(tests, strategy.value if strategy else "unknown")
    run_test_suite(state)


def run_test_suite(state):
    # --- Option A: UUID-based filtering (use when Option A is enabled in State.py) ---
    # executed_ids = {t["test_id"] for t in state.executed_tests}
    # pending_tests = [t for t in state.generated_tests if t["test_id"] not in executed_ids]

    # --- Option B: Index-based filtering (current increment) ---
    already_executed_count = len(state.executed_tests)
    pending_tests = state.generated_tests[already_executed_count:]
    # ------------------------------------------------------------

    if not pending_tests:
        return

    results, executed_lines = run_tests(state.source_code, pending_tests, state.execution_model)
    state.all_executed_lines.update(executed_lines)
    coverage = compute_coverage(state.source_code, state.all_executed_lines)

    state.update_coverage(
        coverage.get("line_coverage", 0),
        coverage.get("branch_coverage", 0)
    )

    bugs = detect_bugs(results, pending_tests)

    state.record_exceptions(bugs.get("exceptions", []))
    state.record_failures(bugs.get("failures", []))
    state.record_incorrect_outputs(bugs.get("incorrect_outputs", []))

    state.mark_tests_executed(pending_tests)

def stop_agent(state):
    state.stop()