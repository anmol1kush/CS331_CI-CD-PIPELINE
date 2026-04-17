from pathlib import Path
from flask import Flask, Response, render_template_string, send_file
import os

app = Flask(__name__)

TARGET_FILE = Path(__file__).resolve().parent / "TARGET_CODE" / "target.py"

BASE_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Target Code Viewer</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; background: #f7f8fb; color: #202020; }
      pre { background: #272822; color: #f8f8f2; padding: 1rem; border-radius: 8px; overflow-x: auto; }
      a.button { display: inline-block; margin: 1rem 0; padding: 0.75rem 1.25rem; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
      a.button:hover { background: #0056b3; }
    </style>
  </head>
  <body>
    <h1>TARGET_CODE/target.py</h1>
    <p>
      <a class="button" href="/download">Download target.py</a>
    </p>
    <pre>{{ code }}</pre>
  </body>
</html>
"""

@app.route("/")
def index():
    try:
        code = TARGET_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Response("TARGET_CODE/target.py not found", status=404)

    return render_template_string(BASE_TEMPLATE, code=code)


@app.route("/download")
def download_target():
    if not TARGET_FILE.exists():
        return Response("TARGET_CODE/target.py not found", status=404)

    return send_file(
        TARGET_FILE,
        as_attachment=True,
        download_name="target.py",
        mimetype="text/x-python",
    )


# 🔥 Health check route (important for Render)
@app.route("/health")
def health():
    return {"status": "ok"}


# ⚠️ Only used for local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)