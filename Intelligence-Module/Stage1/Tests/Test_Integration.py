"""
Grey box test: Integration
Tests data flow across: Semantic Engine → State → Environment → Transition → Tools
Verifies contracts between components
"""
from Stage1.Deterministic.Stage1_Semantic import Semantic_Engine
from Stage1.Core.State import State
from Stage1.Core.Environment import Environment
from Stage1.Core.Objective import evaluate_state
from Stage1.Algo.hybrid_search import Hybrid_Search

if __name__ == '__main__':

    # ===== Semantic Engine → State flow =====
    print("=== Semantic Engine → State ===")

    stage0_result = {"status": "PASS", "language": "python"}
    source_code = "class Solution:\n    def add(self, a, b):\n        return a + b"

    engine = Semantic_Engine(stage0_result, source_code)
    semantic_output = engine.run()

    print(f"  Semantic output has language: {'language' in semantic_output}")
    print(f"  Semantic output has execution_model: {'execution_model' in semantic_output}")
    print(f"  Semantic output has structural_features: {'structural_features' in semantic_output}")
    print(f"  Semantic output has normalized_code: {'normalized_code' in semantic_output}")

    state = State.from_semantic_output(semantic_output)
    print(f"  State.language matches: {state.language == semantic_output['language']}")
    print(f"  State.execution_model matches: {state.execution_model == semantic_output['execution_model']}")
    print(f"  State.source_code non-empty: {len(state.source_code) > 0}")
    print(f"  State.structural_features non-None: {state.structural_features is not None}")

    # ===== State → Objective flow =====
    print("\n=== State → Objective ===")

    state.line_coverage = 0.5
    state.branch_coverage = 0.8
    score = evaluate_state(state)
    print(f"  Score computable: {score > 0}")
    print(f"  Score is float: {isinstance(score, float)}")

    features = state.structural_features
    line_count = features.get("line_count", 0)
    branch_count = features.get("branching_factor", 0)
    print(f"  line_count available: {line_count > 0}")
    print(f"  branching_factor available: {isinstance(branch_count, (int, float))}")

    # ===== Algorithm → Environment flow =====
    print("\n=== Algorithm → Environment ===")

    state = State.from_semantic_output(semantic_output)
    algo = Hybrid_Search()

    exploration_actions = algo.get_exploration_actions()
    print(f"  Exploration actions: {len(exploration_actions)}")
    for a in exploration_actions:
        print(f"    Action type: {a.action_type}, Strategy: {a.strategy}")

    state.iteration = 3
    action = algo.select_action(state)
    print(f"  Agentic action type: {action.action_type}")
    print(f"  Has strategy: {action.strategy is not None}")

    # ===== Full pipeline integration — correct code =====
    print("\n=== Full Pipeline — Correct Code ===")

    source_correct = "class Solution:\n    def add(self, a, b):\n        return a + b"
    stage0_result = {"status": "PASS", "language": "python"}

    engine = Semantic_Engine(stage0_result, source_correct)
    semantic_output = engine.run()
    state = State.from_semantic_output(semantic_output)

    algo = Hybrid_Search()
    env = Environment(state, algo, max_iterations=3)
    final_state = env.run()

    print(f"  Pipeline completed: {final_state.iteration > 0}")
    print(f"  Coverage tracked: {final_state.line_coverage >= 0}")
    print(f"  Tests generated: {len(final_state.generated_tests) > 0}")
    print(f"  Tests executed: {len(final_state.executed_tests) > 0}")

    # ===== Full pipeline integration — buggy code =====
    print("\n=== Full Pipeline — Buggy Code ===")

    source_buggy = "class Solution:\n    def divide(self, a, b):\n        return a / b"
    engine = Semantic_Engine(stage0_result, source_buggy)
    semantic_output = engine.run()
    state = State.from_semantic_output(semantic_output)

    algo = Hybrid_Search()
    env = Environment(state, algo, max_iterations=3)
    final_state = env.run()

    print(f"  Pipeline completed: {final_state.iteration > 0}")
    total_bugs = len(final_state.exceptions) + len(final_state.failures) + len(final_state.incorrect_outputs)
    print(f"  Bugs found: {total_bugs}")

    # ===== Stage 0 FAIL → Stage 1 rejected =====
    print("\n=== Stage 0 FAIL → Stage 1 Rejection ===")

    stage0_fail = {"status": "FAIL", "language": "python"}
    try:
        engine = Semantic_Engine(stage0_fail, "x = 1")
        print("  Stage 0 FAIL accepted: FAILED — should have rejected")
    except ValueError:
        print("  Stage 0 FAIL rejected: PASSED")

    # ===== Cumulative coverage across iterations =====
    print("\n=== Cumulative Coverage Across Iterations ===")

    source = "class Solution:\n    def check(self, n):\n        if n > 0:\n            return 'pos'\n        return 'neg'"
    engine = Semantic_Engine(stage0_result, source)
    semantic_output = engine.run()
    state = State.from_semantic_output(semantic_output)

    algo = Hybrid_Search()
    env = Environment(state, algo, max_iterations=5)
    final_state = env.run()

    print(f"  Final line coverage: {final_state.line_coverage:.2f}")
    print(f"  Final branch coverage: {final_state.branch_coverage:.2f}")
    print(f"  Cumulative lines count: {len(final_state.all_executed_lines)}")
    print(f"  Coverage > 0: {final_state.line_coverage > 0}")

    # ===== Score monotonically increases =====
    print("\n=== Score Monotonicity ===")

    scores = [h.get('score', 0) for h in env.history]
    print(f"  Scores: {[f'{s:.4f}' for s in scores]}")
    monotonic = all(scores[i] <= scores[i+1] for i in range(len(scores)-1))
    print(f"  Monotonically non-decreasing: {monotonic}")