"""
Pipeline Orchestrator
Coordinates Stage0 -> Stage1 -> Stage2.

CLI usage:
    python Orchestrator.py <file-or-directory> [more paths...]

The orchestrator accepts one or more files or directories, recursively discovers
supported source files, runs the batch pipeline, and stores results under
Intelligence-Module/root/<run-name>/.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from Stage0.Stage0_Compile import compile_test, infer_language
from Stage1.Pipeline.Stage1_pipeline import run_stage1
from Stage2.Pipeline.validation_pipeline import run_stage2
from Stage1.config import apply_mode_overrides
from cost_modes import get_mode


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_ROOT = BASE_DIR / "root"
SUPPORTED_EXTENSIONS = {".py", ".c", ".cpp", ".java", ".js", ".jsx", ".ts", ".tsx"}
SKIP_DIRECTORIES = {
    ".git",
    ".github",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "venv",
    ".venv",
    "root",
}


def sanitize_name(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value)
    safe = safe.strip("-._")
    return safe or "item"


def make_json_safe(value):
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]
    if isinstance(value, set):
        return [make_json_safe(item) for item in sorted(value, key=lambda item: repr(item))]
    if isinstance(value, Path):
        return str(value)
    return value


def write_json_atomic(target_path: Path, payload) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    safe_payload = make_json_safe(payload)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=target_path.parent,
        delete=False,
    ) as handle:
        json.dump(safe_payload, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
        temp_path = Path(handle.name)

    temp_path.replace(target_path)


def collect_supported_files(targets: list[str]) -> list[Path]:
    discovered: list[Path] = []

    for target in targets:
        target_path = Path(target).expanduser().resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Target not found: {target_path}")

        if target_path.is_file():
            if target_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                discovered.append(target_path)
            continue

        for candidate in sorted(target_path.rglob("*")):
            if candidate.is_dir():
                if candidate.name in SKIP_DIRECTORIES:
                    continue
                continue

            if any(part in SKIP_DIRECTORIES for part in candidate.parts):
                continue

            if candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
                discovered.append(candidate.resolve())

    unique_files: list[Path] = []
    seen: set[str] = set()
    for file_path in discovered:
        key = str(file_path)
        if key not in seen:
            unique_files.append(file_path)
            seen.add(key)

    return unique_files


def ensure_output_dir(output_dir: str | None) -> Path:
    if output_dir:
        candidate = Path(output_dir)
        resolved = candidate if candidate.is_absolute() else BASE_DIR / candidate
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        resolved = DEFAULT_RESULTS_ROOT / f"run-{timestamp}"

    resolved.mkdir(parents=True, exist_ok=True)
    return resolved.resolve()


def make_file_label(file_path: str, source_root: Path | None) -> str:
    file_obj = Path(file_path).resolve()
    if source_root:
        try:
            return str(file_obj.relative_to(source_root.resolve()))
        except ValueError:
            pass
    return str(file_obj)


class Pipeline_Orchestrator:
    def __init__(self, user_context: str | None = None, mode: str | None = None):
        self.user_context = user_context
        self.mode_config = get_mode(mode)

    @staticmethod
    def resolve_source(file_entry: dict) -> str:
        if "source_code" in file_entry:
            return file_entry["source_code"]
        with open(file_entry["file_path"], "r", encoding="utf-8") as file:
            return file.read()

    def run_pipeline_batch(
        self,
        file_list: list[dict],
        output_dir: str | Path | None = None,
        source_root: str | Path | None = None,
    ) -> dict:
        apply_mode_overrides(self.mode_config)

        output_path = ensure_output_dir(str(output_dir) if output_dir else None)
        root_path = Path(source_root).resolve() if source_root else None

        results = []
        passed = 0
        failed_stage0 = 0
        completed = 0
        skipped = 0

        for file_entry in file_list:
            raw_file_path = file_entry["file_path"]
            display_path = make_file_label(raw_file_path, root_path)

            print(f"\n{'=' * 60}")
            print(f"PIPELINE - {display_path}")
            print(f"{'=' * 60}")

            try:
                source_code = self.resolve_source(file_entry)
            except Exception as exc:
                results.append(
                    {
                        "file_path": display_path,
                        "source_path": raw_file_path,
                        "pipeline_status": "SKIPPED",
                        "error": f"Could not read source: {exc}",
                        "stage0": None,
                        "stage1": None,
                        "stage2": None,
                    }
                )
                skipped += 1
                continue

            try:
                _, ext = os.path.splitext(raw_file_path)
                language = infer_language(ext.lower())
            except ValueError:
                results.append(
                    {
                        "file_path": display_path,
                        "source_path": raw_file_path,
                        "pipeline_status": "SKIPPED",
                        "error": f"Unsupported file extension: {raw_file_path}",
                        "stage0": None,
                        "stage1": None,
                        "stage2": None,
                    }
                )
                skipped += 1
                continue

            file_result = self.run_single_file(display_path, raw_file_path, source_code, language)
            results.append(file_result)

            status = file_result["pipeline_status"]
            if status == "STOPPED_AT_STAGE_0":
                failed_stage0 += 1
            elif status == "STAGE_2_COMPLETE":
                completed += 1
                passed += 1
            elif status == "SKIPPED":
                skipped += 1

        summary = {
            "pipeline_status": "BATCH_COMPLETE",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "output_dir": str(output_path),
            "source_root": str(root_path) if root_path else None,
            "total_files": len(file_list),
            "passed": passed,
            "failed_stage0": failed_stage0,
            "completed": completed,
            "skipped": skipped,
            "results": results,
        }

        self.write_results(summary, output_path)
        return summary

    def run_single_file(
        self, display_path: str, raw_file_path: str, source_code: str, language: str
    ) -> dict:
        stage0_result = compile_test(source_code, language)

        if stage0_result["status"] != "PASS":
            return {
                "file_path": display_path,
                "source_path": raw_file_path,
                "language": language,
                "pipeline_status": "STOPPED_AT_STAGE_0",
                "stage0": stage0_result,
                "stage1": None,
                "stage2": None,
            }

        try:
            stage1_result = run_stage1(
                stage0_result,
                source_code,
                user_context=self.user_context,
            )
        except Exception as exc:
            return {
                "file_path": display_path,
                "source_path": raw_file_path,
                "language": language,
                "pipeline_status": "FAILED_AT_STAGE_1",
                "stage0": stage0_result,
                "stage1": None,
                "stage2": None,
                "error": str(exc),
            }

        try:
            stage2_result = run_stage2(
                stage1_result,
                max_mutants=self.mode_config.get("max_mutants"),
            )
        except Exception as exc:
            return {
                "file_path": display_path,
                "source_path": raw_file_path,
                "language": language,
                "pipeline_status": "FAILED_AT_STAGE_2",
                "stage0": stage0_result,
                "stage1": stage1_result,
                "stage2": None,
                "error": str(exc),
            }

        return {
            "file_path": display_path,
            "source_path": raw_file_path,
            "language": language,
            "pipeline_status": "STAGE_2_COMPLETE",
            "stage0": stage0_result,
            "stage1": stage1_result,
            "stage2": stage2_result,
        }

    @staticmethod
    def write_results(summary: dict, output_path: Path) -> None:
        files_dir = output_path / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        write_json_atomic(output_path / "pipeline_results_summary.json", summary)

        for index, file_result in enumerate(summary["results"], start=1):
            label = sanitize_name(file_result.get("file_path", f"file-{index}"))
            detail_path = files_dir / f"{index:03d}-{label}.json"
            write_json_atomic(detail_path, file_result)


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the intelligence pipeline against one or more files/directories."
    )
    parser.add_argument("targets", nargs="+", help="Source file(s) or directory/directories to test")
    parser.add_argument("--mode", default=None, help="Pipeline cost mode")
    parser.add_argument("--user-context", default=None, help="Optional user context for Stage 1")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for generated results. Relative paths are created inside Intelligence-Module.",
    )
    parser.add_argument(
        "--source-root",
        default=None,
        help="Optional base directory used to make file paths in reports relative.",
    )
    return parser


def main() -> int:
    parser = build_cli_parser()
    args = parser.parse_args()

    file_paths = collect_supported_files(args.targets)
    if not file_paths:
        print("No supported source files were found in the provided targets.")
        return 1

    if args.source_root:
        source_root = Path(args.source_root).expanduser().resolve()
    elif len(args.targets) == 1 and Path(args.targets[0]).expanduser().resolve().is_dir():
        source_root = Path(args.targets[0]).expanduser().resolve()
    else:
        source_root = None

    pipeline = Pipeline_Orchestrator(user_context=args.user_context, mode=args.mode)
    batch_input = [{"file_path": str(path)} for path in file_paths]
    result = pipeline.run_pipeline_batch(
        batch_input,
        output_dir=args.output_dir,
        source_root=source_root,
    )

    print("\n" + "=" * 60)
    print("BATCH PIPELINE RESULT")
    print("=" * 60)
    print(f"\nBatch Status : {result['pipeline_status']}")
    print(f"Total Files  : {result['total_files']}")
    print(f"Completed    : {result['completed']}")
    print(f"Failed Stg0  : {result['failed_stage0']}")
    print(f"Skipped      : {result['skipped']}")
    print(f"Results Dir  : {result['output_dir']}")

    for file_result in result["results"]:
        print(f"\n{'-' * 40}")
        print(f"File    : {file_result.get('file_path')}")
        print(f"Language: {file_result.get('language')}")
        print(f"Status  : {file_result.get('pipeline_status')}")

        if file_result.get("error"):
            print(f"Error   : {file_result['error']}")

        if file_result.get("stage1"):
            stage1 = file_result["stage1"]
            print(
                f"Coverage - Line: {stage1['coverage']['line']:.2%}, "
                f"Branch: {stage1['coverage']['branch']:.2%}"
            )
            print(
                f"Bugs - Exceptions: {len(stage1['bugs']['exceptions'])}, "
                f"Failures: {len(stage1['bugs']['failures'])}, "
                f"Incorrect: {len(stage1['bugs']['incorrect_outputs'])}"
            )

        if file_result.get("stage2") and file_result["stage2"].get("mutation_testing"):
            mutation_testing = file_result["stage2"]["mutation_testing"]
            print(f"Mutation Score: {mutation_testing.get('mutation_score', 0):.2%}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
