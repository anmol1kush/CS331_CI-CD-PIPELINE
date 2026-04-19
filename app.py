from pathlib import Path
from flask import Flask, Response, render_template, send_from_directory
import os

app = Flask(__name__)

TARGET_FOLDER = Path(__file__).resolve().parent / "TARGET_CODE"


@app.route("/")
def index():
    if not TARGET_FOLDER.exists():
        return Response("TARGET_CODE folder not found", status=404)

    files = []

    for file in TARGET_FOLDER.iterdir():
        if file.is_file():
            files.append({
                "name": file.name,
                "size": round(file.stat().st_size / 1024, 2)
            })

    return render_template("index.html", files=files)


@app.route("/download/<filename>")
def download_file(filename):
    file_path = TARGET_FOLDER / filename

    if not file_path.exists() or not file_path.is_file():
        return Response("File not found", status=404)

    return send_from_directory(
        TARGET_FOLDER,
        filename,
        as_attachment=True
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)