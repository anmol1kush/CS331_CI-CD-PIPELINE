"""
Oracle Verifier for Stage-1 (Triangulation-Based)

Verifies test results by making an independent LLM call
that traces through the code step-by-step to produce
a verification output I.

Triangulates three values:
    A = actual output from code execution
    E = expected output from original LLM prediction
    I = independent output from step-by-step verification

Four possible outcomes:
    O1: A = E = I  → all agree        → verdict: pass
    O2: E = I ≠ A  → bug confirmed    → verdict: confirmed_bug
    O3: I = A ≠ E  → E was wrong      → verdict: likely_hallucination
    O4: all differ → no agreement     → verdict: inconclusive

Confidence scores derived from Bayesian posterior using
Condorcet's Jury Theorem framework:
    O1: 0.998   O2: 0.829   O3: 0.000   O4: 0.432

Integration point:
    Called by Transition.py inside run_test_suite(),
    AFTER test_executor runs and BEFORE bug_detector consumes results.

Research backing:
    - Condorcet's Jury Theorem (1785) — majority voting correctness
    - Konstantinou et al. (2024) — p_E ≈ 0.50 baseline oracle accuracy
    - CoT prompting research — Δp ≈ 0.10 improvement for step-by-step trace
    - SelfCheckGPT (Manakul et al., EMNLP 2023) — independent sampling principle
"""

import json
from Stage1.config import ENABLE_TRIANGULATION, VERIFICATION_TEMPERATURE


# Fixed confidence scores from Bayesian posterior
# Derived using p_E=0.50, p_I=0.60, ρ=0.3, δ=0.1, P(C)=0.75
CONFIDENCE_O1 = 0.998     # all agree — strong pass
CONFIDENCE_O2 = 0.829     # E=I≠A — confirmed bug
CONFIDENCE_O3 = 0.000     # I=A≠E — hallucination, removed
CONFIDENCE_O4 = 0.432     # all differ — inconclusive

# Verdict labels
VERDICT_PASS = "pass"
VERDICT_CONFIRMED = "confirmed_bug"
VERDICT_HALLUCINATION = "likely_hallucination"
VERDICT_INCONCLUSIVE = "inconclusive"


class Oracle_Verifier:
    def __init__(self, provider):
        """
        Args:
            provider: instance of Base_LLM_Provider (e.g., Gemini_Provider)
                      Must support generate(prompt, temperature=...)
        """
        self.provider = provider

    def verify_results(self, tests, results, source_code, execution_model):
        """
        Verifies each test result via independent LLM step-by-step trace.
        Called AFTER test_executor, receives both tests (with E) and results (with A).

        Args:
            tests: list of test dicts (each has expected_output = E)
            results: list of result dicts from test_executor (each has output = A)
            source_code: the program under test
            execution_model: callable_method / stdin_program / script

        Returns:
            list of test dicts with added fields:
                - verdict: pass / confirmed_bug / likely_hallucination / inconclusive
                - validation_confidence: float
                - independent_output: what the verification LLM produced
        """
        for i, test in enumerate(tests):
            if i >= len(results):
                test["verdict"] = VERDICT_INCONCLUSIVE
                test["validation_confidence"] = CONFIDENCE_O4
                test["independent_output"] = None
                continue

            result = results[i]
            status = result.get("status")

            # if execution itself failed (exception/timeout/crash),
            # skip verification — no actual output to triangulate
            if status != "success":
                test["verdict"] = VERDICT_PASS
                test["validation_confidence"] = CONFIDENCE_O1
                test["independent_output"] = None
                continue

            expected = test.get("expected_output")

            # if no expected output (e.g., script mode), skip verification
            if expected is None:
                test["verdict"] = VERDICT_PASS
                test["validation_confidence"] = CONFIDENCE_O1
                test["independent_output"] = None
                continue

            actual = result.get("output")

            # if actual == expected, test passed — but still verify for false negatives
            # if actual != expected, test failed — verify if E was hallucinated

            # get independent output I
            independent = self.get_independent_output(
                test, source_code, execution_model
            )

            # determine outcome
            comparison_mode = test.get("comparison_mode", "exact")
            outcome = self.determine_outcome(
                actual, expected, independent, comparison_mode
            )

            # assign verdict and confidence
            if outcome == "O1":
                test["verdict"] = VERDICT_PASS
                test["validation_confidence"] = CONFIDENCE_O1
            elif outcome == "O2":
                test["verdict"] = VERDICT_CONFIRMED
                test["validation_confidence"] = CONFIDENCE_O2
            elif outcome == "O3":
                test["verdict"] = VERDICT_HALLUCINATION
                test["validation_confidence"] = CONFIDENCE_O3
            elif outcome == "O4":
                test["verdict"] = VERDICT_INCONCLUSIVE
                test["validation_confidence"] = CONFIDENCE_O4

            test["independent_output"] = independent

            print(
                f"    [Oracle Verifier] "
                f"Test {i} | "
                f"A={actual} | E={expected} | I={independent} | "
                f"Outcome={outcome} | "
                f"Verdict={test['verdict']} | "
                f"Confidence={test['validation_confidence']}"
            )

        return tests

    def get_independent_output(self, test, source_code, execution_model):
        """
        Makes one LLM call with step-by-step trace prompt.
        Returns the independently computed output, or None if call fails.
        """
        prompt = self.build_trace_prompt(test, source_code, execution_model)

        try:
            response = self.provider.generate(
                prompt, temperature=VERIFICATION_TEMPERATURE
            )
            return self.parse_response(response)
        except Exception as e:
            print(f"    [Oracle Verifier] Verification call failed: {e}")
            return None

    def build_trace_prompt(self, test, source_code, execution_model):
        """
        Builds a step-by-step trace prompt.
        Forces the LLM into computation mode rather than prediction mode.
        """
        test_input = test.get("input")
        method_name = test.get("method_name")

        if execution_model == "callable_method":
            input_desc = (
                f"Call method '{method_name}' on class Solution "
                f"with arguments: {json.dumps(test_input)}"
            )
        elif execution_model == "stdin_program":
            input_desc = f"Provide this stdin input:\n{test_input}"
        else:
            input_desc = "Run the script with no input"

        prompt = f"""You are a code execution engine.
Given the following program and input, determine the EXACT output
by tracing through the code step by step.

Program source code:
--------------------
{source_code}
--------------------

Input:
{input_desc}

Instructions:
1. Read the code carefully
2. Trace execution line by line for the given input
3. Track all variable values at each step
4. Determine the final output

Respond with ONLY valid JSON in this format:
{{"step_by_step": "<brief trace of key steps>", "expected_output": <the_output>}}

Rules:
- You MUST trace through the actual code logic, do not guess
- Return ONLY the JSON object, no other text
- The output must match what the program would actually produce
"""
        return prompt

    def parse_response(self, response):
        """Extracts expected_output from verification response."""
        try:
            data = json.loads(response)
            return data.get("expected_output")
        except (json.JSONDecodeError, AttributeError):
            return None

    def determine_outcome(self, actual, expected, independent, comparison_mode):
        """
        Compares A, E, I to determine which outcome occurred.

        Returns: "O1", "O2", "O3", or "O4"
        """
        if independent is None:
            return "O4"

        ae = self.compare(actual, expected, comparison_mode)
        ai = self.compare(actual, independent, comparison_mode)
        ei = self.compare(expected, independent, comparison_mode)

        if ae and ai and ei:
            return "O1"     # all agree

        if ei and not ae:
            return "O2"     # E=I≠A, bug confirmed

        if ai and not ae:
            return "O3"     # I=A≠E, hallucination

        return "O4"         # all differ or partial matches

    def compare(self, value_a, value_b, comparison_mode="exact"):
        """
        Compares two values using the appropriate comparison mode.
        """
        if value_a == value_b:
            return True

        if comparison_mode == "float_tolerance":
            if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
                return abs(value_a - value_b) < 1e-6
            return False

        if comparison_mode == "unordered":
            if isinstance(value_a, list) and isinstance(value_b, list):
                if len(value_a) == len(value_b):
                    try:
                        return sorted(value_a) == sorted(value_b)
                    except TypeError:
                        return False
            return False

        if comparison_mode == "unordered_nested":
            if isinstance(value_a, list) and isinstance(value_b, list):
                if len(value_a) == len(value_b):
                    return self.normalize(value_a) == self.normalize(value_b)
            return False

        return False

    def normalize(self, value):
        """Normalize nested lists for unordered comparison."""
        if isinstance(value, list):
            normalized = [self.normalize(item) for item in value]
            try:
                return sorted(normalized)
            except TypeError:
                return normalized
        return value