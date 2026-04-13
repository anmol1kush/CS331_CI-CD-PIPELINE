import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TARGET_DIR = BASE_DIR / "TARGET_CODE"
SUPPORTED_EXTENSIONS = {".py", ".c", ".cpp", ".java"}

# Ensure Intelligence-Module is importable without changing existing app behavior.
sys.path.append(str(BASE_DIR / "Intelligence-Module"))

try:
    from Orchestrator import Pipeline_Orchestrator
except Exception as exc:
    print(f"Failed to import existing Intelligence-Module orchestrator: {exc}")
    sys.exit(1)


def find_target_files():
    if not TARGET_DIR.exists() or not TARGET_DIR.is_dir():
        return []
    return sorted(
        [path for path in TARGET_DIR.iterdir() if path.suffix.lower() in SUPPORTED_EXTENSIONS and path.is_file()],
        key=lambda p: p.name
    )


def format_stage_output(stage_name, stage_data):
    output = [f"\n{stage_name}", "-" * len(stage_name)]
    if stage_data is None:
        output.append("No data available for this stage.")
    else:
        output.append(json.dumps(stage_data, indent=2, default=str))
    return "\n".join(output)


def format_pipeline_output(result):
    lines = ["PIPELINE RESULT SUMMARY", "======================="]
    lines.append(f"Pipeline Status: {result.get('pipeline_status')}")
    lines.append(format_stage_output("Stage 0 — Compilation Check", result.get('stage0')))
    lines.append(format_stage_output("Stage 1 — Semantic Analysis & Test Generation", result.get('stage1')))
    lines.append(format_stage_output("Stage 2 — Validation", result.get('stage2')))
    return "\n\n".join(lines)


def run_file(target_file: Path):
    print(f"\n{'=' * 80}")
    print(f"Running pipeline for: {target_file}")
    print(f"{'=' * 80}\n")

    pipeline = Pipeline_Orchestrator(str(target_file))
    result = pipeline.run_pipeline()
    output_text = format_pipeline_output(result)

    print(output_text)

    result_path = TARGET_DIR / f"{target_file.stem}_pipeline_result.json"
    with result_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    text_path = TARGET_DIR / f"{target_file.stem}_pipeline_result.txt"
    with text_path.open("w", encoding="utf-8") as f:
        f.write(output_text)

    print(f"\nSaved JSON result to: {result_path}")
    print(f"Saved text result to: {text_path}\n")

    return result


def main():
    files = find_target_files()
    if not files:
        print("No TARGET_CODE files found. Place your source files in TARGET_CODE/ and rerun.")
        sys.exit(1)

    summary = {}
    for target_file in files:
        try:
            result = run_file(target_file)
            summary[target_file.name] = result
        except Exception as exc:
            print(f"Error running pipeline for {target_file.name}: {exc}")
            sys.exit(1)

    summary_path = TARGET_DIR / "pipeline_results_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Pipeline complete. Summary written to: {summary_path}")


if __name__ == "__main__":
    main()
