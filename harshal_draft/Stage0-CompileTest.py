import os
import subprocess
import tempfile


# Stage 0: Compilation / Syntax Check
def file_reader(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        _, ext = os.path.splitext(file_path)
        language = infer_language(ext)

        return compile_test(code, language)

    except Exception as e:
        return {
            "stage": 0,
            "status": "FAIL",
            "check_type": "compile_only",
            "language": None,
            "executed": False,
            "error_type": type(e).__name__,
            "error": str(e)
        }


def infer_language(ext: str):
    if ext == ".py":
        return "python"
    if ext == ".c":
        return "c"
    if ext == ".cpp":
        return "cpp"
    if ext == ".java":
        return "java"
    raise ValueError("Unsupported language")


def compile_test(code: str, language: str):
    try:
        if language == "python":
            compile(code, "<submitted_code>", "exec")

        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=language_extension(language)) as tmp:
                tmp.write(code.encode("utf-8"))
                tmp_path = tmp.name

            run_compiler(tmp_path, language)

        return {
            "stage": 0,
            "status": "PASS",
            "check_type": "compile_only",
            "language": language,
            "executed": False,
            "error": None
        }

    except Exception as e:
        return {
            "stage": 0,
            "status": "FAIL",
            "check_type": "compile_only",
            "language": language,
            "executed": False,
            "error_type": type(e).__name__,
            "error": str(e)
        }


def run_compiler(file_path: str, language: str):
    if language == "c":
        subprocess.run(["gcc", "-fsyntax-only", file_path], check=True)
    elif language == "cpp":
        subprocess.run(["g++", "-fsyntax-only", file_path], check=True)
    elif language == "java":
        subprocess.run(["javac", file_path], check=True)


def language_extension(language: str):
    return {
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java"
    }[language]


# Example run
result_py = file_reader("Sample code 1.py")
print(result_py)

result_c = file_reader("Sample code 1.c")
print(result_c)

result_cpp = file_reader("Sample code 1.cpp")
print(result_cpp)
