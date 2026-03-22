"""
Hybrid Search Algorithm for Stage-1.

Combines three algorithm strategies into a single adaptive algorithm:
- Random Search: forced initial exploration
- Simulated Annealing: temperature-controlled explore/exploit transition
- Hill Climb: greedy exploitation with plateau detection

Temperature function:
    remaining_ratio = (max_iterations - iteration) / max_iterations
    temperature = remaining_ratio ** TEMPERATURE_EXPONENT

Decision flow:
    1. Forced exploration phase → try each strategy once
    2. Plateau detected → force random pick
    3. Temperature roll → explore (random) or exploit (best)
    4. Stop condition → all explored + stagnated + low temperature
"""
import random
from Stage1.Core.Actions import Action, Action_Type, Test_Strategy
from Stage1.Algo.base import Base_Algorithm
from Stage1.config import (
    MAX_ITERATIONS,
    TEMPERATURE_EXPONENT,
    STAGNATION_THRESHOLD
)


class Hybrid_Search(Base_Algorithm):
    def __init__(self):
        self.strategies = [
            Test_Strategy.EDGE_CASE,
            Test_Strategy.BRANCH,
            Test_Strategy.ADVERSARIAL
        ]

        # reward tracking per strategy
        self.strategy_rewards = {s: [] for s in self.strategies}

        # plateau detection
        self.previous_score = 0.0
        self.stagnation_counter = 0

        # forced exploration tracking
        self.untried_strategies = list(self.strategies)

        # action history
        self.last_chosen_strategy = None
        self.action_history = []

    def select_action(self, state) -> Action:
        # ---------- Phase 1: Forced Exploration ----------
        # ---------- Stop Condition ----------
        if self.should_stop(state):
            return Action(action_type=Action_Type.STOP)

        # ---------- Plateau Detection ----------
        if self.stagnation_counter >= STAGNATION_THRESHOLD:
            self.stagnation_counter = 0
            strategy = random.choice(self.strategies)
            self.track_action(state, strategy)
            return Action(action_type=Action_Type.GENERATE_TESTS, strategy=strategy)

        # ---------- Temperature-Guided Selection ----------
        temperature = self.compute_temperature(state.iteration)

        if random.random() < temperature:
            strategy = random.choice(self.strategies)
        else:
            strategy = self.get_best_strategy()

        self.track_action(state, strategy)
        return Action(action_type=Action_Type.GENERATE_TESTS, strategy=strategy)

    def get_exploration_actions(self):
        """
        Returns all forced exploration actions at once.
        Called by Environment BEFORE the agent loop starts.
        These do NOT consume agent loop iterations.
        """
        actions = []
        for strategy in list(self.untried_strategies):
            self.last_chosen_strategy = strategy
            self.action_history.append({
                "phase": "exploration",
                "strategy": strategy,
                "temperature": 1.0
            })
            actions.append(Action(action_type=Action_Type.GENERATE_TESTS, strategy=strategy))

        self.untried_strategies = []
        return actions


    def track_action(self, state, strategy):
        """
        Internal helper to track chosen strategy and record action history.
        Called from every decision path in select_action.
        """
        self.last_chosen_strategy = strategy
        self.action_history.append({
            "iteration": state.iteration,
            "strategy": strategy,
            "temperature": self.compute_temperature(state.iteration)
        })

    def update_rewards(self, state, score):
        """
        Called by Environment after each iteration to update
        reward history and stagnation tracking.

        Must be called AFTER evaluate_state produces the score.
        """
        # use internally tracked strategy — not state.strategy_usage
        if self.last_chosen_strategy:
            improvement = score - self.previous_score
            self.strategy_rewards[self.last_chosen_strategy].append(improvement)

            # update history with reward
            if self.action_history:
                self.action_history[-1]["reward"] = improvement
                self.action_history[-1]["score"] = score

        # stagnation tracking
        if score > self.previous_score:
            self.stagnation_counter = 0
        else:
            self.stagnation_counter += 1

        self.previous_score = score

    def compute_temperature(self, iteration):
        """
        Temperature function:
            remaining_ratio = (max_iterations - iteration) / max_iterations
            temperature = remaining_ratio ** exponent

        Domain: iteration ∈ [0, max_iterations]
        Range: temperature ∈ [0.0, 1.0]

        Higher temperature → more exploration
        Lower temperature → more exploitation
        """
        agentic_iteration = iteration - len(self.strategies)
        if agentic_iteration < 0:
            agentic_iteration = 0

        remaining_ratio = (MAX_ITERATIONS - agentic_iteration) / MAX_ITERATIONS
        temperature = remaining_ratio ** TEMPERATURE_EXPONENT
        return temperature

    def get_best_strategy(self):
        """
        Hill Climb logic: pick strategy with highest average reward.
        If no data or tie, pick random.
        """
        best_strategy = None
        best_average = float("-inf")

        for strategy, rewards in self.strategy_rewards.items():
            if not rewards:
                continue

            average = sum(rewards) / len(rewards)

            if average > best_average:
                best_average = average
                best_strategy = strategy

        if best_strategy is None:
            return random.choice(self.strategies)

        return best_strategy

    def should_stop(self, state):
        """
        Stop if ALL conditions met:
        - Every strategy tried at least twice
        - Score stagnated beyond threshold
        - Temperature below 0.1 (in exploitation phase)
        """
        all_tried_twice = all(
            len(rewards) >= 2 for rewards in self.strategy_rewards.values()
        )

        stagnated = self.stagnation_counter >= STAGNATION_THRESHOLD

        temperature = self.compute_temperature(state.iteration)
        low_temperature = temperature < 0.1

        return all_tried_twice and stagnated and low_temperature