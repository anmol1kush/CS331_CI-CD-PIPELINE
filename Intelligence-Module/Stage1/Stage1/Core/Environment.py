"""
Environment controller for the Stage-1 intelligent testing agent.

This module manages the agent loop and connects:

- State
- Algorithms
- Transition system
- Objective evaluation
"""

from Stage1.Core.Transition import apply_action
from Stage1.Core.Objective import evaluate_state
from Stage1.Core.State import State


class Environment:
    def __init__(self, state, algorithm, max_iterations=20):
        self.state = state
        self.algorithm = algorithm
        self.max_iterations = max_iterations
        self.history = []

    def run(self):
        if not self.algorithm:
            return self.state

        # Phase 0: Deterministic exploration — does NOT consume iteration budget
        if hasattr(self.algorithm, 'get_exploration_actions'):
            print(f"\n[Environment] Starting deterministic exploration phase")
            self.exploration_count = 0

            for action in self.algorithm.get_exploration_actions():
                print(f"[Exploration] Action: {action}")
                apply_action(self.state, action)
                score = evaluate_state(self.state)
                print(f"[Exploration] Score: {score}")

                if hasattr(self.algorithm, 'update_rewards'):
                    self.algorithm.update_rewards(self.state, score)

                self.history.append({
                    "iteration": self.state.iteration,
                    "phase": "exploration",
                    "action": str(action),
                    "score": score
                })

                self.exploration_count += 1

        # Phase 1: Agentic loop — only these count toward budget
        print(f"\n[Environment] Starting agent loop (max {self.max_iterations} iterations)")

        while not self.state.stop_flag and (self.state.iteration - self.exploration_count) < self.max_iterations:
            print(f"\n[Iteration {self.state.iteration - self.exploration_count}] Selecting action...")

            action = self.algorithm.select_action(self.state)
            print(f"[Iteration {self.state.iteration - self.exploration_count}] Action: {action}")

            apply_action(self.state, action)
            score = evaluate_state(self.state)
            print(f"[Iteration {self.state.iteration - self.exploration_count}] Score: {score}")

            if hasattr(self.algorithm, 'update_rewards'):
                self.algorithm.update_rewards(self.state, score)

            self.history.append({
                "iteration": self.state.iteration,
                "phase": "agentic",
                "action": str(action),
                "score": score
            })

        print(f"\n[Environment] Loop ended at iteration {self.state.iteration}")
        return self.state

    def get_history(self):
        return self.history