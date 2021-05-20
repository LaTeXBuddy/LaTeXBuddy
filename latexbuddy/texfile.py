"""This module defines new TexFile class used to abstract files LaTeXBuddy is working
with."""
import re
import sys

from io import StringIO
from pathlib import Path
from tempfile import mkstemp
from typing import Optional, Tuple

from chardet import detect
from yalafi.tex2txt import Options, tex2txt, translate_numbers

from latexbuddy.tools import absolute_to_linecol, is_binary


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
        self.tex = tex_bytes.decode(encoding=tex_encoding)

        self.plain, self._charmap, self._parse_problems = self.__detex()

        _, plain_path = mkstemp(suffix=".detexed", prefix=self.tex_file.stem)
        self.plain_file = Path(plain_path)
        self.plain_file.write_text(self.plain)

        self.is_faulty = is_binary(tex_bytes) or len(self._parse_problems) > 0

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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TexFile):
            return False

        return self.tex_file == other.tex_file

    def __repr__(self) -> str:
        return f"{self.__name__}(file={str(self.tex_file.resolve())})"

    def __str__(self) -> str:
        return str(self.tex_file)
