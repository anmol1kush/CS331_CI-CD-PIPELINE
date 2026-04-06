"""
Execution Verifier for Stage-2 (Layer 2)

Independently verifies whether a flagged incorrect_output bug
is a real bug or a hallucinated expected_output.

Method:
    For each bug, makes an independent LLM call with a DIFFERENT
    prompt structure — asks the LLM to trace through the code
    step-by-step and compute the output, rather than predict it.
    (Based on TestChain's ReAct approach)

Triangulation logic:
    independent_result == actual_output     → likely_hallucination
    independent_result == expected_output   → confirmed_bug
    independent_result matches neither      → inconclusive

Input:
    - Bug reports with: input, expected_output, actual output
    - Source code and execution model

Output:
    - Each bug tagged with verdict: confirmed_bug / likely_hallucination / inconclusive
    - Each bug tagged with independent_output for audit trail

Integration point:
    Called by signal_filter.py for all incorrect_output bugs
    regardless of confidence score.

Current increment:
    - Python source code (LC/CP files)
    - Single independent LLM call per bug

Future increment placeholders:
    - Multi-model cross-verification (use second LLM provider)
    - Property-based verification (check output satisfies invariants)
    - Metamorphic relation checking (if f(x)=y then f(2x)=?)
"""

import json


# Verdicts — used by signal_filter and report_builder
VERDICT_CONFIRMED = "confirmed_bug"
VERDICT_HALLUCINATION = "likely_hallucination"
VERDICT_INCONCLUSIVE = "inconclusive"


class Execution_Verifier:
    def __init__(self, provider):
        """
        Args:
            provider: an instance of Base_LLM_Provider (e.g., Gemini_Provider)
        """
        self.provider = provider

    def verify_bugs(self, bugs, source_code, execution_model):
        """
        Verifies each incorrect_output bug via independent LLM re-solve.

        Args:
            bugs: list of incorrect_output bug dicts from Stage 1
            source_code: the program under test
            execution_model: callable_method / stdin_program / script

        Returns:
            list of bug dicts with added fields:
                - verdict: confirmed_bug / likely_hallucination / inconclusive
                - independent_output: what the independent solve produced
        """
        verified_bugs = []

        for bug in bugs:
            verdict, independent_output = self.verify_single_bug(
                bug, source_code, execution_model
            )

            bug["verdict"] = verdict
            bug["independent_output"] = independent_output

            print(
                f"    [Execution Verifier] "
                f"Input: {bug.get('input')} | "
                f"Expected: {bug.get('expected')} | "
                f"Actual: {bug.get('actual')} | "
                f"Independent: {independent_output} | "
                f"Verdict: {verdict}"
            )

            verified_bugs.append(bug)

        return verified_bugs

    def verify_single_bug(self, bug, source_code, execution_model):
        """
        Makes one independent LLM call to re-solve for a specific input.
        Compares the independent result against both actual and expected.

        Returns:
            (verdict, independent_output)
        """
        prompt = self.build_verification_prompt(
            bug, source_code, execution_model
        )

        try:
            response = self.provider.generate(prompt)
            independent_output = self.parse_response(response)
        except Exception as e:
            print(f"    [Execution Verifier] LLM call failed: {e}")
            return VERDICT_INCONCLUSIVE, None

        if independent_output is None:
            return VERDICT_INCONCLUSIVE, None

        actual = bug.get("actual")
        expected = bug.get("expected")
        comparison_mode = bug.get("comparison_mode", "exact")

        matches_actual = self.compare(independent_output, actual, comparison_mode)
        matches_expected = self.compare(independent_output, expected, comparison_mode)

        if matches_actual and not matches_expected:
            return VERDICT_HALLUCINATION, independent_output

        if matches_expected and not matches_actual:
            return VERDICT_CONFIRMED, independent_output

        if matches_actual and matches_expected:
            # actual == expected == independent — shouldn't be a bug at all
            # edge case: bug_detector flagged it but all three agree
            return VERDICT_HALLUCINATION, independent_output

        # matches neither
        return VERDICT_INCONCLUSIVE, independent_output

    def build_verification_prompt(self, bug, source_code, execution_model):
        """
        Builds a step-by-step trace prompt.
        Different from llm_test_generator's prompt — forces
        the LLM into computation mode rather than prediction mode.
        """
        test_input = bug.get("input")
        method_name = bug.get("method_name")

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
- The output must match what the program would actually produce for this input
"""
        return prompt

    def parse_response(self, response):
        """
        Extracts expected_output from verification response.
        """
        try:
            data = json.loads(response)
            return data.get("expected_output")
        except (json.JSONDecodeError, AttributeError):
            return None

    def compare(self, value_a, value_b, comparison_mode="exact"):
        """
        Compares two values using the same logic as bug_detector.
        Reuses comparison modes: exact, unordered, float_tolerance, etc.
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

    # ──────────────────────────────────────────────
    # Placeholders: Future Increment Verification
    # ──────────────────────────────────────────────

    def cross_model_verify(self, bug, source_code, execution_model):
        """
        Future: Use a second LLM provider (e.g., OpenAI) to
        independently verify, reducing single-model bias.
        """
        # TODO: accept secondary_provider in __init__
        # TODO: make same verification call via different model
        # TODO: if both models agree → stronger signal
        raise NotImplementedError

    def property_based_verify(self, bug, source_code, execution_model):
        """
        Future: Check if the output satisfies known invariants
        without needing the exact expected value.
        e.g., sorted output should be sorted, sum should be conserved
        """
        # TODO: extract properties from source code or user hints
        # TODO: verify actual output against properties
        raise NotImplementedError

    def metamorphic_verify(self, bug, source_code, execution_model):
        """
        Future: Generate related inputs and check if outputs
        maintain expected relationships.
        e.g., if f([1,2,3]) = 6 then f([1,2,3,0]) should also = 6
        """
        # TODO: define metamorphic relations per problem type
        # TODO: generate related inputs
        # TODO: execute and compare relationships
        raise NotImplementedError