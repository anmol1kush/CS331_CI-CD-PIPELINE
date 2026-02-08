import os
from stage0_compile import file_reader

SUPPORTED_EXT = {".py", ".c", ".cpp", ".java"}

def process_submission(file_path):
    if not os.path.exists(file_path):
        return {"error": "file not found"}

    _, ext = os.path.splitext(file_path)
    if ext not in SUPPORTED_EXT:
        return {"error": "unsupported file type"}

    return file_reader(file_path)

if __name__ == "__main__":
    samples = [
        "samples/SampleCode.py",
        "samples/SampleCode.c",
        "samples/SampleCode.cpp",
        "samples/SampleCode.java"
    ]

    for s in samples:
        print(s, process_submission(s))
