"""This module defines new TexFile class used to abstract files LaTeXBuddy is working
with."""

from pathlib import Path

from chardet import detect

from latexbuddy.tools import is_binary, yalafi_detex


class TexFile:
    """A simple TeX file. This class reads the file, detects its encoding and saves it
    as text for future editing."""

    def __init__(self, file: Path):
        """Creates a new file instance.

        By default, the file is being read, but not detexed. The file can be detexed at
        any point using `detex()` method.

        :param file: Path object of the file to be loaded
        """
        self.path = file

        file_bytes = self.path.read_bytes()
        file_encoding = detect(file_bytes)["encoding"]
        self.source_contents = file_bytes.decode(encoding=file_encoding)

        self.detexed, self.detexed_charmap, self._detex_problems = yalafi_detex(
            self.path
        )

        self.detexed_contents = self.detexed.read_text()

        self.faulty = is_binary(file_bytes[:1024]) or len(self._detex_problems) > 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TexFile):
            return False

        return self.path == other.path

    def __repr__(self) -> str:
        return f"{self.__name__}(file={str(self.path.resolve())})"

    def __str__(self) -> str:
        return str(self.path)
