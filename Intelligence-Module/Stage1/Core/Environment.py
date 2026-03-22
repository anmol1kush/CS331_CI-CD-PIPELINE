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
    def __init__(self, semantic_output, algorithm, max_iterations=20):
        self.state = State.from_semantic_output(semantic_output)
        self.algorithm = algorithm
        self.max_iterations = max_iterations
        self.history = []

    def run(self):
        while not self.state.stop_flag and self.state.iteration < self.max_iterations:
            action = self.algorithm.select_action(self.state)
            apply_action(self.state, action)
            score = evaluate_state(self.state)

            self.history.append(
                {
                    "iteration": self.state.iteration,
                    "action": str(action),
                    "score": score
                }
            )

        return self.state

    def get_history(self):
        return self.history