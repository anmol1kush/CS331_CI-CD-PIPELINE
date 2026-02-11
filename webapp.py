from flask import Flask, request, render_template, redirect, url_for, flash
import os
from app import process_submission, SUPPORTED_EXT

app = Flask(__name__)
app.secret_key = "dev-secret"

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    samples = []
    if os.path.isdir(SAMPLES_DIR):
        samples = [f for f in os.listdir(SAMPLES_DIR) if os.path.splitext(f)[1] in SUPPORTED_EXT]

    if request.method == "POST":
        # sample selected
        sample = request.form.get("sample")
        if sample:
            path = os.path.join(SAMPLES_DIR, sample)
            result = process_submission(path)
            return render_template("result.html", filename=sample, result=result)

        # file uploaded
        uploaded = request.files.get("file")
        if uploaded and uploaded.filename:
            filename = uploaded.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded.save(save_path)
            result = process_submission(save_path)
            return render_template("result.html", filename=filename, result=result)

        flash("No file uploaded or sample selected")
        return redirect(url_for("index"))

    return render_template("index.html", samples=samples)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
