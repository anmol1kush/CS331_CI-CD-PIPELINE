"""
State representation for the Stage-1 agentic testing system.
"""
from typing import Dict, List, Any
import uuid

class State:
    def __init__(
        self,
        language: str,
        execution_model: str,
        structural_features: Dict[str, Any],
        source_code: str = ""
    ):

        # pipeline context
        self.language = language
        self.execution_model = execution_model
        self.source_code = source_code

        # static str features
        self.structural_features = structural_features

        # test pool
        self.generated_tests: List[Any] = []
        self.executed_tests: List[Any] = []
        self.strategy_usage: Dict[str, int] = {}

        # runtime observations
        self.failures: List[Any] = []
        self.exceptions: List[str] = []
        self.incorrect_outputs: List[Any] = []

        # coverage metrics
        self.line_coverage: float = 0.0
        self.branch_coverage: float = 0.0
        self.all_executed_lines: set = set()

        # agent control
        self.iteration: int = 0
        self.stop_flag: bool = False

    @classmethod
    def from_semantic_output(cls, semantic_output: Dict[str, Any]):
        language = semantic_output.get("language")
        execution_model = semantic_output.get("execution_model")
        structural_features = semantic_output.get("structural_features") or {}
        source_code = semantic_output.get("normalized_code","")

        return cls(
            language=language,
            execution_model=execution_model,
            structural_features=structural_features,
            source_code = source_code
        )

    def add_generated_tests(self, tests: List[Any], strategy: str):
        # --- Option A: UUID stamping ---
        # for test in tests:
        #     test["test_id"] = str(uuid.uuid4())
        self.generated_tests.extend(tests)

        if strategy not in self.strategy_usage:
            self.strategy_usage[strategy] = 0

        self.strategy_usage[strategy] += 1

    def mark_tests_executed(self, tests: List[Any]):
        self.executed_tests.extend(tests)

    def record_failures(self, failures: List[Any]):
        self.failures.extend(failures)

    def record_exceptions(self, exceptions: List[str]):
        self.exceptions.extend(exceptions)

    def record_incorrect_outputs(self, outputs: List[Any]):
        self.incorrect_outputs.extend(outputs)

    def update_coverage(self, line_coverage: float, branch_coverage: float):
        self.line_coverage = line_coverage
        self.branch_coverage = branch_coverage

    def increment_iteration(self):
        self.iteration += 1

    def stop(self):
        self.stop_flag = True

    def to_dict(self):

        return {
            "language": self.language,
            "execution_model": self.execution_model,
            "source_code": self.source_code,
            "structural_features": self.structural_features,
            "generated_tests": self.generated_tests,
            "executed_tests": self.executed_tests,
            "strategy_usage": self.strategy_usage,
            "failures": self.failures,
            "exceptions": self.exceptions,
            "incorrect_outputs": self.incorrect_outputs,
            "line_coverage": self.line_coverage,
            "branch_coverage": self.branch_coverage,
            "iteration": self.iteration,
            "stop_flag": self.stop_flag,
            "all_executed_lines": list(self.all_executed_lines)
        }