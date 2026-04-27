"""
Tests Executor — Thin Dispatcher

Routes test execution to language-specific executors
via the Executor Factory.

Supported languages:
    - python (exec + sys.settrace)
    - javascript / typescript (node subprocess)
    - java (javac + java subprocess)
    - c / cpp (gcc/g++ + binary subprocess)

NOTE:
This file previously contained all execution logic inline.
That logic now lives in Stage1/Executors/ submodule.
This file exists to preserve the call interface for
upstream consumers (Environment, Transition).
"""

from Stage1.Executors.executor_factory import get_executor


def run_tests(source_code, tests, execution_model, language="python", structural_features=None):
    """
    Execute tests against source code using the appropriate language executor.

    Args:
        source_code: full source code string
        tests: list of test dicts from LLM test generator
        execution_model: "callable_method" | "stdin_program" | "script"
        language: "python" | "javascript" | "typescript" | "java" | "c" | "cpp"
        structural_features: parser output with class_hierarchy, method_signatures, etc.

    Returns:
        (results: list[dict], all_executed_lines: set)
    """
    executor = get_executor(language)
    return executor.run(source_code, tests, execution_model, structural_features)