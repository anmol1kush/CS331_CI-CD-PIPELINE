"""
Coverage Analyzer

Computes line coverage and approximate branch coverage
from executed line data provided by test_executor.

This module does NOT execute any code.
It receives pre-computed trace data and source code,
then computes coverage metrics.

Downstream consumer: Objective function (evaluate_state)
"""
import ast


def compute_coverage(source_code, executed_lines, executable_lines=None):
    if executable_lines and len(executable_lines) > 0:
        covered = executed_lines & executable_lines
        line_coverage = len(covered) / len(executable_lines)
    else:
        total = len(source_code.splitlines())
        if total == 0:
            line_coverage = 0.0
        else:
            line_coverage = len(executed_lines) / total

    branch_coverage = compute_branch_coverage(source_code, executed_lines, executable_lines)

    return {
        "line_coverage": line_coverage,
        "branch_coverage": branch_coverage
    }


def compute_branch_coverage(source_code, executed_lines, executable_lines=None):
    tree = ast.parse(source_code)
    total_paths = 0
    executed_paths = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Skip branches in non-executable regions (dead code, docstrings)
            if executable_lines and node.lineno not in executable_lines:
                continue

            # True path
            total_paths += 1
            if node.body and node.body[0].lineno in executed_lines:
                executed_paths += 1

            # False path — only if else/elif exists
            if node.orelse:
                total_paths += 1
                if node.orelse[0].lineno in executed_lines:
                    executed_paths += 1

        if isinstance(node, (ast.For, ast.While)):
            # Skip loops in non-executable regions
            if executable_lines and node.lineno not in executable_lines:
                continue

            # Loop body executed path
            total_paths += 1
            if node.body and node.body[0].lineno in executed_lines:
                executed_paths += 1

            # Loop else path (runs when loop completes normally)
            if node.orelse:
                total_paths += 1
                if node.orelse[0].lineno in executed_lines:
                    executed_paths += 1

    if total_paths == 0:
        return 1.0

    return executed_paths / total_paths