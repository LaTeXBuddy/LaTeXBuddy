# LaTeXBuddy - a LaTeX checking tool
# Copyright (C) 2021-2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import datetime
import hashlib
import logging
import os
import re
import tempfile
import typing
import zipfile
from pathlib import Path
from pathlib import PurePath

import flask
from flask import abort
from flask import Flask
from flask import redirect
from flask import request
from flask import send_from_directory
from jinja2 import Environment
from jinja2 import PackageLoader
from werkzeug.utils import secure_filename

from latexbuddy import __name__ as name
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleLoader

if typing.TYPE_CHECKING:
    from werkzeug.datastructures import FileStorage
    from werkzeug.wrappers.response import Response


app = Flask(name)
env = Environment(loader=PackageLoader("latexbuddy"))
LOG = logging.getLogger(__name__)

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
    "png",
    "gif",
    "svg",
    "zip",
]


class FlaskConfigLoader(ConfigLoader):
    _REGEX_LANGUAGE_FLAG = re.compile(
        r"([a-zA-Z]{2,3})(?:[-_\s]([a-zA-Z]{2,3}))?",
    )

    def __init__(
        self,
        output_dir: Path,
        language: str | None,
        module_selector_mode: str | None,
        module_selection: str | None,
        whitelist_id: str | None,
    ):
        super().__init__()

        self.main_flags = {
            "output": str(output_dir),
            "format": "HTML_FLASK",
            "enable-modules-by-default": True,
            "module_dir": "latexbuddy/modules/",
        }

        self.module_flags = {}

        if language:
            match = self._REGEX_LANGUAGE_FLAG.fullmatch(language)

            if match:
                self.main_flags["language"] = match.group(1)

                if match.group(2):
                    self.main_flags["language_country"] = match.group(2)

        if module_selector_mode \
                and module_selector_mode in ["blacklist", "whitelist"]:
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


def _get_filename(file: FileStorage) -> str:
    if file.filename is None:
        return hashlib.blake2b(
            file.stream.read(1024),
            digest_size=8,
        ).hexdigest()

    return file.filename


def run_server() -> None:
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
def index() -> str:
    return env.get_template("flask_index.html").render(
        whitelist_ids=get_available_whitelist_ids(),
    )


@app.route("/check", methods=["GET", "POST"])
def document_check() -> Response:
    if request.method != "POST":
        return redirect("/")

    files = request.files.getlist("file")

    if len(files) < 1:
        return redirect("/")

    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_id = f"{date}_{_get_filename(files[0]).replace('.', '_')}"
    result_path = os.path.join(app.config["RESULTS_FOLDER"], result_id)

    saved_tex_files = []

    for file in files:
        file_name = _get_filename(file)

        if not allowed_file(file_name):
            continue

        filename = secure_filename(file_name)
        target_dir_path = os.path.join(app.config["UPLOAD_FOLDER"], result_id)
        Path(target_dir_path).mkdir()

        target_file_path = os.path.join(target_dir_path, filename)
        file.save(target_file_path)

        if zipfile.is_zipfile(target_file_path):
            with zipfile.ZipFile(target_file_path) as archive:
                archive.extractall(target_dir_path)

        tex_files = list(Path(target_dir_path).rglob("*.tex"))
        saved_tex_files.extend(tex_files)

    for tex_file in saved_tex_files:
        # TODO: compile PDF only in main document
        run_buddy(tex_file, Path(result_path), saved_tex_files)

    return redirect(f"/result/{result_id}")


@app.route("/result/<result_id>")
def check_result(result_id: str) -> Response:
    result_path = Path(
        os.path.join(app.config["RESULTS_FOLDER"], secure_filename(result_id)),
    )

    if not result_path.exists():
        abort(404)

    files = list(result_path.rglob("*.html"))

    if len(files) < 1:
        abort(404)

    return redirect(f"/result/{result_id}/{secure_filename(files[0].name)}")


@app.route("/result/<result_id>/<file_name>")
def display_result(
    result_id: str,
    file_name: str,
) -> Response:
    result_path = Path(
        os.path.join(app.config["RESULTS_FOLDER"], secure_filename(result_id)),
    )

    if not result_path.exists():
        abort(404)

    file_path = Path(
        os.path.join(
            str(result_path), secure_filename(file_name),
        ),
    )

    with open(file_path) as f:
        return flask.Response(f.read())


@app.route("/result/<result_id_0>/compiled/<result_id_1>/<pdf_name>")
def compiled_pdf(
    result_id_0: str,
    result_id_1: str,
    pdf_name: str,
) -> Response:
    result_id = result_id_0
    if result_id_0 != result_id_1:
        abort(404)

    pdf_dir = os.path.join(
        app.config["RESULTS_FOLDER"],
        result_id,
        "compiled",
        result_id,
    )

    if not Path(pdf_dir + "/" + pdf_name).exists():
        abort(404)

    return send_from_directory(pdf_dir, pdf_name)


@app.route("/whitelist-api/upload", methods=["GET", "POST"])
def upload_whitelist() -> Response:
    if request.method != "POST":
        return redirect("/")

    files = request.files.getlist("whitelist-file")

    if len(files) < 1:
        return redirect("/")

    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    for wl_file in files:
        file_name = _get_filename(wl_file)

        if not allowed_whitelist_file(file_name):
            continue

        file_name = f"{date}_{secure_filename(file_name)}"
        target_path = os.path.join(app.config["WHITELIST_FOLDER"], file_name)

        wl_file.save(target_path)

    return redirect("/")


def allowed_file(filename: str) -> bool:
    return PurePath(filename).suffix.lower() in ALLOWED_EXTENSIONS


def allowed_whitelist_file(filename: str) -> bool:
    return len(PurePath(filename).suffixes) == 0


def run_buddy(
    file_path: Path,
    output_dir: Path,
    path_list: list[Path],
) -> None:
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
        request.form["module_selector"]
        if "module_selector" in request.form
        else None
    )
    whitelist_id = (
        request.form["whitelist_id"]
        if "whitelist_id" in request.form
        else None
    )

    config_loader = FlaskConfigLoader(
        output_dir,
        language,
        module_selector_mode,
        module_selection,
        whitelist_id,
    )

    LatexBuddy.init(
        config_loader,
        ModuleLoader(
            Path(
                config_loader.get_config_option_or_default(
                    LatexBuddy,
                    "module_dir",
                    "modules/",
                ),
            ),
        ),
        file_path,
        path_list,
        # TODO: change this to only compile the first/main file
        compile_tex=True,
    )

    LatexBuddy.run_tools()

    if whitelist_id and whitelist_id != "[none]":
        LatexBuddy.check_whitelist()

    LatexBuddy.output_file()


def get_available_whitelist_ids() -> list[str]:
    whitelist_path = Path(app.config["WHITELIST_FOLDER"])

    if not whitelist_path.exists() or not whitelist_path.is_dir():
        return []

    wl_ids = []
    for child in whitelist_path.glob("./*"):

        if child.is_dir():
            continue

        wl_ids.append(child.stem)

    return wl_ids


def get_whitelist_path(whitelist_id: str) -> str | None:
    if whitelist_id not in get_available_whitelist_ids():
        return None

    return os.path.join(app.config["WHITELIST_FOLDER"], whitelist_id)


if __name__ == "__main__":
    run_server()
