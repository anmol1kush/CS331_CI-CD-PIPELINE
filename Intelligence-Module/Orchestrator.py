"""
Pipeline Orchestrator
Coordinates Stage0 → Stage1 → Stage2
"""

from Stage0.Stage0_Compile import file_reader
from Stage1.Pipeline.Stage1_pipeline import run_stage1
from Stage2.Pipeline.validation_pipeline import run_stage2
from cost_modes import get_mode
from Stage1.config import apply_mode_overrides
import json
import os


class Pipeline_Orchestrator:
    def __init__(self, file_path: str, user_context: str = None, mode: str = None):
        self.file_path = file_path
        self.user_context = user_context
        self.mode_config = get_mode(mode)
        self.source_code = None
        self.stage0_output = None
        self.stage1_output = None
        self.stage2_output = None

    def load_source(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.source_code = f.read()

    def run_stage_0(self):
        self.stage0_output = file_reader(self.file_path)
        return self.stage0_output

    def run_stage_1(self, user_context=None):
        self.stage1_output = run_stage1(self.stage0_output, self.source_code, user_context=user_context)
        return self.stage1_output

    # def run_stage_2(self):
    #     self.stage2_output = run_stage2(self.stage1_output)
    #     return self.stage2_output

    def run_stage_2(self):
        self.stage2_output = run_stage2(
            self.stage1_output,
            max_mutants=self.mode_config.get("max_mutants")
        )
        return self.stage2_output

    def run_pipeline(self):
        # Apply mode overrides before pipeline starts
        apply_mode_overrides(self.mode_config)

        # Load source code
        self.load_source()

        # Run Stage0
        stage0_result = self.run_stage_0()

        # Gate
        if stage0_result["status"] != "PASS":
            return {
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None,
                "stage2": None
            }

        # Run Stage1
        stage1_result = self.run_stage_1(user_context=self.user_context)

        # Run Stage2
        stage2_result = self.run_stage_2()

        return {
            "pipeline_status": "STAGE_2_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result,
            "stage2": stage2_result
        }

if __name__ == "__main__":
    import sys
    
    # Get file path from command line argument, environment variable, or default to uploads folder
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Look for the most recent file in uploads directory
        uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        if os.path.exists(uploads_dir):
            files = [os.path.join(uploads_dir, f) for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
            if files:
                file_path = max(files, key=os.path.getctime)  # Get most recently created file
            else:
                print("Error: No files found in uploads directory")
                sys.exit(1)
        else:
            print("Error: uploads directory not found")
            sys.exit(1)

    print(f"Processing file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    pipeline = Pipeline_Orchestrator(file_path)
    result = pipeline.run_pipeline()


    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)

    print(f"\nPipeline Status: {result['pipeline_status']}")

    print("\n" + "-" * 40)
    print("STAGE 0 — Compilation Check")
    print("-" * 40)
    print(json.dumps(result['stage0'], indent=2, default=str))

    if result.get('stage1'):
        print("\n" + "-" * 40)
        print("STAGE 1 — Semantic Analysis & Testing")
        print("-" * 40)

        stage1 = result['stage1']

        print(f"\n  Language: {stage1['language']}")
        print(f"  Execution Model: {stage1['execution_model']}")

        print("\n  Structural Features:")
        print(json.dumps(stage1['structural_features'], indent=4, default=str))

        print("\n  Coverage:")
        print(f"    Line:   {stage1['coverage']['line']}")
        print(f"    Branch: {stage1['coverage']['branch']}")

        print(f"\n  Bugs Summary:")
        print(f"    Exceptions:       {len(stage1['bugs']['exceptions'])}")
        print(f"    Failures:         {len(stage1['bugs']['failures'])}")
        print(f"    Incorrect Outputs: {len(stage1['bugs']['incorrect_outputs'])}")

        print(f"\n  Tests Executed: {len(stage1['executed_tests'])}")

        # All generated test cases
        test_cases = stage1.get('generated_test_cases', [])
        print(f"\n  Generated Tests Cases: {len(test_cases)}")
        print(f"\n  Tests Case Details:")
        for i, test in enumerate(test_cases):
            print(f"    Tests {i + 1}:")
            print(f"      Strategy: {test.get('strategy')}")
            print(f"      Method:   {test.get('method_name')}")
            print(f"      Input:    {test.get('input')}")
            print(f"      Expected: {test.get('expected_output')}")
            print(f"      Mode:     {test.get('comparison_mode')}")
            print(f"      Verdict:  {test.get('verdict', 'N/A')}")
            print(f"      Confidence: {test.get('validation_confidence', 'N/A')}")

        # Bug details — at most 3
        all_bugs = []
        for bug in stage1['bugs']['exceptions']:
            bug['type'] = 'exception'
            all_bugs.append(bug)
        for bug in stage1['bugs']['failures']:
            bug['type'] = 'failure'
            all_bugs.append(bug)
        for bug in stage1['bugs']['incorrect_outputs']:
            bug['type'] = 'incorrect_output'
            all_bugs.append(bug)

        if all_bugs:
            print(f"\n  Bug Details (showing {min(3, len(all_bugs))} of {len(all_bugs)}):")
            for i, bug in enumerate(all_bugs[:3]):
                print(f"    Bug {i + 1}:")
                print(f"      Type:     {bug.get('type')}")
                print(f"      Strategy: {bug.get('strategy', 'N/A')}")
                print(f"      Input:    {bug.get('input', 'N/A')}")
                print(f"      Confidence: {bug.get('validation_confidence', 'N/A')}")
                if bug.get('type') == 'incorrect_output':
                    print(f"      Expected: {bug.get('expected', 'N/A')}")
                    print(f"      Actual:   {bug.get('actual', 'N/A')}")
                    print(f"      Verdict:  {bug.get('verdict', 'N/A')}")
                else:
                    print(f"      Error:    {bug.get('error', 'N/A')}")

        # Bug summary by strategy
        print(f"\n  Bug Summary by Strategy:")
        strategy_counts = {}
        for bug in all_bugs:
            strategy = bug.get('strategy', 'unknown')
            if strategy not in strategy_counts:
                strategy_counts[strategy] = 0
            strategy_counts[strategy] += 1

        for strategy, count in strategy_counts.items():
            print(f"    {strategy}: {count} bugs")

        # Bug summary by type
        print(f"\n  Bug Summary by Type:")
        print(f"    Exceptions:        {len(stage1['bugs']['exceptions'])}")
        print(f"    Failures:          {len(stage1['bugs']['failures'])}")
        print(f"    Incorrect Outputs: {len(stage1['bugs']['incorrect_outputs'])}")
        print(f"    Total:             {len(all_bugs)}")

    if result.get('stage2'):
        print("\n" + "-" * 40)
        print("STAGE 2 — Validation")
        print("-" * 40)

        stage2 = result['stage2']

        print(f"\n  Bug Summary:")
        print(f"    Confirmed:    {stage2['bugs']['summary']['confirmed_count']}")
        print(f"    Inconclusive: {stage2['bugs']['summary']['inconclusive_count']}")
        print(f"    Hallucinated: {stage2['bugs']['summary']['hallucinated_count']}")
        print(f"    Total incoming: {stage2['bugs']['summary']['total_incoming']}")
        print(f"    After filtering: {stage2['bugs']['summary']['total_after_filtering']}")

        print(f"\n  Test Suite:")
        print(f"    Total generated: {stage2['tests']['total_generated']}")
        print(f"    Valid (shown to user): {stage2['tests']['total_valid']}")
        print(f"    Filtered (coverage only): {stage2['tests']['filtered_count']}")

        if stage2.get('mutation_testing'):
            mt = stage2['mutation_testing']
            print(f"\n  Mutation Testing:")
            print(f"    Total mutants: {mt.get('total_mutants', 0)}")
            print(f"    Killed: {mt.get('killed', 0)}")
            print(f"    Survived: {mt.get('survived', 0)}")
            print(f"    Mutation score: {mt.get('mutation_score', 0):.2%}")

        print(f"\n  Weak tests: {len(stage2.get('weak_tests', []))}")
        print(f"  Strong tests: {len(stage2.get('strong_tests', []))}")

    # Save results
    if result.get('stage1'):
        if result.get('stage2'):
            save_data = {
                "generated_test_cases": result["stage1"].get("generated_test_cases", []),
                "stage1_bugs": result["stage1"]["bugs"],
                "stage2_validation": result["stage2"]
            }
        else:
            save_data = {
                "generated_test_cases": result["stage1"].get("generated_test_cases", []),
                "bugs": result["stage1"]["bugs"]
            }

        output_filename = "Test_Cases.json"
        output_path = r"Stage1/Tests"

        full_path = os.path.join(output_path, output_filename)

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, default=str)

        print(f"\n  Results saved to: {output_path}")

    print("\n\n\n", result)