"""
Action definitions for the Stage-1.
"""
from enum import Enum
from typing import Optional

class Action_Type(Enum):
    GENERATE_TESTS = "generate_tests"
    RUN_TEST_SUITE = "run_test_suite"
    STOP = "stop"

class Test_Strategy(Enum):
    EDGE_CASE = "edge_case"
    BRANCH = "branch"
    ADVERSARIAL = "adversarial"
    STRESS = "stress"
    CONSTRAINT = "constraint"

class Action:
    def __init__(
        self,
        action_type: Action_Type,
        strategy: Optional[Test_Strategy] = None
    ):

        self.action_type = action_type
        self.strategy = strategy

    def __repr__(self):
        if self.strategy:
            return f"Action(type={self.action_type.value}, strategy={self.strategy.value})"

        return f"Action(type={self.action_type.value})"