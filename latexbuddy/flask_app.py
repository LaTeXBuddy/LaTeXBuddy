import datetime
import os
import re
import tempfile

from pathlib import Path
from typing import List, Optional

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

    _REGEX_LANGUAGE_FLAG = re.compile(r"([a-zA-Z]{2,3})(?:[-_\s]([a-zA-Z]{2,3}))?")

    def __init__(
        self,
        output_dir: Path,
        language: Optional[str],
        module_selector_mode: Optional[str],
        module_selection: Optional[str],
        whitelist_id: Optional[str],
    ):
        super().__init__()

        self.main_flags = {
            "output": str(output_dir),
            "format": "HTML_FLASK",
            "enable-modules-by-default": True,
        }

        self.module_flags = {}

        if language:
            match = self._REGEX_LANGUAGE_FLAG.fullmatch(language)

            if match:
                self.main_flags["language"] = match.group(1)

                if match.group(2):
                    self.main_flags["language_country"] = match.group(2)

        if module_selector_mode and module_selector_mode in ["blacklist", "whitelist"]:
            self.main_flags["enable-modules-by-default"] = (
                True if module_selector_mode == "blacklist" else False
            )

            if module_selection:
                for module in module_selection.split(","):
                    self.module_flags[module] = {}
                    self.module_flags[module]["enabled"] = (
                        False if module_selector_mode == "blacklist" else True
                    )

        if (
            whitelist_id
            and whitelist_id != "[none]"
            and get_whitelist_path(whitelist_id)
        ):
            self.main_flags["whitelist"] = get_whitelist_path(whitelist_id)


def run_server():
    upload_folder = tempfile.TemporaryDirectory()
    app.config["UPLOAD_FOLDER"] = upload_folder.name

    results_folder = tempfile.TemporaryDirectory()
    app.config["RESULTS_FOLDER"] = results_folder.name

    whitelist_folder = tempfile.TemporaryDirectory()
    app.config["WHITELIST_FOLDER"] = whitelist_folder.name

    # TODO: replace with actual default whitelist
    defaul_wl = Path(whitelist_folder.name + "/default_whitelist")
    defaul_wl.touch()

    with open(defaul_wl, "w") as f:
        f.write("YaLafi_tex2txt\n")

    app.run()

    # deleting temporary directories and their contents upon context exit


@app.route("/")
def index():
    return env.get_template("flask_index.html").render(
        whitelist_ids=get_available_whitelist_ids(),
    )


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


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_buddy(file_path: Path, output_dir: Path):

    if not output_dir.exists():
        output_dir.mkdir()

    # assume request.method == "POST"

    language = request.form["language"] if "language" in request.form else None
    module_selector_mode = (
        request.form["module_selector_type"]
        if "module_selector_type" in request.form
        else None
    )
    module_selection = (
        request.form["module_selector"] if "module_selector" in request.form else None
    )
    whitelist_id = (
        request.form["whitelist_id"] if "whitelist_id" in request.form else None
    )

    LatexBuddy.init(
        FlaskConfigLoader(
            output_dir, language, module_selector_mode, module_selection, whitelist_id
        ),
        ModuleLoader(Path("latexbuddy/modules/")),
        file_path,
        [file_path],
    )

    LatexBuddy.run_tools()

    if whitelist_id and whitelist_id != "[none]":
        LatexBuddy.check_whitelist()

    LatexBuddy.output_file()


def get_available_whitelist_ids() -> List[str]:

    whitelist_path = Path(app.config["WHITELIST_FOLDER"])

    if not whitelist_path.exists() or not whitelist_path.is_dir():
        return []

    wl_ids = []
    for child in whitelist_path.glob("./*"):

        if child.is_dir():
            continue

        wl_ids.append(child.stem)

    return wl_ids


def get_whitelist_path(whitelist_id: str) -> Optional[str]:

    if whitelist_id not in get_available_whitelist_ids():
        return None

    return os.path.join(app.config["WHITELIST_FOLDER"], whitelist_id)
