"""
Pipeline Orchestrator
Coordinates Stage0 → Stage1
"""

from Stage0.Stage0_Compile import file_reader
from Stage1.Pipeline.Stage1_pipeline import run_stage1
import json
import os


class Pipeline_Orchestrator:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.source_code = None
        self.stage0_output = None
        self.stage1_output = None

    def load_source(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.source_code = f.read()

    def run_stage_0(self):
        self.stage0_output = file_reader(self.file_path)
        return self.stage0_output

    def run_stage_1(self):
        self.stage1_output = run_stage1(self.stage0_output, self.source_code)
        return self.stage1_output

    def run_pipeline(self):
        # Load source code
        self.load_source()

        # Run Stage0
        stage0_result = self.run_stage_0()

        # Gate
        if stage0_result["status"] != "PASS":
            return {
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None
            }

        # Run Stage1
        stage1_result = self.run_stage_1()


        return {
            "pipeline_status": "STAGE_1_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result
        }

    def get_output_string(self, result):
        output = "\n" + "=" * 60
        output += "\nPIPELINE RESULT"
        output += "\n" + "=" * 60

        output += f"\n\nPipeline Status: {result['pipeline_status']}"

        output += "\n\n" + "-" * 40
        output += "\nSTAGE 0 — Compilation Check"
        output += "\n" + "-" * 40
        output += "\n" + json.dumps(result['stage0'], indent=2, default=str)

        if result.get('stage1'):
            output += "\n\n" + "-" * 40
            output += "\nSTAGE 1 — Semantic Analysis & Testing"
            output += "\n" + "-" * 40

            stage1 = result['stage1']

            output += f"\n\n  Language: {stage1['language']}"
            output += f"\n  Execution Model: {stage1['execution_model']}"

            output += "\n\n  Structural Features:"
            output += "\n" + json.dumps(stage1['structural_features'], indent=4, default=str)

            output += "\n\n  Coverage:"
            output += f"\n    Line:   {stage1['coverage']['line']}"
            output += f"\n    Branch: {stage1['coverage']['branch']}"

            output += f"\n\n  Bugs Summary:"
            output += f"\n    Exceptions:       {len(stage1['bugs']['exceptions'])}"
            output += f"\n    Failures:         {len(stage1['bugs']['failures'])}"
            output += f"\n    Incorrect Outputs: {len(stage1['bugs']['incorrect_outputs'])}"

            output += f"\n\n  Tests Executed: {len(stage1['executed_tests'])}"

            # All generated test cases
            test_cases = stage1.get('generated_test_cases', [])
            output += f"\n\n  Generated Tests Cases: {len(test_cases)}"
            output += f"\n\n  Tests Case Details:"
            for i, test in enumerate(test_cases):
                output += f"\n    Tests {i + 1}:"
                output += f"\n      Strategy: {test.get('strategy')}"
                output += f"\n      Method:   {test.get('method_name')}"
                output += f"\n      Input:    {test.get('input')}"
                output += f"\n      Expected: {test.get('expected_output')}"
                output += f"\n      Mode:     {test.get('comparison_mode')}"

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
                output += f"\n\n  Bug Details (showing {min(3, len(all_bugs))} of {len(all_bugs)}):"
                for i, bug in enumerate(all_bugs[:3]):
                    output += f"\n    Bug {i + 1}:"
                    output += f"\n      Type:     {bug.get('type')}"
                    output += f"\n      Strategy: {bug.get('strategy', 'N/A')}"
                    output += f"\n      Input:    {bug.get('input', 'N/A')}"
                    if bug.get('type') == 'incorrect_output':
                        output += f"\n      Expected: {bug.get('expected', 'N/A')}"
                        output += f"\n      Actual:   {bug.get('actual', 'N/A')}"
                    else:
                        output += f"\n      Error:    {bug.get('error', 'N/A')}"

            # Bug summary by strategy
            output += f"\n\n  Bug Summary by Strategy:"
            strategy_counts = {}
            for bug in all_bugs:
                strategy = bug.get('strategy', 'unknown')
                if strategy not in strategy_counts:
                    strategy_counts[strategy] = 0
                strategy_counts[strategy] += 1

            for strategy, count in strategy_counts.items():
                output += f"\n    {strategy}: {count} bugs"

            # Bug summary by type
            output += f"\n\n  Bug Summary by Type:"
            output += f"\n    Exceptions:        {len(stage1['bugs']['exceptions'])}"
            output += f"\n    Failures:          {len(stage1['bugs']['failures'])}"
            output += f"\n    Incorrect Outputs: {len(stage1['bugs']['incorrect_outputs'])}"
            output += f"\n    Total:             {len(all_bugs)}"

            # Save test cases and bugs to temp file
            import tempfile

            if result.get('stage1'):
                save_data = {
                    "generated_test_cases": result["stage1"].get("generated_test_cases", []),
                    "bugs": result["stage1"]["bugs"]
                }

                output_filename = "Test_Cases.json"
                output_path = r"Stage1/Tests"

                full_path = os.path.join(output_path, output_filename)

                with open(full_path, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, indent=2, default=str)

                output += f"\n\n  Results saved to: {output_path}"

        output += "\n\n\n" + str(result)
        return output

if __name__ == "__main__":
    #file_path = r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\Stage1\Tests\LC Tests.py"
    # file_path = r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS 201 (Algorithm)\Mid Sem Algo\Q2.cpp"
    file_path = r"./Stage1/Tests/CP Test.py"
    #file_path = r"./Stage1/Tests/Test5.py"

    pipeline = Pipeline_Orchestrator(file_path)
    result = pipeline.run_pipeline()

    output = pipeline.get_output_string(result)
    print(output)
