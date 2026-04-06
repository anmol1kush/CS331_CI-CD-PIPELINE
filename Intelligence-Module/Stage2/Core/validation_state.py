"""
Validation State for Stage-2

Holds intermediate and final results as bugs move through
Layer 2 (execution verification) and Layer 3 (mutation testing).

Similar role to State.py in Stage 1 — structured storage
with access methods, no complex logic.


Lifecycle:
    1. Created by validation_pipeline with Stage 1 output
    2. signal_filter drops hallucinations and runs Layer 3 (mutation testing)
    3. report_builder reads to produce final output

Current increment:
    - Flat storage with helper methods
    - In-memory only

Future increment placeholders:
    - Persistence across pipeline runs for trend analysis
    - Diff against previous validation state for regression detection
"""


class Validation_State:
    def __init__(self, stage1_output):
        """
        Args:
            stage1_output: the complete output dict from Stage 1 pipeline
        """
        # preserve full stage1 output for reference
        self.stage1_output = stage1_output

        # extracted from stage1 for convenience
        self.language = stage1_output.get("language")
        self.execution_model = stage1_output.get("execution_model")
        self.source_code = stage1_output.get("source_code", "")
        self.structural_features = stage1_output.get("structural_features", {})

        # test suite from stage1
        self.executed_tests = stage1_output.get("executed_tests", [])
        self.generated_tests = stage1_output.get("generated_test_cases", [])

        # coverage from stage1 (passed through to final output)
        self.coverage = stage1_output.get("coverage", {})

        # incoming bugs from stage1 — separated by type
        bugs = stage1_output.get("bugs", {})
        self.exceptions = list(bugs.get("exceptions", []))
        self.failures = list(bugs.get("failures", []))
        self.incorrect_outputs = list(bugs.get("incorrect_outputs", []))

        # Bugs after filtering (hallucinations removed) — populated by signal_filter
        self.verified_bugs = []

        # Layer 3 results — populated by signal_filter
        self.mutation_results = None

        # final classifications — populated by report_builder
        self.final_classifications = []

    def get_all_incoming_bugs(self):
        """Returns all bugs from Stage 1 as a flat list with type tag."""
        all_bugs = []

        for bug in self.exceptions:
            bug["bug_type"] = "exception"
            all_bugs.append(bug)

        for bug in self.failures:
            bug["bug_type"] = "failure"
            all_bugs.append(bug)

        for bug in self.incorrect_outputs:
            bug["bug_type"] = "incorrect_output"
            all_bugs.append(bug)

        return all_bugs

    def get_bugs_by_verdict(self, verdict):
        def get_bugs_by_verdict(self, verdict):
            """
            Returns bugs matching a specific verdict from Stage 1 triangulation.
            e.g., get_bugs_by_verdict("confirmed_bug")
            """
            return [b for b in self.verified_bugs if b.get("verdict") == verdict]

    def get_weak_tests(self):
        """
        Returns test indices with zero kill count from Layer 3.
        These are tests whose oracles are suspect.
        """
        if not self.mutation_results:
            return []

        test_scores = self.mutation_results.get("test_scores", {})
        return [
            idx for idx, score in test_scores.items()
            if score["kill_count"] == 0
        ]

    def get_strong_tests(self):
        """
        Returns test indices with kill_count > 0 from Layer 3.
        These tests have validated discriminative power.
        """
        if not self.mutation_results:
            return []

        test_scores = self.mutation_results.get("test_scores", {})
        return [
            idx for idx, score in test_scores.items()
            if score["kill_count"] > 0
        ]

    def summary(self):
        mutation_summary = {}
        if self.mutation_results:
            mutation_summary = self.mutation_results.get("summary", {})

        return {
            "incoming_bugs": {
                "exceptions": len(self.exceptions),
                "failures": len(self.failures),
                "incorrect_outputs": len(self.incorrect_outputs),
                "total": len(self.exceptions) + len(self.failures) + len(self.incorrect_outputs)
            },
            "surviving_bugs": len(self.verified_bugs),
            "by_verdict": {
                "confirmed_bug": len(self.get_bugs_by_verdict("confirmed_bug")),
                "inconclusive": len(self.get_bugs_by_verdict("inconclusive")),
                "passthrough": len(self.get_bugs_by_verdict("passthrough"))
            },
            "layer3_mutation": mutation_summary,
            "weak_tests": len(self.get_weak_tests()),
            "strong_tests": len(self.get_strong_tests()),
            "final_classifications": len(self.final_classifications)
        }

    # ──────────────────────────────────────────────
    # Placeholders: Future Increment
    # ──────────────────────────────────────────────

    def persist(self, path):
        """
        Future: Save validation state to disk for trend analysis
        across multiple pipeline runs on successive commits.
        """
        # TODO: serialize to JSON (exclude non-serializable fields)
        # TODO: append to history file
        raise NotImplementedError

    def diff(self, previous_state):
        """
        Future: Compare against a previous validation state
        to detect regressions — new bugs appearing, old bugs
        disappearing, test strength changes.
        """
        # TODO: compare bug lists, coverage, mutation scores
        # TODO: flag new bugs and resolved bugs
        raise NotImplementedError