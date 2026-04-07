"""
Tests Executor

Runs generated tests against the program under test and
returns structured execution results with line-level trace data.

Supported execution models (current iteration):
- callable_method
- stdin_program
- script

NOTE:
Execution occurs locally inside the container environment.
The LLM is NOT used for execution.
Tracing is integrated into each worker to collect executed_lines
for coverage analysis downstream.
"""
import time
import multiprocessing
import sys
import io
import os
import tempfile
from Stage1.config import TEST_TIMEOUT, QUEUE_DRAIN_TIMEOUT


def run_tests(source_code, tests, execution_model):
    results = []
    all_executed_lines = set()

    if execution_model == "callable_method":
        results, all_executed_lines = execute_callable(source_code, tests)

    elif execution_model == "stdin_program":
        results, all_executed_lines = execute_stdin(source_code, tests)

    elif execution_model == "script":
        results, all_executed_lines = execute_script(source_code)

    else:
        raise ValueError(f"Unsupported execution model: {execution_model}")

    return results, all_executed_lines


def run_with_timeout(target, args):
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=target, args=(*args, queue))

    start = time.time()
    process.start()
    process.join(TEST_TIMEOUT)

    runtime = time.time() - start

    if process.is_alive():
        process.terminate()
        process.join()

        return {
            "status": "timeout",
            "output": None,
            "error": f"Execution exceeded {TEST_TIMEOUT} seconds",
            "runtime": runtime,
            "executed_lines": set()
        }

    try:
        result = queue.get(timeout=QUEUE_DRAIN_TIMEOUT)
    except Exception:
        result = {
            "status": "crash",
            "output": None,
            "error": "Child process died without producing a result",
            "executed_lines": set()
        }

    result["runtime"] = runtime
    return result


def extract_traced_lines(tracer):
    executed_lines = set()
    results = tracer.results()
    for (filename, lineno), _ in results.counts.items():
        executed_lines.add(lineno)
    return executed_lines


def callable_worker(source_code, test, queue):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        code = compile(open(tmp_path).read(), tmp_path, 'exec')

        executed_lines = set()

        def line_tracer(frame, event, arg):
            if event == 'line' and frame.f_code.co_filename == tmp_path:
                executed_lines.add(frame.f_lineno)
            return line_tracer

        def global_tracer(frame, event, arg):
            if frame.f_code.co_filename == tmp_path:
                return line_tracer
            return None

        namespace = {}
        sys.settrace(global_tracer)
        exec(code, namespace)
        sys.settrace(None)

        if "Solution" not in namespace:
            raise RuntimeError("Solution class not found")

        solution = namespace["Solution"]()

        method_name = test.get("method_name")
        if not method_name:
            raise RuntimeError("Tests missing method_name field")

        method = getattr(solution, method_name, None)
        if not method:
            raise RuntimeError(f"Method '{method_name}' not found in Solution class")

        inputs = test.get("input", [])
        sys.settrace(global_tracer)
        output = method(*inputs)
        sys.settrace(None)

        queue.put({
            "status": "success",
            "output": output,
            "error": None,
            "executed_lines": list(executed_lines)
        })

    except Exception as e:
        queue.put({
            "status": "exception",
            "output": None,
            "error": str(e),
            "executed_lines": []
        })

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def execute_callable(source_code, tests):
    results = []
    all_executed_lines = set()

    for ind, test in enumerate(tests):
        result = run_with_timeout(
            callable_worker,
            (source_code, test)
        )

        all_executed_lines.update(result.pop("executed_lines", []))
        result["test_id"] = ind
        results.append(result)

    return results, all_executed_lines


def stdin_worker(source_code, fake_input, queue):
    tmp_path = None
    sys.stdin = io.StringIO(fake_input)
    sys.stdout = io.StringIO()

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        code = compile(open(tmp_path).read(), tmp_path, 'exec')

        executed_lines = set()

        def line_tracer(frame, event, arg):
            if event == 'line' and frame.f_code.co_filename == tmp_path:
                executed_lines.add(frame.f_lineno)
            return line_tracer

        def global_tracer(frame, event, arg):
            if frame.f_code.co_filename == tmp_path:
                return line_tracer
            return None

        sys.settrace(global_tracer)
        exec(code, {})
        sys.settrace(None)

        output = sys.stdout.getvalue()

        queue.put({
            "status": "success",
            "output": output,
            "error": None,
            "executed_lines": list(executed_lines)
        })

    except Exception as e:
        queue.put({
            "status": "exception",
            "output": None,
            "error": str(e),
            "executed_lines": []
        })

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def execute_stdin(source_code, tests):
    results = []
    all_executed_lines = set()

    for ind, test in enumerate(tests):
        fake_input = test.get("input", "")

        result = run_with_timeout(
            stdin_worker,
            (source_code, fake_input)
        )

        all_executed_lines.update(result.pop("executed_lines", []))
        result["test_id"] = ind
        results.append(result)

    return results, all_executed_lines


def script_worker(source_code, queue):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        code = compile(open(tmp_path).read(), tmp_path, 'exec')

        executed_lines = set()

        def line_tracer(frame, event, arg):
            if event == 'line' and frame.f_code.co_filename == tmp_path:
                executed_lines.add(frame.f_lineno)
            return line_tracer

        def global_tracer(frame, event, arg):
            if frame.f_code.co_filename == tmp_path:
                return line_tracer
            return None

        sys.settrace(global_tracer)
        exec(code, {})
        sys.settrace(None)

        queue.put({
            "status": "success",
            "output": None,
            "error": None,
            "executed_lines": list(executed_lines)
        })

    except Exception as e:
        queue.put({
            "status": "exception",
            "output": None,
            "error": str(e),
            "executed_lines": []
        })

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def execute_script(source_code):
    result = run_with_timeout(
        script_worker,
        (source_code,)
    )

    all_executed_lines = result.pop("executed_lines", [])
    result["test_id"] = 0

    return [result], all_executed_lines


# def find_method(solution_obj):
#     methods = [
#         getattr(solution_obj, attr)
#         for attr in dir(solution_obj)
#         if callable(getattr(solution_obj, attr)) and not attr.startswith("_")
#     ]
#
#     if not methods:
#         raise RuntimeError("No callable method found in Solution class")
#
#     return methods[0]