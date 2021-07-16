import datetime
import os
import tempfile

from pathlib import Path

from flask import Flask, abort, redirect, request
from jinja2 import Environment, PackageLoader
from werkzeug.utils import secure_filename

from latexbuddy import __name__ as name
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleLoader


app = Flask(name)
env = Environment(loader=PackageLoader("latexbuddy"))

ALLOWED_EXTENSIONS = [
    "txt",
    "tex",
    "bib",
    "bbl",
    "blg",
    "sty",
    "bst",
    "cls",
    "aux",
    "pdf",
    "jpg",
    "jpeg",
    "gif",
    "svg",
]


class FlaskConfigLoader(ConfigLoader):
    def __init__(self, output_dir: Path):
        super().__init__()

        self.main_flags = {
            "output": str(output_dir),
            "format": "HTML_FLASK",
            "enable-modules-by-default": True,
        }
        self.module_flags = {}


def run_server():
    upload_folder = tempfile.TemporaryDirectory()
    app.config["UPLOAD_FOLDER"] = upload_folder.name

    results_folder = tempfile.TemporaryDirectory()
    app.config["RESULTS_FOLDER"] = results_folder.name

    app.run()

    # deleting temporary directories and their contents upon context exit


@app.route("/")
def index():
    return env.get_template("flask_index.html").render()


@app.route("/check", methods=["GET", "POST"])
def document_check():

    if request.method != "POST":
        return redirect("/")

    if "file" not in request.files:
        # flash("No files attached")
        return redirect(request.url)

    file = request.files["file"]

    if file.filename == "":
        # flash("No files attached")
        return redirect(request.url)

    if file and allowed_file(file.filename):

        filename = secure_filename(file.filename)
        target_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(target_path)

        date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_id = f"{date}_{filename.replace('.', '_')}"
        result_path = os.path.join(app.config["RESULTS_FOLDER"], result_id)

        # TODO: multiprocessing?
        run_buddy(Path(target_path), Path(result_path))

        return redirect(f"/result/{result_id}")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_buddy(file_path: Path, output_dir: Path):

    if not output_dir.exists():
        output_dir.mkdir()

    LatexBuddy.init(
        FlaskConfigLoader(output_dir),
        ModuleLoader(Path("latexbuddy/modules/")),
        file_path,
        [file_path],
    )

    LatexBuddy.run_tools()
    LatexBuddy.output_file()


@app.route("/result/<result_id>")
def check_result(result_id):

    result_path = Path(
        os.path.join(app.config["RESULTS_FOLDER"], secure_filename(result_id))
    )

    if not result_path.exists():
        abort(404)

    files = list(result_path.rglob("*.html"))

    if len(files) < 1:
        abort(404)

    return redirect(f"/result/{result_id}/{secure_filename(files[0].name)}")


@app.route("/result/<result_id>/<file_name>")
def display_result(result_id, file_name):

    result_path = Path(
        os.path.join(app.config["RESULTS_FOLDER"], secure_filename(result_id))
    )

    if not result_path.exists():
        abort(404)

    file_path = Path(os.path.join(str(result_path), secure_filename(file_name)))

    with open(file_path, "r") as f:
        file_contents = f.read()

    return file_contents


@app.route("/whitelist-api")
def modify_whitelist():
    return "<p>Nope, not yet.</p>"
