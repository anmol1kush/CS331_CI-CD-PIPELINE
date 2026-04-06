"""
Signal Filter for Stage-2

Routes tests and bugs to Layer 3 (mutation testing).
Layer 2 (triangulation verification) is already done inside
Stage 1's agent loop — verdicts arrive in Stage 1's output.

Flow:
    1. Receive Stage 1 output with verdicts already attached
    2. Separate bugs by verdict (confirmed / inconclusive / hallucination)
    3. Drop hallucination bugs (O3, confidence = 0.0)
    4. Collect test suite for mutation testing
    5. Run Layer 3 (mutation engine + mutation runner)
    6. Write results to validation_state

Design:
    No LLM calls. Pure execution-based validation.
    Mutation testing validates test strength independent
    of oracle correctness.

Current increment:
    - Routes all executed tests to mutation testing
    - Filters out hallucination verdicts

Future increment placeholders:
    - Selective mutation testing (only mutate code regions with bugs)
    - Adaptive mutant count based on code complexity
    - Feedback from mutation results to Stage 1 for next pipeline run
"""

from Stage2.Mutation.mutation_engine import Mutation_Engine
from Stage2.Mutation.mutation_runner import Mutation_Runner


class Signal_Filter:
    def __init__(self):
        """No LLM provider needed — Stage 2 is execution-only."""
        self.mutation_engine = Mutation_Engine()
        self.mutation_runner = Mutation_Runner()

    def run(self, validation_state):
        """
        Routes bugs and tests through Layer 3 (mutation testing).

        Args:
            validation_state: Validation_State instance with Stage 1 data loaded
        """
        source_code = validation_state.source_code
        execution_model = validation_state.execution_model

        # ── Step 1: Log incoming verdicts from Stage 1 ──
        all_bugs = validation_state.get_all_incoming_bugs()
        confirmed = [b for b in all_bugs if b.get("verdict") == "confirmed_bug"]
        inconclusive = [b for b in all_bugs if b.get("verdict") == "inconclusive"]
        hallucinated = [b for b in all_bugs if b.get("verdict") == "likely_hallucination"]
        passthrough = [b for b in all_bugs if b.get("verdict") in ("pass", "passthrough", None)]

        print(f"\n[Signal Filter] Incoming from Stage 1:")
        print(f"    Confirmed bugs: {len(confirmed)}")
        print(f"    Inconclusive: {len(inconclusive)}")
        print(f"    Hallucinations (will drop): {len(hallucinated)}")
        print(f"    Passthrough (exceptions/failures): {len(passthrough)}")

        # ── Step 2: Drop hallucinations ──
        surviving_bugs = confirmed + inconclusive + passthrough
        validation_state.verified_bugs = surviving_bugs

        print(f"    Surviving bugs for Layer 3: {len(surviving_bugs)}")

        # ── Step 3: Prepare test suite for Layer 3 ──
        tests = validation_state.executed_tests

        if not tests:
            print("\n[Signal Filter] No executed tests — skipping Layer 3")
            return

        # ── Step 4: Generate mutants ──
        print(f"\n[Signal Filter] Running Layer 3 — mutation testing")

        mutants = self.mutation_engine.generate_mutants(source_code)

        if not mutants:
            print("    No mutants generated — skipping mutation runner")
            return

        # ── Step 5: Get original results for comparison ──
        original_results = self.get_original_results(
            source_code, tests, execution_model
        )

        if not original_results:
            print("    Failed to get original results — skipping mutation runner")
            return

        # ── Step 6: Run mutation testing ──
        mutation_results = self.mutation_runner.run_against_mutants(
            mutants, tests, execution_model, original_results
        )

        validation_state.mutation_results = mutation_results

        # ── Step 7: Summary ──
        print(f"\n[Signal Filter] Layer 3 complete")
        print(f"    {validation_state.summary()}")

    def get_original_results(self, source_code, tests, execution_model):
        """
        Runs test suite against original code to get baseline results.

        NOTE: Stage 1 already ran these tests but raw per-test results
        (status, output) are not preserved in Stage 1 output.
        Future optimization: include raw results in Stage 1 output.
        """
        from Stage1.Tools.test_executor import run_tests

        try:
            results, _ = run_tests(source_code, tests, execution_model)
            return results
        except Exception as e:
            print(f"    [Signal Filter] Original execution failed: {e}")
            return None

    # ──────────────────────────────────────────────
    # Placeholders: Future Increment
    # ──────────────────────────────────────────────

    def selective_mutation(self, validation_state):
        """
        Future: Only generate mutants for code regions
        where bugs were found. Reduces mutant count and
        focuses mutation testing on suspicious areas.
        """
        # TODO: extract line ranges from bug reports
        # TODO: pass target lines to mutation_engine
        raise NotImplementedError

    def adaptive_mutant_count(self, validation_state):
        """
        Future: Adjust MAX_MUTANTS based on code complexity
        from structural features. More complex code gets
        more mutants for thorough validation.
        """
        # TODO: read structural_features from validation_state
        # TODO: scale MAX_MUTANTS proportionally
        raise NotImplementedError

    def feedback_to_stage1(self, validation_state):
        """
        Future: Use mutation results to inform Stage 1
        in the next pipeline run. Strategies that produce
        more mutant-killing tests get higher reward.
        """
        # TODO: persist mutation scores per strategy
        # TODO: feed back into Hybrid_Search reward system
        raise NotImplementedError