"""This module describes the LaTeXBuddy Problem class and its properties.

*Problems* are found by *Checkers*. *Checkers* are free to implement their own
:class:`~latexbuddy.problem.Problem` types, however, LaTeXBuddy will most
surely not display extra metadata.
"""
from __future__ import annotations

import logging
import time
import typing
from enum import Enum
from functools import total_ordering
from json import JSONEncoder
from pathlib import Path

if typing.TYPE_CHECKING:
    from latexbuddy.modules import NamedModule


LOG = logging.getLogger(__name__)

# static variable used for a uniform key generation
language: str | None = None


@total_ordering
class ProblemSeverity(Enum):
    """Defines possible problem severity grades.

    Problem severity is usually preset by the checkers themselves.
    However, a user should be able to redefine the severity of a
    specific problem, using either ``category``, ``key``, or
    ``p_type``.

    * ``"none"`` problems are not being highlighted, but are still
      being output.
    * ``"info"`` problems are highlighted with light blue colour. These
      are suggestions; problems, that aren't criticising the text.
      Example: suggestion to use "lots" instead of "a lot"
    * ``"warning"`` problems are highlighted with orange colour. These
      are warnings about problematic areas in documents. The files
      compile and work as expected, but some behaviour may be
      unacceptable.
      Example: warning about using "$$" in LaTeX
    * ``"error"`` problems are highlighted with red colour. These are
      errors, that prevent the documents to compile correctly.
      Example: not closed environment, or plain wrong LaTeX syntax
    """

    NONE = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

    def __str__(self) -> str:
        return self.name.lower()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProblemSeverity):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ProblemSeverity):
            return NotImplemented
        return self.value < other.value


def set_language(lang: str | None) -> None:
    """Sets the static variable language used for key generation.

    :param lang: global language that the modules currently work with
    """
    # FIXME: don't use global variables
    global language
    language = lang


class Problem:
    """Describes a Problem object.

    A Problem object contains information about a problem detected by a
    checker. For example, it can be wrong LaTeX code or a misspelled
    word.
    """

    def __init__(
        self,
        position: tuple[int, int] | None,
        text: str,
        checker: type[NamedModule] | NamedModule,
        file: Path,
        severity: ProblemSeverity = ProblemSeverity.WARNING,
        p_type: str | None = None,
        length: int | None = None,
        category: str | None = None,
        description: str | None = None,
        context: tuple[str, str] | None = None,
        suggestions: list[str] | None = None,
        key: str | None = None,
    ):
        """Initializes a Problem object.

        :param position: position of the problem in the source file,
                         encoded as ``(line, column)``
        :param length: the length of the problematic text
        :param text: problematic text
        :param checker: type or instance of the tool that discovered
                        the problem
        :param p_type: ID of the problem type, used inside the
                       respective checker
        :param file: **[DEPRECATED]** path to the file where the
                     problem was found
        :param severity: severity of the problem
        :param category: category of the problem, for example "grammar"
        :param description: description of the problem
        :param context: optional context of the problem, that is, text
                        that comes before and after the problematic
                        text
        :param suggestions: list of suggestions, that is, possible
                            replacements for problematic text
        :param key: semi-unique string, which can be used to compare
                    two problems. Will be used for entries in the
                    whitelist
        """
        # TODO: maybe move the defaults to the params, or was there a specific
        #  reason?

        # importing these here to avoid circular import error
        from latexbuddy.buddy import LatexBuddy

        self.position = position

        if length is None:
            length = 0
        self.length = length

        self.text = text

        if (
            checker is None
            or isinstance(checker, LatexBuddy)
            or (isinstance(checker, type) and checker == LatexBuddy)
        ):
            _msg = "Checker module can not be main LatexBuddy instance."
            raise ValueError(_msg)

        self.checker = checker.display_name

        if position is not None and len(text) < 1:
            LOG.warning(
                f"A problem reported by {self.checker} includes position "
                f"data, but does not specify the problematic code. It will be "
                f"displayed as a general problem without a position.",
            )
            self.position = None

        if p_type is None:
            p_type = ""
        self.p_type = p_type

        self.file = file  # FIXME: deprecated!
        self.severity = severity
        self.category = category
        self.description = description

        if context is None:
            context = ("", "")
        self.context = context

        if suggestions is None:
            suggestions = []
        self.suggestions = suggestions

        self.key = self.__generate_key(key)
        self.length = len(text)
        self.uid = self.__generate_uid()

        self.__cut_suggestions(10)

    def __cut_suggestions(self, n: int) -> None:
        """Cuts the suggestions list down to the first n elements if there are
        more.

        :param n: maximum number of suggestions that should be shown
        """
        if len(self.suggestions) > n:
            self.suggestions = self.suggestions[:n]

    def __generate_key(self, key: str | None) -> str:
        """Generates a key for the problem based on language and the given key.

        Major difference for this method is if the module that created
        this problem instance has supplied a key or not.

        :param key: key generated and given by the checker module,
                    ``None`` if not supplied
        :return: final generated key
        """
        if key is None:
            # TODO: maybe remove automatic key generation altogether and
            #  default to `None`
            space = " "
            minus = "-"
            key = f"{self.checker}_" \
                  f"{self.p_type}_" \
                  f"{self.text.replace(space, minus)}"

        # add language to the key if its a spelling or grammar error
        if language is not None and (
            self.category == "grammar" or self.category == "spelling"
        ):
            return f"{language}_{key}"

        return key.replace("\n", "")

    def __generate_uid(self) -> str:
        """Creates the UID for the Problem object.

        :return: a unique UID for the Problem object
        """
        return str(time.time())

    def __get_pos_str(self) -> str:
        """Returns the string value of the problem's position.

        :return: string value of the position
        """
        if self.position is None:
            return "None"

        return f"{self.position[0]}:{self.position[1]}"

    def better_eq(self, key: str) -> bool:
        """equal method based on the key/CompareID."""
        return self.key == key

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Problem):
            return False

        if not self.key or not o.key:
            return False
        return self.key == o.key

    def __ne__(self, o: object) -> bool:
        return not self == o

    def __str__(self) -> str:
        return (
            f"{str(self.category).capitalize()} "
            f"{str(self.severity).lower()} "
            f"on {self.__get_pos_str()}: "
            f"{self.text}: "
            f"{self.description}."
        )


class ProblemJSONEncoder(JSONEncoder):
    """Provides JSON serializability for class Problem."""

    def default(self, obj: typing.Any) -> dict[str, typing.Any]:
        if not isinstance(obj, Problem):
            return JSONEncoder.default(self, obj)

        return {
            "position": obj.position,
            "text": obj.text,
            "checker": obj.checker,
            "p_type": obj.p_type,
            "file": str(obj.file),
            "severity": str(obj.severity),
            "length": obj.length,
            "category": obj.category,
            "description": obj.description,
            "context": obj.context,
            "suggestions": obj.suggestions,
            "key": obj.key,
        }
