"""
Python Executor — runs Python code via exec() with sys.settrace coverage.

Extracted from the original test_executor.py.
All logic is preserved exactly as-is.
"""

import time
import multiprocessing
import sys
import io
import os
import tempfile
from Stage1.config import TEST_TIMEOUT, QUEUE_DRAIN_TIMEOUT
from Stage1.Executors.executor_base import ExecutorBase


class PythonExecutor(ExecutorBase):

    def execute_callable(self, source_code, tests, structural_features=None):
        results = []
        all_executed_lines = set()

        for ind, test in enumerate(tests):
            result = self.run_with_timeout(
                self.callable_worker,
                (source_code, test)
            )

            per_test_lines = result.pop("executed_lines", [])
            all_executed_lines.update(per_test_lines)
            result["per_test_executed_lines"] = set(per_test_lines)
            result["test_id"] = ind
            results.append(result)

        return results, all_executed_lines

    def execute_stdin(self, source_code, tests):
        results = []
        all_executed_lines = set()

        for ind, test in enumerate(tests):
            fake_input = test.get("input", "")

            result = self.run_with_timeout(
                self.stdin_worker,
                (source_code, fake_input)
            )

            per_test_lines = result.pop("executed_lines", [])
            all_executed_lines.update(per_test_lines)
            result["per_test_executed_lines"] = set(per_test_lines)
            result["test_id"] = ind
            results.append(result)

        return results, all_executed_lines

    def execute_script(self, source_code):
        result = self.run_with_timeout(
            self.script_worker,
            (source_code,)
        )

        per_test_lines = result.pop("executed_lines", [])
        result["per_test_executed_lines"] = set(per_test_lines)
        result["test_id"] = 0

        return [result], set(per_test_lines)

    # ── Subprocess Timeout Wrapper ──

    def run_with_timeout(self, target, args):
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
                "executed_lines": set(),
                "called_operations": []
            }

        try:
            result = queue.get(timeout=QUEUE_DRAIN_TIMEOUT)
        except Exception:
            result = {
                "status": "crash",
                "output": None,
                "error": "Child process died without producing a result",
                "executed_lines": set(),
                "called_operations": []
            }

        result["runtime"] = runtime
        return result

    # ── Workers (static methods for multiprocessing) ──

    @staticmethod
    def callable_worker(source_code, test, queue):
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(source_code)
                tmp_path = tmp.name

            code = compile(open(tmp_path).read(), tmp_path, 'exec')

            namespace = {}
            executed_lines = set()
            called_operations = []

            def local_tracer(frame, event, arg):
                if frame.f_code.co_filename == tmp_path:
                    if event == 'line':
                        executed_lines.add(frame.f_lineno)
                    elif event == 'call':
                        called_operations.append(("func", frame.f_code.co_name))
                return local_tracer

            def global_tracer(frame, event, arg):
                if frame.f_code.co_filename == tmp_path:
                    if event == 'call':
                        called_operations.append(("func", frame.f_code.co_name))
                    return local_tracer
                if event == 'call' and frame.f_back and frame.f_back.f_code.co_filename == tmp_path:
                    called_operations.append(("external", frame.f_code.co_name))
                return None

            sys.settrace(global_tracer)
            exec(code, namespace)
            sys.settrace(None)

            # Find Solution class and call method
            solution_class = namespace.get("Solution")
            if not solution_class:
                raise RuntimeError("No Solution class found")

            instance = solution_class()
            method_name = test.get("method_name")
            method = getattr(instance, method_name, None)

            if not method:
                raise RuntimeError(f"Method '{method_name}' not found in Solution")

            test_input = test.get("input", [])

            sys.settrace(global_tracer)
            output = method(*test_input)
            sys.settrace(None)

            queue.put({
                "status": "success",
                "output": output,
                "error": None,
                "executed_lines": list(executed_lines),
                "called_operations": list(called_operations)
            })

        except Exception as e:
            queue.put({
                "status": "exception",
                "output": None,
                "error": str(e),
                "executed_lines": list(executed_lines) if 'executed_lines' in dir() else [],
                "called_operations": list(called_operations) if 'called_operations' in dir() else []
            })

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
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
            called_operations = []

            def local_tracer(frame, event, arg):
                if frame.f_code.co_filename == tmp_path:
                    if event == 'line':
                        executed_lines.add(frame.f_lineno)
                    elif event == 'call':
                        called_operations.append(("func", frame.f_code.co_name))
                return local_tracer

            def global_tracer(frame, event, arg):
                if frame.f_code.co_filename == tmp_path:
                    if event == 'call':
                        called_operations.append(("func", frame.f_code.co_name))
                    return local_tracer
                if event == 'call' and frame.f_back and frame.f_back.f_code.co_filename == tmp_path:
                    called_operations.append(("external", frame.f_code.co_name))
                return None

            sys.settrace(global_tracer)
            exec(code, {})
            sys.settrace(None)

            output = sys.stdout.getvalue()

            queue.put({
                "status": "success",
                "output": output,
                "error": None,
                "executed_lines": list(executed_lines),
                "called_operations": list(called_operations)
            })

        except Exception as e:
            queue.put({
                "status": "exception",
                "output": None,
                "error": str(e),
                "executed_lines": list(executed_lines) if 'executed_lines' in dir() else [],
                "called_operations": list(called_operations) if 'called_operations' in dir() else []
            })

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def script_worker(source_code, queue):
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(source_code)
                tmp_path = tmp.name

            code = compile(open(tmp_path).read(), tmp_path, 'exec')

            executed_lines = set()
            called_operations = []

            def local_tracer(frame, event, arg):
                if frame.f_code.co_filename == tmp_path:
                    if event == 'line':
                        executed_lines.add(frame.f_lineno)
                    elif event == 'call':
                        called_operations.append(("func", frame.f_code.co_name))
                return local_tracer

            def global_tracer(frame, event, arg):
                if frame.f_code.co_filename == tmp_path:
                    if event == 'call':
                        called_operations.append(("func", frame.f_code.co_name))
                    return local_tracer
                if event == 'call' and frame.f_back and frame.f_back.f_code.co_filename == tmp_path:
                    called_operations.append(("external", frame.f_code.co_name))
                return None

            sys.settrace(global_tracer)
            exec(code, {})
            sys.settrace(None)

            queue.put({
                "status": "success",
                "output": None,
                "error": None,
                "executed_lines": list(executed_lines),
                "called_operations": list(called_operations)
            })

        except Exception as e:
            queue.put({
                "status": "exception",
                "output": None,
                "error": str(e),
                "executed_lines": list(executed_lines) if 'executed_lines' in dir() else [],
                "called_operations": list(called_operations) if 'called_operations' in dir() else []
            })

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)