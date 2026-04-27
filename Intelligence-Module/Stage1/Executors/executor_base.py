"""
Executor Base — Abstract interface for language-specific test executors.

Every executor must:
    1. Take source code + test case
    2. Execute the code with the test input
    3. Return a standardized result dict
    4. Collect executed line numbers for coverage

Result contract (same for all languages):
    {
        "status": str,           # "success" | "exception" | "timeout" | "crash"
        "output": any,           # actual output from execution
        "error": str | None,     # error message if not success
        "executed_lines": set,   # line numbers hit during execution
        "called_operations": list,
        "runtime": float         # seconds
    }
"""

from abc import ABC, abstractmethod


class ExecutorBase(ABC):

    @abstractmethod
    def execute_callable(self, source_code: str, tests: list, structural_features: dict = None) -> tuple:
        """
        Execute tests against a callable method/function.

        Args:
            source_code: full source code string
            tests: list of test dicts with "method_name", "input", "expected_output"
            structural_features: parser output with class_hierarchy, method_signatures, etc.

        Returns:
            (results: list[dict], all_executed_lines: set)
        """
        pass

    @abstractmethod
    def execute_stdin(self, source_code: str, tests: list) -> tuple:
        """
        Execute tests by feeding stdin input.

        Args:
            source_code: full source code string
            tests: list of test dicts with "input" (stdin string), "expected_output"

        Returns:
            (results: list[dict], all_executed_lines: set)
        """
        pass

    @abstractmethod
    def execute_script(self, source_code: str) -> tuple:
        """
        Execute source code as a standalone script (no input).

        Args:
            source_code: full source code string

        Returns:
            (results: list[dict], all_executed_lines: set)
        """
        pass

    def run(self, source_code: str, tests: list, execution_model: str, structural_features: dict = None) -> tuple:
        """
        Dispatcher — routes to the correct execution method.

        Args:
            source_code: full source code string
            tests: list of test dicts
            execution_model: "callable_method" | "stdin_program" | "script"
            structural_features: parser output with class_hierarchy, method_signatures, etc.

        Returns:
            (results: list[dict], all_executed_lines: set)
        """
        if execution_model == "callable_method":
            return self.execute_callable(source_code, tests, structural_features)
        elif execution_model == "stdin_program":
            return self.execute_stdin(source_code, tests)
        elif execution_model == "script":
            return self.execute_script(source_code)
        else:
            raise ValueError(f"Unsupported execution model: {execution_model}")