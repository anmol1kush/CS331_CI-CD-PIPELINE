import os
import subprocess
import tempfile

def infer_language(ext):
    return {
        ".py": "python",
        ".c": "c",
        ".cpp": "cpp",
        ".java": "java"
    }.get(ext)

def compile_test(code, language):
    try:
        if language == "python":
            compile(code, "<submitted_code>", "exec")
            return pass_result(language)

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext_map(language)) as f:
            f.write(code.encode())
            path = f.name

        run_compiler(path, language)
        os.remove(path)
        return pass_result(language)

    except subprocess.CalledProcessError as e:
        return fail_result(language, e.stderr)
    except Exception as e:
        return fail_result(language, str(e))

def run_compiler(path, language):
    cmds = {
        "c": ["gcc", "-fsyntax-only", path],
        "cpp": ["g++", "-fsyntax-only", path],
        "java": ["javac", path]
    }
    subprocess.run(
        cmds[language],
        check=True,
        capture_output=True,
        text=True
    )

def ext_map(language):
    return {
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java"
    }[language]

def pass_result(lang):
    return {
        "stage": 0,
        "status": "PASS",
        "language": lang,
        "executed": False,
        "error": None
    }

def fail_result(lang, err):
    return {
        "stage": 0,
        "status": "FAIL",
        "language": lang,
        "executed": False,
        "error": err
    }

def file_reader(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    _, ext = os.path.splitext(file_path)
    lang = infer_language(ext)
    if not lang:
        raise ValueError("unsupported language")

    return compile_test(code, lang)
