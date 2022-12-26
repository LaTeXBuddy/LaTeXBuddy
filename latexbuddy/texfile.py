"""This module defines new TexFile class used to abstract files LaTeXBuddy is
working with."""
from __future__ import annotations

import logging
import os
import re
import sys
from io import StringIO
from pathlib import Path
from tempfile import mkstemp

from chardet import detect
from yalafi.tex2txt import Options
from yalafi.tex2txt import tex2txt
from yalafi.tex2txt import translate_numbers

from latexbuddy.messages import not_found
from latexbuddy.messages import texfile_error
from latexbuddy.tools import absolute_to_linecol
from latexbuddy.tools import execute
from latexbuddy.tools import find_executable
from latexbuddy.tools import get_line_offsets
from latexbuddy.tools import is_binary


# regex to parse out error location from tex2txt output
location_re = re.compile(r"line (\d+), column (\d+)")

LOG = logging.getLogger(__name__)


class TexFile:
    """A simple TeX file.

    This class reads the file, detects its encoding and saves it as text
    for future editing.
    """

    def __init__(self, file: Path, compile_tex: bool):
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
        # compile_pdf = cfg.get_config_option_or_default(
        #     "buddy", "pdf", True, verify_type=bool
        # )
        compile_pdf = True
        if compile_tex:
            self.log_file, self.pdf_file = self.__compile_tex(compile_pdf)
        else:
            self.log_file, self.pdf_file = (None, None)

    def __detex(self):
        opts = Options()  # use default options

        detex_stderr = StringIO()
        sys.stderr = detex_stderr  # temporary redirect stderr

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
        :return: line and column number of the respective char in the tex file
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
    ) -> tuple[int, int] | None:
        offsets = get_line_offsets(self.plain)
        aux = translate_numbers(
            self.tex, self.plain,
            self._charmap, offsets, line, col,
        )

        if aux is None:
            return None

        return aux.lin, aux.col

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TexFile):
            return False

        return self.tex_file == other.tex_file

    def __repr__(self) -> str:
        return f"{self.__name__}(file={str(self.tex_file.resolve())})"

    def __str__(self) -> str:
        return str(self.tex_file)

    def __compile_tex(
        self,
        compile_pdf: bool,
    ) -> tuple[Path | None, Path | None]:
        from latexbuddy.buddy import LatexBuddy

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

        html_directory = LatexBuddy.instance.cfg.get_config_option_or_default(
            LatexBuddy,
            "output",
            os.getcwd() + "/latexbuddy_html/",
        )

        try:
            os.mkdir(html_directory)
        except FileExistsError:
            LOG.debug(f"Directory {html_directory} already exists.")
        except Exception as exc:
            LOG.error(
                texfile_error(
                    f"{exc} occurred while creating {html_directory}.",
                ),
            )

        compile_directory = html_directory + "/compiled"

        try:
            os.mkdir(compile_directory)
        except FileExistsError:
            LOG.debug(f"Directory {compile_directory} already exists.")
        except Exception as exc:
            LOG.error(
                texfile_error(
                    f"{exc} occurred while creating {compile_directory}.",
                ),
            )

        compilation_path = Path(
            compile_directory + "/" + str(self.tex_file.parent.name),
        )

        try:
            os.mkdir(str(compilation_path))
        except FileExistsError:
            LOG.debug(
                f"Directory {str(compilation_path)} already exists.",
            )
        except Exception as exc:
            LOG.error(
                texfile_error(
                    f"{exc} occurred while creating {str(compilation_path)}.",
                ),
            )

        tex_mf = self.__create_tex_mf(compilation_path)

        LOG.debug(
            f"TEXFILE: {str(self.tex_file)}, exists: {self.tex_file.exists()}",
        )
        LOG.debug(
            f"PATH: {str(compilation_path)}, "
            f"exists: {compilation_path.exists()}",
        )

        print(self.tex_file.name)
        print(self.tex_file.parent)
        execute(
            f'TEXMFCNF="{tex_mf}";',
            "cd",
            f"{str(self.tex_file.parent)};",
            compiler,
            "-interaction=nonstopmode",
            f"-output-directory='{str(compilation_path)}'",
            "-8bit",
            str(self.tex_file.name),
        )

        log = compilation_path / f"{self.tex_file.stem}.log"
        pdf = compilation_path / \
            f"{self.tex_file.stem}.pdf" if compile_pdf else None
        LOG.debug(f"LOG: {str(log)}, isFile: {log.is_file()}")
        LOG.debug(f"PDF: {str(pdf)}, isFile: {pdf.is_file()}")
        return log, pdf

    @staticmethod
    def __create_tex_mf(path: Path) -> str:
        """This method makes the log file be written correctly."""
        # https://tex.stackexchange.com/questions/52988/avoid-linebreaks-in-latex-console-log-output-or-increase-columns-in-terminal
        # https://tex.stackexchange.com/questions/410592/texlive-personal-texmf-cnf
        text = "\n".join(
            ["max_print_line=1000", "error_line=254", "half_error_line=238"],
        )
        cnf_path = path / "texmf.cnf"
        Path(cnf_path).resolve().write_text(text)
        return str(cnf_path.parent) + ":"
