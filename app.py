import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Intelligence-Module'))

from Stage0.stage0_compile import file_reader

SUPPORTED_EXT = ['.py', '.c', '.cpp', '.java']

def process_submission(file_path):
    try:
        return file_reader(file_path)
    except Exception as e:
        return {
            "stage": 0,
            "status": "ERROR",
            "language": "unknown",
            "executed": False,
            "error": str(e)
        }