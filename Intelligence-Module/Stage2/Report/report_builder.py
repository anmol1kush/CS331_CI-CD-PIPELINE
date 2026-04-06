"""
Report Builder for Stage-2

Produces the final validated output that downstream stages consume.
Combines two sources of information:
    - Verdicts from Stage 1 triangulation (confirmed_bug / inconclusive / passthrough)
    - Kill counts from Layer 3 mutation testing (test strength)

Final classification logic:
    confirmed_bug + kills mutants    → confirmed_bug (strongest signal)
    confirmed_bug + kills nothing    → downgrade to inconclusive
    inconclusive + kills mutants     → upgrade to confirmed_bug
    inconclusive + kills nothing     → likely_hallucination
    passthrough (exception/timeout)  → confirmed_bug (execution-level signal)

Test suite separation:
    valid_test_cases:    tests with reliable expected outputs (shown to user)
    coverage_only_tests: tests whose expected output was unreliable
                         (not shown, but coverage contribution preserved)

Current increment:
    - Binary kill count check (killed > 0 or not)
    - Fixed classification logic

Future increment placeholders:
    - Kill ratio weighted classification
    - Trend analysis across pipeline runs
    - Per-strategy effectiveness report
"""


class Report_Builder:
    def __init__(self):
        pass

    def build(self, validation_state):
        """
        Produces the final Stage 2 output.

        Args:
            validation_state: Validation_State with verified_bugs and mutation_results

        Returns:
            dict with final classifications, separated test suites, and summary
        """
        # ── Step 1: Get mutation data ──
        mutation_results = validation_state.mutation_results
        test_scores = {}
        if mutation_results:
            test_scores = mutation_results.get("test_scores", {})

        # ── Step 2: Classify each bug ──
        final_bugs = []

        for bug in validation_state.verified_bugs:
            classification = self.classify_bug(bug, test_scores)
            bug["final_classification"] = classification
            final_bugs.append(bug)

        validation_state.final_classifications = final_bugs

        # ── Step 3: Separate test suite ──
        valid_tests, coverage_only_tests, filtered_count = self.separate_tests(
            validation_state.executed_tests
        )

        # ── Step 4: Build summary ──
        confirmed = [b for b in final_bugs if b["final_classification"] == "confirmed_bug"]
        inconclusive = [b for b in final_bugs if b["final_classification"] == "inconclusive"]
        hallucinated = [b for b in final_bugs if b["final_classification"] == "likely_hallucination"]

        mutation_summary = {}
        if mutation_results:
            mutation_summary = mutation_results.get("summary", {})

        # ── Step 5: Produce final output ──
        output = {
            "stage": 2,
            "status": "STAGE2_COMPLETE",

            "bugs": {
                "confirmed": confirmed,
                "inconclusive": inconclusive,
                "hallucinated": hallucinated,
                "summary": {
                    "confirmed_count": len(confirmed),
                    "inconclusive_count": len(inconclusive),
                    "hallucinated_count": len(hallucinated),
                    "total_incoming": len(validation_state.get_all_incoming_bugs()),
                    "total_after_filtering": len(confirmed) + len(inconclusive)
                }
            },

            "tests": {
                "valid_test_cases": valid_tests,
                "coverage_only_tests": coverage_only_tests,
                "total_generated": len(validation_state.generated_tests),
                "total_valid": len(valid_tests),
                "filtered_count": filtered_count
            },

            "coverage": validation_state.coverage,

            "mutation_testing": mutation_summary,

            "weak_tests": validation_state.get_weak_tests(),
            "strong_tests": validation_state.get_strong_tests()
        }

        print(f"\n[Report Builder] Final report:")
        print(f"    Confirmed bugs: {len(confirmed)}")
        print(f"    Inconclusive: {len(inconclusive)}")
        print(f"    Hallucinations removed: {len(hallucinated)}")
        print(f"    Valid test cases: {len(valid_tests)}")
        print(f"    Coverage-only tests: {len(coverage_only_tests)}")
        if mutation_summary:
            print(f"    Mutation score: {mutation_summary.get('mutation_score', 0):.2%}")

        return output

    def classify_bug(self, bug, test_scores):
        """
        Combines Stage 1 verdict with Layer 3 kill count
        to produce final classification.

        Args:
            bug: bug dict with verdict and validation_confidence from Stage 1
            test_scores: dict of {test_index: {"kill_count": int, ...}} from mutation runner

        Returns:
            "confirmed_bug" / "inconclusive" / "likely_hallucination"
        """
        verdict = bug.get("verdict", "passthrough")
        test_id = bug.get("test_id")

        # exceptions and failures are always confirmed
        bug_type = bug.get("bug_type")
        if bug_type in ("exception", "failure"):
            return "confirmed_bug"

        # get kill count for this test from mutation results
        kills = 0
        if test_id is not None and test_scores:
            score = test_scores.get(test_id, test_scores.get(str(test_id)))
            if score:
                kills = score.get("kill_count", 0)

        # combine verdict with kill count
        if verdict == "confirmed_bug":
            if kills > 0:
                return "confirmed_bug"
            else:
                return "inconclusive"

        elif verdict == "inconclusive":
            if kills > 0:
                return "confirmed_bug"
            else:
                return "likely_hallucination"

        elif verdict == "passthrough":
            return "confirmed_bug"

        return "inconclusive"

    def separate_tests(self, executed_tests):
        """
        Separates executed tests into valid and coverage-only.

        valid: tests with reliable expected output (shown to user)
        coverage_only: tests whose expected output was unreliable
                       (coverage preserved, not shown as test cases)

        Returns:
            (valid_tests, coverage_only_tests, filtered_count)
        """
        valid = []
        coverage_only = []

        for test in executed_tests:
            verdict = test.get("verdict")

            if verdict == "likely_hallucination":
                coverage_only.append(test)
            elif verdict == "inconclusive":
                coverage_only.append(test)
            else:
                valid.append(test)

        filtered_count = len(coverage_only)
        return valid, coverage_only, filtered_count

    # ──────────────────────────────────────────────
    # Placeholders: Future Increment
    # ──────────────────────────────────────────────

    def weighted_classification(self, bug, test_scores):
        """
        Future: Use kill_count / total_mutants ratio instead
        of binary kills > 0 check. A test that kills 10 mutants
        is stronger evidence than one that kills 1.
        """
        # TODO: compute kill_ratio = kill_count / total_mutants
        # TODO: combine with validation_confidence as weighted score
        raise NotImplementedError

    def trend_report(self, validation_state, previous_reports):
        """
        Future: Compare against previous pipeline runs.
        Track: new bugs appearing, old bugs resolved,
        test strength improving or degrading over commits.
        """
        # TODO: load previous reports from persistence
        # TODO: diff bug lists and mutation scores
        raise NotImplementedError

    def strategy_effectiveness(self, validation_state):
        """
        Future: Report which test strategies produced the
        most confirmed bugs and strongest tests. Feeds back
        into Stage 1 algorithm for better strategy selection.
        """
        # TODO: group bugs and kill counts by strategy
        # TODO: rank strategies by effectiveness
        raise NotImplementedError