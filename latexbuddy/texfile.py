"""This module defines new TexFile class used to abstract files LaTeXBuddy is working
with."""
import os
import re
import sys

from io import StringIO
from pathlib import Path
from tempfile import mkstemp, mkdtemp
from typing import Optional, Tuple
from chardet import detect
from yalafi.tex2txt import Options, tex2txt, translate_numbers
from latexbuddy.messages import not_found, texfile_error
from latexbuddy.tools import absolute_to_linecol, get_line_offsets, is_binary, \
    find_executable, execute

# regex to parse out error location from tex2txt output
location_re = re.compile(r"line (\d+), column (\d+)")


class TexFile:
    """A simple TeX file. This class reads the file, detects its encoding and saves it
    as text for future editing."""

    def __init__(self, file: Path):
        """Creates a new file instance.

        By default, the file is being read, but not detexed. The file can be detexed at
        any point using `detex()` method.

        :param file: Path object of the file to be loaded
        """

        self.tex_file = file

        tex_bytes = self.tex_file.read_bytes()
        tex_encoding = detect(tex_bytes)["encoding"]
        if tex_encoding is None:
            tex_encoding = "UTF-8"
        self.tex = tex_bytes.decode(encoding=tex_encoding)

        self.plain, self._charmap, self._parse_problems = self.__detex()

        _, plain_path = mkstemp(suffix=".detexed", prefix=self.tex_file.stem)
        self.plain_file = Path(plain_path)
        self.plain_file.write_text(self.plain)

        self.is_faulty = is_binary(tex_bytes) or len(self._parse_problems) > 0
        compile_pdf = True
        self.log_file, self.pdf_file = self.__compile_tex(compile_pdf)

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
                location = (int(location_match.group(1)), int(location_match.group(2)))
            else:
                location = None

            err.append((location, reason.strip()))

        return plain, charmap, err

    def get_position_in_tex(self, char_pos: int) -> Optional[Tuple[int, int]]:
        """Gets position of a character in the original file.

        :param char_pos: absolute char position
        :return: line and column number of the respective char in the tex file
        """
        line, col, offsets = absolute_to_linecol(self.plain, char_pos)

        aux = translate_numbers(self.tex, self.plain, self._charmap, offsets, line, col)

        if aux is None:
            return None

        return aux.lin, aux.col

    def get_position_in_tex_from_linecol(
        self, line: int, col: int
    ) -> Optional[Tuple[int, int]]:
        offsets = get_line_offsets(self.plain)
        aux = translate_numbers(self.tex, self.plain, self._charmap, offsets, line, col)

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

    def __compile_tex(self, compile_pdf: bool) -> Tuple[Path, Path]:
        compiler = 'latex'
        if compile_pdf:
            try:
                find_executable("pdflatex")
            except FileNotFoundError:
                self.__logger.error(not_found("pdflatex", "LaTeX (e.g., TeXLive Core)"))
            compiler = "pdflatex"
        else:
            try:
                find_executable('latex')
            except FileNotFoundError:
                self.__logger.error(not_found('latex', 'LaTeX (e.g., TeXLive Core)'))

        tex_mf = self.__create_tex_mf()
        html_directory = os.getcwd() + "/latexbuddy_html"
        try:
            os.mkdir(html_directory)
        except FileExistsError:
            pass # TODO
        except Exception as exc:
            pass # TODO
        compile_directory = html_directory + "/compiled"
        try:
            os.mkdir(compile_directory)
        except FileExistsError:
            pass # TODO
        except Exception as exc:
            pass # TODO

        # for unique file names
        path = Path(
            mkdtemp(suffix='comiled_tex', prefix='latexbuddy', dir=compile_directory)
        )
        # path = Path(compile_directory)
        execute(
            f'TEXMFCNF="{tex_mf}";',
            compiler,
            "-interaction=nonstopmode",
            "-8bit",
            f"-output-directory={str(path)}",
            str(self.tex_file),
        )

        path = Path(compile_directory).resolve()
        log = path / f"{self.tex_file.stem}.log"
        pdf = path / f"{self.tex_file.stem}.pdf" if compile_pdf else None
        return log, pdf

    @staticmethod
    def __create_tex_mf() -> str:
        """
        This method makes the log file be written correctly
        """
        # https://tex.stackexchange.com/questions/52988/avoid-linebreaks-in-latex-console-log-output-or-increase-columns-in-terminal
        # https://tex.stackexchange.com/questions/410592/texlive-personal-texmf-cnf
        text = "\n".join(
            ["max_print_line=1000", "error_line=254", "half_error_line=238"])
        descriptor, cnf_path = mkstemp(prefix="latexbuddy", suffix="cnf")
        Path(cnf_path).resolve().write_text(text)
        return str(cnf_path)
