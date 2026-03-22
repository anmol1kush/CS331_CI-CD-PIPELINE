"""
Base Algorithm Interface for Stage-1.

All algorithms must implement select_action(state) → Action.
Environment.run() calls this method each iteration.

The algorithm:
- READS from state (coverage, bugs, strategy usage, iteration)
- RETURNS an Action (which strategy to generate tests with, or STOP)
- Does NOT modify state directly
"""
from abc import ABC, abstractmethod
from Stage1.Core.Actions import Action


class Base_Algorithm(ABC):
    @abstractmethod
    def select_action(self, state) -> Action:
        """
        Given the current state, decide the next action.

        Must return:
            Action(GENERATE_TESTS, strategy) — to generate tests
            Action(STOP) — to end the agent loop
        """
        pass