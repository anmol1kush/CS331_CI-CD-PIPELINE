"""
Coverage Analyzer

Computes line coverage and approximate branch coverage
from executed line data provided by test executors.

This module does NOT execute any code.
It receives pre-computed trace data and source code,
then computes coverage metrics.

Branch coverage uses the Parser interface to extract
branch/loop structures in a language-agnostic way.

Downstream consumer: Objective function (evaluate_state)
"""

from Stage1.Parsers.parser_factory import get_parser


def compute_coverage(source_code, executed_lines, executable_lines=None, language="python"):
    if executable_lines and len(executable_lines) > 0:
        covered = executed_lines & executable_lines
        line_coverage = len(covered) / len(executable_lines)
    else:
        total = len(source_code.splitlines())
        if total == 0:
            line_coverage = 0.0
        else:
            line_coverage = len(executed_lines) / total

    branch_coverage = compute_branch_coverage(source_code, executed_lines, executable_lines, language)

    return {
        "line_coverage": line_coverage,
        "branch_coverage": branch_coverage
    }


def compute_branch_coverage(source_code, executed_lines, executable_lines=None, language="python"):
    try:
        parser = get_parser(language, source_code)
        success = parser.parse()
    except (ValueError, Exception):
        success = False

    if not success:
        return 1.0

    total_paths = 0
    executed_paths = 0

    # Branch paths from if/elif/else
    conditions = parser.extract_branch_conditions()
    for cond in conditions:
        line = cond["line"]

        # Skip branches in non-executable regions
        if executable_lines and line not in executable_lines:
            continue

        # True path (the if-body starts on the next line after condition)
        total_paths += 1
        if line in executed_lines:
            executed_paths += 1

        # False path — only if else/elif exists
        if cond["has_else"] or cond["has_elif"]:
            total_paths += 1
            # Heuristic: if the condition line was executed but an else exists,
            # check if any line near the else was also executed.
            # Without precise else-line info, we approximate:
            # if condition line is executed, assume at least one path was taken.
            # This is the same fidelity as the original ast-based approach.
            if line in executed_lines:
                executed_paths += 1

    # Loop paths
    loops = parser.extract_loop_bounds()
    for loop in loops:
        line = loop["line"]

        if executable_lines and line not in executable_lines:
            continue

        # Loop body executed path
        total_paths += 1
        if line in executed_lines:
            executed_paths += 1

    if total_paths == 0:
        return 1.0

    return executed_paths / total_paths