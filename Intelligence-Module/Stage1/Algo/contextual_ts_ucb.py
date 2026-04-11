"""
Contextual Thompson Sampling + UCB Algorithm for Stage-1.

Replaces Hybrid Search (SA + Hill Climb) with a contextual
multi-armed bandit that uses:

    1. Thompson Sampling — Beta posteriors per arm for Bayesian exploration
    2. UCB bonus — exploration guarantee for tight iteration budgets
    3. Contextual bonus — structural features bias arm selection

Arm score = Thompson sample + UCB bonus + Context bonus
Highest score wins.

Reward model:
    Binary Bernoulli: improvement > 0 → success, else failure
    Beta(α, β) conjugate update per arm
    FRRMAB-style sliding window for non-stationarity

No forced exploration phase — TS naturally explores via
high posterior variance (Beta(1,1) = uniform) in early rounds.

Backed by:
    - COLEMAN (Prado Lima & Vergilio, IEEE TSE 2020)
    - TS-UCB (Baek & Farias, 2020)
    - Chapelle & Li (NeurIPS 2011)
"""
import random
import math
from collections import deque
from Stage1.Core.Actions import Action, Action_Type, Test_Strategy
from Stage1.Algo.base import Base_Algorithm
from Stage1.config import (
    UCB_CONSTANT,
    SLIDING_WINDOW_SIZE,
    PRIOR_ALPHA,
    PRIOR_BETA,
    CONTEXT_WEIGHT_BRANCH,
    CONTEXT_WEIGHT_EDGE,
    CONTEXT_WEIGHT_ADVERSARIAL,
    STAGNATION_THRESHOLD
)


class Contextual_TS_UCB(Base_Algorithm):
    def __init__(self):
        self.strategies = [
            Test_Strategy.EDGE_CASE,
            Test_Strategy.BRANCH,
            Test_Strategy.ADVERSARIAL
        ]

        # Beta posteriors per arm: (alpha, beta)
        self.posteriors = {
            s: [PRIOR_ALPHA, PRIOR_BETA] for s in self.strategies
        }

        # Sliding window reward history per arm
        self.reward_windows = {
            s: deque(maxlen=SLIDING_WINDOW_SIZE) for s in self.strategies
        }

        # Pull counts per arm
        self.pull_counts = {s: 0 for s in self.strategies}
        self.total_pulls = 0

        # Score tracking
        self.previous_score = 0.0
        self.stagnation_counter = 0

        # Action history
        self.last_chosen_strategy = None
        self.action_history = []

    def select_action(self, state) -> Action:
        if self.should_stop(state):
            return Action(action_type=Action_Type.STOP)

        scores = {}
        for strategy in self.strategies:
            ts_sample = self._thompson_sample(strategy)
            ucb_bonus = self._ucb_bonus(strategy)
            ctx_bonus = self._context_bonus(strategy, state)

            scores[strategy] = ts_sample + ucb_bonus + ctx_bonus

        # Select arm with highest combined score
        best_strategy = max(scores, key=scores.get)

        self._track_action(state, best_strategy, scores)
        return Action(action_type=Action_Type.GENERATE_TESTS, strategy=best_strategy)

    def _thompson_sample(self, strategy):
        """
        Sample from Beta(α, β) posterior for this arm.
        High variance early (exploration) → low variance later (exploitation).
        """
        alpha, beta = self.posteriors[strategy]
        return random.betavariate(alpha, beta)

    def _ucb_bonus(self, strategy):
        """
        UCB exploration bonus: C * sqrt(log(N) / n_i)
        Guarantees minimum exploration of under-pulled arms.
        """
        n_i = self.pull_counts[strategy]
        if n_i == 0:
            return float('inf')  # force exploration of untried arms

        N = max(self.total_pulls, 1)
        return UCB_CONSTANT * math.sqrt(math.log(N) / n_i)

    def _context_bonus(self, strategy, state):
        """
        Contextual bonus from structural features.
        Biases arm selection based on code properties.
        """
        features = state.structural_features or {}

        branching_factor = features.get("branching_factor", 0)
        line_count = features.get("line_count", 0)
        max_depth = features.get("max_nesting_depth", 0)
        recursion = features.get("direct_recursion", False)
        loop_count = features.get("loop_count", 0)

        # Normalize features to [0, 1] range
        total_structure = branching_factor + line_count + max_depth + loop_count
        if total_structure == 0:
            return 0.0

        norm_branch = branching_factor / total_structure
        norm_lines = line_count / total_structure
        norm_depth = max_depth / total_structure
        norm_loops = loop_count / total_structure

        if strategy == Test_Strategy.BRANCH:
            return CONTEXT_WEIGHT_BRANCH * (norm_branch + norm_loops)

        elif strategy == Test_Strategy.EDGE_CASE:
            return CONTEXT_WEIGHT_EDGE * (norm_lines + norm_branch)

        elif strategy == Test_Strategy.ADVERSARIAL:
            recursion_signal = 0.3 if recursion else 0.0
            return CONTEXT_WEIGHT_ADVERSARIAL * (norm_depth + recursion_signal)

        return 0.0

    def update_rewards(self, state, score):
        """
        Called by Environment after each iteration.
        Updates Beta posteriors and sliding window.
        """
        if not self.last_chosen_strategy:
            return

        improvement = score - self.previous_score

        # Binary reward: improvement > 0 → success
        success = 1 if improvement > 0 else 0

        strategy = self.last_chosen_strategy

        # Update sliding window
        self.reward_windows[strategy].append(success)

        # Recompute posteriors from sliding window
        # (not cumulative — window-based for non-stationarity)
        window = self.reward_windows[strategy]
        successes = sum(window)
        failures = len(window) - successes

        self.posteriors[strategy] = [
            PRIOR_ALPHA + successes,
            PRIOR_BETA + failures
        ]

        # Update action history
        if self.action_history:
            self.action_history[-1]["reward"] = improvement
            self.action_history[-1]["score"] = score
            self.action_history[-1]["success"] = success

        # Stagnation tracking
        if improvement > 0:
            self.stagnation_counter = 0
        else:
            self.stagnation_counter += 1

        self.previous_score = score

    def _track_action(self, state, strategy, scores):
        """Record chosen action and update pull counts."""
        self.last_chosen_strategy = strategy
        self.pull_counts[strategy] += 1
        self.total_pulls += 1

        self.action_history.append({
            "iteration": state.iteration,
            "strategy": strategy,
            "scores": {s.value: round(v, 4) for s, v in scores.items()},
            "alpha": self.posteriors[strategy][0],
            "beta": self.posteriors[strategy][1]
        })

    def should_stop(self, state):
        """
        Stop if ALL conditions met:
        - Every arm pulled at least twice
        - Score stagnated beyond threshold
        - All posteriors have low variance (confident in estimates)
        """
        all_pulled_twice = all(
            count >= 2 for count in self.pull_counts.values()
        )

        stagnated = self.stagnation_counter >= STAGNATION_THRESHOLD

        # Posterior variance check: Beta variance = αβ / ((α+β)²(α+β+1))
        # Low variance → confident → ready to stop
        low_variance = all(
            self._posterior_variance(s) < 0.01
            for s in self.strategies
        )

        return all_pulled_twice and stagnated and low_variance

    def _posterior_variance(self, strategy):
        """Compute variance of Beta(α, β) posterior."""
        alpha, beta = self.posteriors[strategy]
        total = alpha + beta
        if total == 0:
            return 1.0
        return (alpha * beta) / (total * total * (total + 1))