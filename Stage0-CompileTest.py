#Stage 0: Compilation Errors Test
def compile_test(code: str):
    try:
        compiled = compile(code, "<submitted_code>", "exec")
        exec(compiled, {})
        return {
            "status": "PASS",
            "error": None
        }
    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e)
        }

print(compile_test('''
def test():
    print(10 + "a")
'''))
