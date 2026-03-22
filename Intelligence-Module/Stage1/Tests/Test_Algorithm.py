"""
White box test: Hybrid Search Algorithm
Tests exploration, temperature, plateau detection, strategy selection, stop condition
"""
from Stage1.Algo.hybrid_search import Hybrid_Search
from Stage1.Core.State import State
from Stage1.Core.Actions import Action_Type, Test_Strategy

if __name__ == '__main__':
    semantic = {
        "language": "python",
        "execution_model": "callable_method",
        "structural_features": {"line_count": 10, "branching_factor": 2},
        "normalized_code": "dummy"
    }

    # ===== exploration actions =====
    print("=== Exploration Actions ===")

    algo = Hybrid_Search()
    actions = algo.get_exploration_actions()
    print(f"  Count: {len(actions)}")

    strategies_seen = set()
    for a in actions:
        strategies_seen.add(a.strategy)
        print(f"  {a}")
    print(f"  All strategies covered: {len(strategies_seen) == 3}")

    print(f"  Untried after exploration: {len(algo.untried_strategies)}")

    # ===== temperature computation =====
    print("\n=== Temperature ===")

    algo = Hybrid_Search()
    algo.untried_strategies = []

    temps = []
    for i in range(14):
        t = algo.compute_temperature(i)
        temps.append(t)
        print(f"  Iteration {i}: temp={t:.4f}")

    print(f"  Monotonically decreasing: {all(temps[i] >= temps[i+1] for i in range(len(temps)-1))}")
    print(f"  Starts near 1.0: {temps[0] > 0.9}")
    print(f"  Ends near 0.0: {temps[-1] < 0.1}")

    # ===== update_rewards — improvement =====
    print("\n=== Update Rewards ===")

    algo = Hybrid_Search()
    algo.untried_strategies = []
    state = State.from_semantic_output(semantic)

    algo.last_chosen_strategy = Test_Strategy.EDGE_CASE
    algo.update_rewards(state, 0.5)
    print(f"  After improvement: stagnation={algo.stagnation_counter}")

    algo.last_chosen_strategy = Test_Strategy.BRANCH
    algo.update_rewards(state, 0.5)
    print(f"  After stagnation 1: stagnation={algo.stagnation_counter}")

    algo.last_chosen_strategy = Test_Strategy.BRANCH
    algo.update_rewards(state, 0.5)
    print(f"  After stagnation 2: stagnation={algo.stagnation_counter}")

    algo.last_chosen_strategy = Test_Strategy.ADVERSARIAL
    algo.update_rewards(state, 0.8)
    print(f"  After improvement: stagnation={algo.stagnation_counter}")

    # ===== reward tracking per strategy =====
    print("\n=== Reward Tracking ===")

    algo = Hybrid_Search()
    algo.untried_strategies = []

    algo.last_chosen_strategy = Test_Strategy.EDGE_CASE
    algo.update_rewards(state, 0.3)

    algo.last_chosen_strategy = Test_Strategy.EDGE_CASE
    algo.update_rewards(state, 0.5)

    algo.last_chosen_strategy = Test_Strategy.BRANCH
    algo.update_rewards(state, 0.8)

    for s, r in algo.strategy_rewards.items():
        print(f"  {s.value}: rewards={r}")

    # ===== get_best_strategy =====
    print("\n=== Best Strategy ===")

    algo = Hybrid_Search()
    algo.untried_strategies = []
    algo.strategy_rewards = {
        Test_Strategy.EDGE_CASE: [0.1, 0.2, 0.0],
        Test_Strategy.BRANCH: [0.3, 0.4],
        Test_Strategy.ADVERSARIAL: [0.05, 0.05]
    }

    best = algo.get_best_strategy()
    print(f"  Best strategy: {best.value}")

    algo.strategy_rewards = {
        Test_Strategy.EDGE_CASE: [],
        Test_Strategy.BRANCH: [],
        Test_Strategy.ADVERSARIAL: []
    }
    best = algo.get_best_strategy()
    print(f"  Empty rewards → random: {best.value}")

    # ===== plateau escape =====
    print("\n=== Plateau Escape ===")

    algo = Hybrid_Search()
    algo.untried_strategies = []
    state = State.from_semantic_output(semantic)
    state.iteration = 5

    algo.stagnation_counter = 3
    algo.strategies_tried_during_plateau = set()

    action = algo.select_action(state)
    print(f"  Plateau escape action: {action}")
    print(f"  Strategies tried in plateau: {algo.strategies_tried_during_plateau}")

    # ===== plateau — all strategies tried → stop =====
    print("\n=== Inescapable Plateau ===")

    algo = Hybrid_Search()
    algo.untried_strategies = []
    algo.strategy_rewards = {
        Test_Strategy.EDGE_CASE: [0.1, 0.1],
        Test_Strategy.BRANCH: [0.1, 0.1],
        Test_Strategy.ADVERSARIAL: [0.1, 0.1]
    }
    algo.stagnation_counter = 3
    algo.strategies_tried_during_plateau = {
        Test_Strategy.EDGE_CASE,
        Test_Strategy.BRANCH,
        Test_Strategy.ADVERSARIAL
    }
    state.iteration = 12

    action = algo.select_action(state)
    print(f"  All tried in plateau → action: {action.action_type}")

    # ===== should_stop =====
    print("\n=== Should Stop ===")

    algo = Hybrid_Search()
    algo.untried_strategies = []
    state = State.from_semantic_output(semantic)

    state.iteration = 5
    print(f"  Early iteration: should_stop={algo.should_stop(state)}")

    algo.strategy_rewards = {
        Test_Strategy.EDGE_CASE: [0.1, 0.1],
        Test_Strategy.BRANCH: [0.1, 0.1],
        Test_Strategy.ADVERSARIAL: [0.1, 0.1]
    }
    algo.stagnation_counter = 3
    state.iteration = 12
    print(f"  All conditions met: should_stop={algo.should_stop(state)}")

    # ===== action history =====
    print("\n=== Action History ===")

    algo = Hybrid_Search()
    algo.untried_strategies = []
    state = State.from_semantic_output(semantic)
    state.iteration = 3

    action = algo.select_action(state)
    print(f"  History length: {len(algo.action_history)}")
    print(f"  History entry keys: {list(algo.action_history[0].keys())}")

    algo.update_rewards(state, 0.5)
    print(f"  After update — reward in history: {'reward' in algo.action_history[-1]}")
    print(f"  After update — score in history: {'score' in algo.action_history[-1]}")