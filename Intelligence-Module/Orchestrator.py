"""
Pipeline Orchestrator
Coordinates Stage0 → Stage1 → Stage2

Batch CI/CD mode entry point: run_pipeline_batch(file_list)

file_entry format:
    {
        "file_path": str,           # required — used for identification & language inference
        "source_code": str          # optional — if absent, read from disk (local dev fallback)
    }
"""

from Stage0.Stage0_Compile import infer_language, compile_test
from Stage1.Pipeline.Stage1_pipeline import run_stage1
from Stage2.Pipeline.validation_pipeline import run_stage2
from cost_modes import get_mode
from Stage1.config import apply_mode_overrides
import os


class Pipeline_Orchestrator:
    def __init__(self, user_context: str = None, mode: str = None):
        self.user_context = user_context
        self.mode_config = get_mode(mode)

    # ──────────────────────────────────────────────
    # Source resolver
    # ──────────────────────────────────────────────

    @staticmethod
    def resolve_source(file_entry: dict) -> str:
        """
        Prefer inline 'source_code'; fall back to reading from disk.
        """
        if "source_code" in file_entry:
            return file_entry["source_code"]
        with open(file_entry["file_path"], "r", encoding="utf-8") as f:
            return f.read()

    # ──────────────────────────────────────────────
    # Batch CI/CD mode
    # ──────────────────────────────────────────────

    def run_pipeline_batch(self, file_list: list):
        """
        Run the pipeline for a batch of files from a git event trigger.

        Args:
            file_list: list of file_entry dicts
                - "file_path": str   (required)
                - "source_code": str (optional — inlined by CI webhook; falls back to disk)

        Returns:
            {
                "pipeline_status": "BATCH_COMPLETE",
                "total_files": int,
                "passed": int,
                "failed_stage0": int,
                "completed": int,
                "skipped": int,
                "results": [per-file result dicts]
            }
        """
        apply_mode_overrides(self.mode_config)

        results = []
        passed = 0
        failed_stage0 = 0
        completed = 0
        skipped = 0

        for file_entry in file_list:
            file_path = file_entry["file_path"]

            print(f"\n{'=' * 60}")
            print(f"PIPELINE — {file_path}")
            print(f"{'=' * 60}")

            # Resolve source
            try:
                source_code = self.resolve_source(file_entry)
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "pipeline_status": "SKIPPED",
                    "error": f"Could not read source: {e}",
                    "stage0": None, "stage1": None, "stage2": None
                })
                skipped += 1
                continue

            # Infer language from extension
            try:
                _, ext = os.path.splitext(file_path)
                language = infer_language(ext)
            except ValueError:
                results.append({
                    "file_path": file_path,
                    "pipeline_status": "SKIPPED",
                    "error": f"Unsupported file extension: {file_path}",
                    "stage0": None, "stage1": None, "stage2": None
                })
                skipped += 1
                continue

            file_result = self.run_single_file(file_path, source_code, language)
            results.append(file_result)

            status = file_result["pipeline_status"]
            if status == "STOPPED_AT_STAGE_0":
                failed_stage0 += 1
            elif status == "STAGE_2_COMPLETE":
                completed += 1
                passed += 1
            elif status == "SKIPPED":
                skipped += 1

        return {
            "pipeline_status": "BATCH_COMPLETE",
            "total_files": len(file_list),
            "passed": passed,
            "failed_stage0": failed_stage0,
            "completed": completed,
            "skipped": skipped,
            "results": results
        }

    def run_single_file(self, file_path: str, source_code: str, language: str):
        """
        Run full pipeline for a single file.
        """
        # Stage 0
        stage0_result = compile_test(source_code, language)

        if stage0_result["status"] != "PASS":
            return {
                "file_path": file_path,
                "language": language,
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None, "stage2": None
            }

        # Stage 1
        try:
            stage1_result = run_stage1(
                stage0_result, source_code,
                user_context=self.user_context
            )
        except Exception as e:
            return {
                "file_path": file_path,
                "language": language,
                "pipeline_status": "FAILED_AT_STAGE_1",
                "stage0": stage0_result,
                "stage1": None, "stage2": None,
                "error": str(e)
            }

        # Stage 2
        try:
            stage2_result = run_stage2(
                stage1_result,
                max_mutants=self.mode_config.get("max_mutants")
            )
        except Exception as e:
            return {
                "file_path": file_path,
                "language": language,
                "pipeline_status": "FAILED_AT_STAGE_2",
                "stage0": stage0_result,
                "stage1": stage1_result,
                "stage2": None,
                "error": str(e)
            }

        return {
            "file_path": file_path,
            "language": language,
            "pipeline_status": "STAGE_2_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result,
            "stage2": stage2_result
        }


if __name__ == "__main__":

    pipeline = Pipeline_Orchestrator(mode=None)

    batch_input = [
        {"file_path": r"C:\Users\hp\Desktop\Leet Code\Optimised and Learnings\23 - Merge k sorted Lists.py"},
        {"file_path": r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\Test.cpp"},
        {"file_path": r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\Test.c"},
        {"file_path": r"C:\Users\hp\Desktop\IIIT Guwahati\CS\CS331(SE LAB)\Test.js"}
    ]

    result = pipeline.run_pipeline_batch(batch_input)

    print("\n" + "=" * 60)
    print("BATCH PIPELINE RESULT")
    print("=" * 60)
    print(f"\nBatch Status : {result['pipeline_status']}")
    print(f"Total Files  : {result['total_files']}")
    print(f"Completed    : {result['completed']}")
    print(f"Failed Stg0  : {result['failed_stage0']}")
    print(f"Skipped      : {result['skipped']}")

    for file_result in result["results"]:
        print(f"\n{'-' * 40}")
        print(f"File    : {file_result.get('file_path')}")
        print(f"Language: {file_result.get('language')}")
        print(f"Status  : {file_result.get('pipeline_status')}")

        if file_result.get("error"):
            print(f"Error   : {file_result['error']}")

        if file_result.get("stage1"):
            s1 = file_result["stage1"]
            print(f"Coverage — Line: {s1['coverage']['line']:.2%}, Branch: {s1['coverage']['branch']:.2%}")
            print(f"Bugs — Exceptions: {len(s1['bugs']['exceptions'])}, "
                  f"Failures: {len(s1['bugs']['failures'])}, "
                  f"Incorrect: {len(s1['bugs']['incorrect_outputs'])}")

        if file_result.get("stage2") and file_result["stage2"].get("mutation_testing"):
            mt = file_result["stage2"]["mutation_testing"]
            print(f"Mutation Score: {mt.get('mutation_score', 0):.2%}")