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
"""This module defines new TexFile class used to abstract files LaTeXBuddy is
working with."""
from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path
from tempfile import mkstemp
from typing import Any

from chardet import detect
from yalafi.tex2txt import Options  # type: ignore
from yalafi.tex2txt import tex2txt
from yalafi.tex2txt import translate_numbers

from latexbuddy.messages import not_found
from latexbuddy.tools import absolute_to_linecol
from latexbuddy.tools import find_executable
from latexbuddy.tools import get_line_offsets
from latexbuddy.tools import is_binary

# regex to parse out error location from tex2txt output
location_re = re.compile(r"line (\d+), column (\d+)")

LOG = logging.getLogger(__name__)


def _create_texmf(config: dict[str, Any]) -> tuple[Path, str]:
    from tempfile import mkdtemp
    contents = "\n".join(f"{k}={str(v)}" for k, v in config.items())

    file = Path(mkdtemp(None, "latexbuddy-")) / "texmf.cnf"
    file.write_text(contents)
    return file, f"{str(file.absolute())}:"


class TexFile:
    """A simple TeX file.

    This class reads the file, detects its encoding and saves it as text
    for future editing.
    """

    def __init__(self, file: Path, *, compile_tex: bool):
        """Creates a new file instance.

        :param file: Path object of the file to be loaded
        :param compile_tex: Bool if the tex should be compiled
        """
        self.tex_file = file

        tex_bytes = self.tex_file.read_bytes()
        if len(tex_bytes) > 0:
            tex_encoding = detect(tex_bytes)["encoding"]
            if tex_encoding is None:
                tex_encoding = "UTF-8"
            self.tex = tex_bytes.decode(encoding=tex_encoding)
        else:
            self.tex = ""

        self.plain, self._charmap, self._parse_problems = self.__detex()

        _, plain_path = mkstemp(suffix=".detexed", prefix=self.tex_file.stem)
        self.plain_file = Path(plain_path)
        self.plain_file.write_text(self.plain)

        self.is_faulty = is_binary(tex_bytes) or len(self._parse_problems) > 0
        compile_pdf = True
        if compile_tex:
            self.log_file, self.pdf_file = self.__compile_tex(
                compile_pdf=compile_pdf,
            )
        else:
            self.log_file, self.pdf_file = (None, None)

    def __detex(self) -> tuple[
        str, list[int],
        list[tuple[tuple[int, int] | None, str]],
    ]:
        opts = Options()  # use default options

        detex_stderr = StringIO()
        sys.stderr = detex_stderr  # temporary redirect stderr

        plain: str
        charmap: list[int]
        plain, charmap = tex2txt(self.tex, opts)

        sys.stderr = sys.__stderr__  # restore original stderr
        out = detex_stderr.getvalue()  # tex2txt error output
        detex_stderr.close()

        # parse tex2txt errors
        out_split = out.split("*** LaTeX error: ")
        err = []

        # first "error" is a part of tex2txt output
        # TODO: make a big regex?
        for yalafi_error in out_split[1:]:
            location_str, _, reason = yalafi_error.partition("***")

            location_match = location_re.match(location_str)
            if location_match:
                location = (
                    int(location_match.group(1)),
                    int(location_match.group(2)),
                )
            else:
                location = None

            err.append((location, reason.strip()))

        return plain, charmap, err

    def get_position_in_tex(self, char_pos: int) -> tuple[int, int] | None:
        """Gets position of a character in the original file.

        :param char_pos: absolute char position
        :return: line and column number of the respective char in the
            tex file
        """
        line, col, offsets = absolute_to_linecol(self.plain, char_pos)

        aux = translate_numbers(
            self.tex, self.plain,
            self._charmap, offsets, line, col,
        )

        if aux is None:
            return None

        return aux.lin, aux.col

    def get_position_in_tex_from_linecol(
        self,
        line: int,
        col: int,
    ) -> tuple[int, int]:
        offsets = get_line_offsets(self.plain)
        aux = translate_numbers(
            self.tex,
            self.plain,
            self._charmap,
            offsets,
            line,
            col,
        )

        if aux is None:
            _msg = f"Can't translate position {line}:{col}."
            raise ValueError

        return aux.lin, aux.col

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TexFile):
            return False

        return self.tex_file == other.tex_file

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"file={str(self.tex_file.resolve())})"
        )

    def __str__(self) -> str:
        return str(self.tex_file)

    def __compile_tex(
        self,
        *,
        compile_pdf: bool,
    ) -> tuple[Path | None, Path | None]:
        from latexbuddy.buddy import get_instance

        buddy = get_instance()

        compiler = "latex"
        try:
            find_executable("latex")
        except FileNotFoundError:
            LOG.error(
                not_found("pdflatex", "LaTeX (e.g., TeXLive Core)"),
            )
            return None, None

        if compile_pdf:
            compiler = "pdflatex"

        html_directory = buddy.cfg.get_config_option_or_default(
            buddy.__class__,
            "output",
            "./latexbuddy_html/",
        )
        html_path = Path(html_directory)

        results_dir = html_path / "compiled" / str(self.tex_file.parent.name)
        results_dir.mkdir(parents=True, exist_ok=True)

        _, texmfcnf = _create_texmf(
            {
                "max_print_line": "1000",
                "error_line": "254",
                "half_error_line": "238",
            },
        )

        LOG.debug(
            f"TEXFILE: {str(self.tex_file)},"
            f"exists: {self.tex_file.exists()}",
        )
        LOG.debug(
            f"PATH: {str(results_dir)}, "
            f"exists: {results_dir.exists()}",
        )

        subprocess.check_call(
            (
                compiler,
                "-interaction", "nonstopmode",
                "-output-directory", results_dir,
                "-8bit",
                self.tex_file.name,
            ),
            cwd=str(self.tex_file.parent),
            env={
                **os.environ,
                "TEXMFCNF": texmfcnf,
            },
        )

        log = results_dir / f"{self.tex_file.stem}.log"
        LOG.debug(f"LOG: {str(log)}, isFile: {log.is_file()}")

        pdf = None
        if compile_pdf:
            pdf = results_dir / f"{self.tex_file.stem}.pdf"
            LOG.debug(f"PDF: {str(pdf)}, isFile: {pdf.is_file()}")
        return log, pdf
