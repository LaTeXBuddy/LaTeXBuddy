"""This module describes the LaTeXBuddy Error class and its properties."""
from typing import List


class Error:
    """Describes an Error object.

    The Error object contains information about a single error in file. It may be wrong
    LaTeX code or a misspelled word.
    """

    def __init__(
        self,
        buddy,
        path: str,  # TODO: use pathlib.Path
        src: str,
        error_type: str,
        error_id: str,
        text: str,
        start,  # TODO: is this a string? please make this into an int
        length,
        suggestions: List[str],
        warning: bool,  # TODO: make this a string/enum with values error/warning/info
        compare_id,  # TODO: make sure all modules implement this
    ):
        """Creates an error object.

        :param buddy: LaTeXBuddy instance the error will be added to
        :param path: the path to the file
        :param src: the tool that found the error (e.g. chktex, aspell, ...)
        :param error_type: error type: "grammar", "spelling", or "latex"
        :param error_id: tool-specific internal error ID
        :param text: the error as text (e.g., the misspelled word)
        :param start: the absolute position in file of the first symbol of the error
        :param length: the length of the error
        :param suggestions: suggestions that could solve the error
        :param warning: True if the error is a warning, False if it's an error
        :param compare_id: ID to compare semantically equal errors
        """
        self.path = path
        self.src = src
        self.error_type = error_type
        self.error_id = error_id
        self.text = text
        self.start = start
        self.length = length
        self.suggestions = suggestions
        self.warning = warning
        self.compare_id = buddy.get_lang() + "_" + compare_id

        self.uid = self.uid()
        self.cut_suggestions()

        # TODO: remove this; constructors shouldn't produce side effects
        buddy.add_error(self)

    def cut_suggestions(self):
        """Cuts the suggestions list down to the first 10 elements if there are more"""
        if isinstance(self.suggestions, list) & len(self.suggestions) > 10:
            self.suggestions = self.suggestions[:10]

    # TODO: can't we replace this with __str__()?
    def uid(self) -> str:
        """Calculates the UID of the Error object.

        The UID is a unique ID containing all important information about the error.

        :return: the UID of the Error object
        """
        # TODO: use f-strings
        return "{}\0{}\0{}\0{}\0{}\0{}".format(
            self.path, self.src, self.error_type, self.error_id, self.start, self.length
        )

    # TODO: why does this exist? Use the uid() method
    def get_uid(self) -> str:
        """Returns the UID of the Error object.

        The UID is a unique ID containing all important information about the error.

        :return: the UID of the Error object
        """
        return self.uid

    # TODO: why does this exist? Use direct access
    def get_comp_id(self) -> str:
        """Returns the comparing ID of the Error object.

        :return: the comparing ID of the Error object
        """
        return self.compare_id

    # Ignore for now
    # def get_hash(self, language):
    #     string_for_hash = self.dict["error_type"] + self.dict["text"] + language
    #     return hashlib.md5(string_for_hash).hexdigest()

    # TODO: can't we replace this with __eq__()?
    def compare_with_other_comp_id(self, other_comp_id: str) -> bool:
        """Compares this Error to another using the comparing ID.

        :param other_comp_id: comparing ID of the other Error object
        :return: True if two errors are equal, False otherwise
        """
        return self.compare_id == other_comp_id
