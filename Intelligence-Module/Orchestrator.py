"""
Pipeline Orchestrator
Coordinates Stage0 → Stage1
"""

from Stage0.Stage0_Compile import file_reader
from Stage1.Deterministic.Stage1_Semantic import Semantic_Engine


class Pipeline_Orchestrator:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.stage0_output = None
        self.stage1_output = None

    def run_stage_0(self):
        self.stage0_output = file_reader(self.file_path)
        return self.stage0_output

    def run_stage_1(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        engine = Semantic_Engine(self.stage0_output, source_code)
        self.stage1_output = engine.run()

        return self.stage1_output

    def run_pipeline(self):
        # Run Stage0
        stage0_result = self.run_stage_0()

        # Gate
        if stage0_result["status"] != "PASS":
            return {
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None
            }

        # Run Stage1.1
        stage1_result = self.run_stage_1()

        return {
            "pipeline_status": "STAGE_1_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result
        }



file_path = r"/home/mohit-kumawat/Desktop/projects/CS331_CI-CD-PIPELINE/Intelligence-Module/Stage1/Tests/LC Test.py"
#file_path = r"C:\Users\hp\Desktop\Leet Code\Optimised and Learnings\4 - Median of Two Sorted arrays_alt sol.py"
#file_path = r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS 201 (Algorithm)\Mid Sem Algo\Q2.cpp"
pipeline = Pipeline_Orchestrator(file_path)
result = pipeline.run_pipeline()
print(result)