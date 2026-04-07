"""
White box test: Environment
Tests exploration phase, agent loop, iteration counting, history tracking
NOTE: Uses real algorithm but simple code to minimize API calls
"""
from Stage1.Core.State import State
from Stage1.Core.Environment import Environment
from Stage1.Algo.hybrid_search import Hybrid_Search

if __name__ == '__main__':

    semantic = {
        "language": "python",
        "execution_model": "callable_method",
        "structural_features": {"line_count": 5, "branching_factor": 1},
        "normalized_code": "class Solution:\n    def add(self, a, b):\n        if a > 0:\n            return a + b\n        return b"
    }

    # ===== None algorithm guard =====
    print("=== None Algorithm ===")

    state = State.from_semantic_output(semantic)
    env = Environment(state, None, max_iterations=5)
    result = env.run()
    print(f"  None algo → returns state: {result is not None}")
    print(f"  Iteration: {result.iteration}")

    # ===== exploration phase runs =====
    print("\n=== Exploration Phase ===")

    state = State.from_semantic_output(semantic)
    algo = Hybrid_Search()
    env = Environment(state, algo, max_iterations=5)

    has_exploration = hasattr(algo, 'get_exploration_actions')
    print(f"  Algorithm has get_exploration_actions: {has_exploration}")

    final_state = env.run()
    exploration_entries = [h for h in env.history if h.get('phase') == 'exploration']
    agentic_entries = [h for h in env.history if h.get('phase') == 'agentic']
    print(f"  Exploration entries in history: {len(exploration_entries)}")
    print(f"  Agentic entries in history: {len(agentic_entries)}")
    print(f"  Exploration count: {env.exploration_count}")

    # ===== exploration doesn't consume iteration budget =====
    print("\n=== Iteration Budget ===")

    state = State.from_semantic_output(semantic)
    algo = Hybrid_Search()
    env = Environment(state, algo, max_iterations=3)
    final_state = env.run()

    print(f"  Total iterations (internal): {final_state.iteration}")
    print(f"  Exploration count: {env.exploration_count}")
    print(f"  Agentic iterations: {final_state.iteration - env.exploration_count}")
    print(f"  Max iterations config: 3")
    print(f"  Agentic <= max: {(final_state.iteration - env.exploration_count) <= 3}")

    # ===== history tracking =====
    print("\n=== History Tracking ===")

    state = State.from_semantic_output(semantic)
    algo = Hybrid_Search()
    env = Environment(state, algo, max_iterations=2)
    final_state = env.run()

    print(f"  History length: {len(env.history)}")
    if env.history:
        first = env.history[0]
        print(f"  First entry has iteration: {'iteration' in first}")
        print(f"  First entry has action: {'action' in first}")
        print(f"  First entry has score: {'score' in first}")
        print(f"  First entry has phase: {'phase' in first}")

    # ===== update_rewards called =====
    print("\n=== Update Rewards Called ===")

    state = State.from_semantic_output(semantic)
    algo = Hybrid_Search()
    env = Environment(state, algo, max_iterations=2)
    final_state = env.run()

    has_rewards = any(len(r) > 0 for r in algo.strategy_rewards.values())
    print(f"  Algorithm received rewards: {has_rewards}")
    print(f"  Previous score tracked: {algo.previous_score > 0 or algo.previous_score == 0}")

    # ===== early stop via algorithm =====
    print("\n=== Early Stop ===")

    state = State.from_semantic_output(semantic)
    algo = Hybrid_Search()

    algo.strategy_rewards = {s: [0.1, 0.1] for s in algo.strategies}
    algo.stagnation_counter = 3
    algo.strategies_tried_during_plateau = set(algo.strategies)
    algo.untried_strategies = []

    env = Environment(state, algo, max_iterations=10)
    state.iteration = 12
    final_state = env.run()

    print(f"  Early stop triggered: {final_state.stop_flag or final_state.iteration < 10 + env.exploration_count}")

    # ===== get_history =====
    print("\n=== Get History ===")

    state = State.from_semantic_output(semantic)
    algo = Hybrid_Search()
    env = Environment(state, algo, max_iterations=2)
    env.run()

    history = env.get_history()
    print(f"  get_history returns list: {isinstance(history, list)}")
    print(f"  History length: {len(history)}")