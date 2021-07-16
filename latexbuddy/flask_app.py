import os
import tempfile

from flask import Flask, request, flash, redirect
from jinja2 import Environment, PackageLoader
from werkzeug.utils import secure_filename

from latexbuddy import __name__ as name


app = Flask(name)
env = Environment(loader=PackageLoader("latexbuddy"))

ALLOWED_EXTENSIONS = [
    "txt", "tex", "bib", "bbl", "blg", "sty", "bst", "cls", "aux", "pdf", "jpg",
    "jpeg", "gif", "svg"
]


def run_server():
    upload_folder = tempfile.TemporaryDirectory()
    app.config["UPLOAD_FOLDER"] = upload_folder.name

    app.run()

    # deletes the temporary directory upon context exit


@app.route("/")
def index():
    return env.get_template("flask_index.html").render()


@app.route("/check", methods=["GET", "POST"])
def document_check():

    if request.method == "POST":

        if "file" not in request.files:
            # flash("No files attached")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            # flash("No files attached")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            # TODO: generate an id and start buddy checks
            result_id = "TBD"

            return redirect(f"/result/{result_id}")

    return redirect(request.url)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/result/<result_id>")
def check_result(result_id):
    return f"<p>This page (id {result_id}) is not yet available...</p>"


@app.route("/whitelist-api")
def modify_whitelist():
    return "<p>Nope, not yet.</p>"
