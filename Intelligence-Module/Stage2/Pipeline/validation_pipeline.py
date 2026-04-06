"""
Stage-2 Validation Pipeline

Orchestrates the full Stage 2 flow:
    1. Receive Stage 1 output (with triangulation verdicts)
    2. Create validation state
    3. Run signal filter (drops hallucinations, runs mutation testing)
    4. Run report builder (produces final classified output)
    5. Return structured Stage 2 output

No LLM calls in Stage 2. Pure execution-based validation.

Current increment:
    - Single entry point: run_stage2(stage1_output)
    - Sequential flow: filter → mutate → report

Future increment placeholders:
    - Parallel mutation testing across multiple source files
    - Caching mutation results across pipeline runs
    - Configurable validation depth (quick vs thorough)
"""

from Stage2.Core.validation_state import Validation_State
from Stage2.Core.signal_filter import Signal_Filter
from Stage2.Report.report_builder import Report_Builder


def run_stage2(stage1_output):
    """
    Entry point for Stage 2 validation.

    Args:
        stage1_output: complete output dict from Stage 1 pipeline
                       Must contain: bugs, executed_tests, generated_test_cases,
                       coverage, language, execution_model, structural_features

    Returns:
        dict with validated bugs, separated test suite, mutation results, summary
    """
    print("\n" + "=" * 60)
    print("STAGE 2 — Validation Pipeline")
    print("=" * 60)

    # ── Step 1: Create validation state ──
    validation_state = Validation_State(stage1_output)

    print(f"\n[Stage 2] Loaded Stage 1 output:")
    print(f"    Language: {validation_state.language}")
    print(f"    Execution model: {validation_state.execution_model}")
    print(f"    Executed tests: {len(validation_state.executed_tests)}")
    print(f"    Exceptions: {len(validation_state.exceptions)}")
    print(f"    Failures: {len(validation_state.failures)}")
    print(f"    Incorrect outputs: {len(validation_state.incorrect_outputs)}")

    # ── Step 2: Run signal filter (hallucination removal + mutation testing) ──
    signal_filter = Signal_Filter()
    signal_filter.run(validation_state)

    # ── Step 3: Build final report ──
    report_builder = Report_Builder()
    stage2_output = report_builder.build(validation_state)

    print(f"\n[Stage 2] Pipeline complete")

    return stage2_output