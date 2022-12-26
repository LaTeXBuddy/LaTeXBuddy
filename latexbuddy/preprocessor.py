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

import logging
import re
from abc import ABC
from abc import abstractmethod
from typing import Callable

from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile

LOG = logging.getLogger(__name__)


class ProblemFilter(ABC):
    """Describes the base class for any problem filter.

    ``ProblemFilter`` provides functionality to define a start and
    end line and to match a :class:`~latexbuddy.problem.Problem` based
    on its line position.

    ``ProblemFilter`` objects can be made "open-ended" by omitting the
    ``end_line`` parameter. This results in a filter matching any
    problem located at or below the ``start_line``. Open-ended filters
    can later be closed by supplying the ``end_line`` via the
    :meth:`.end` method.

    For more diverse filters, ProblemFilter provides the following
    abstract methods which must be implemented by all subclasses:
    :meth:`.custom_match` and :meth:`.custom_parameters_equal`.

    :param start_line: beginning of the filter's area
    :param end_line: end of the filter's area (open-ended, if omitted)
    """

    def __init__(self, start_line: int, end_line: int | None = None):
        self.start_line = start_line
        self.end_line = end_line

    def end(self, end_line: int) -> bool:
        """Sets the end line of ProblemFilter, if not already done.

        :param end_line: line number of the filter's end
        :return: ``True`` if ``end_line`` was set before;
                 ``False`` otherwise
        """
        if self.end_line is None:
            self.end_line = end_line
            return True

        return False

    def __match_line(self, problem: Problem) -> bool:
        """Determines, whether a given problem is located within the
        ProblemFilter's line boundaries.

        :param problem: Problem object to examine
        :return: True, if the problem is located in the area covered by the
                 ProblemFilter, False otherwise
        """

        if problem.position is None:
            return True

        if self.end_line is None:
            return self.start_line <= problem.position[0]

        return self.start_line <= problem.position[0] <= self.end_line

    def match(self, problem: Problem) -> bool:
        """Matches custom filter's requirements against a problem.

        This method etermines, whether a given `problem is located
        within the filter's line boundaries and matches all custom
        requirements that the subclass implementation imposes.

        :param problem: Problem object to examine
        :return: ``True``, if the problem is located in the area
                 covered by the ProblemFilter and matches all custom
                 requirements, ``False`` otherwise
        """

        return self.__match_line(problem) and self.custom_match(problem)

    @abstractmethod
    def custom_match(self, problem: Problem) -> bool:
        """Matches a given Problem object based on custom parameters of the
        subclass implementation.

        :param problem: Problem object to be examined
        :return: ``True``, if the problem matches all custom
                 requirements, ``False`` otherwise
        """

    @abstractmethod
    def custom_parameters_equal(self, other: ProblemFilter) -> bool:
        """Determines, if two custom ``ProblemFilter`` objects are equal.

        Two objects of type :class:`~.ProblemFilter` are considered
        equal as long as they are:

        * of the same type
        * equal in terms of their custom parameters

        .. caution::
           This method does not check the equality of `start_line``
           and ``end_line``!

        :param other: second custom ProblemFilter to be compared with
                      the current one
        :return: ``True``, if the other custom ProblemFilter is equal
                 to the current one, ``False`` otherwise
        """


class LineProblemFilter(ProblemFilter):
    """ProblemFilter implementation that only considers a problem's line
    position."""

    def __init__(self, start_line: int, end_line: int | None = None):
        """Initializes a new LineProblemFilter with no custom parameters.

        :param start_line: beginning of the filter's area
        :param end_line: end of the filter's area
        """

        super().__init__(start_line, end_line)

    def custom_match(self, problem: Problem) -> bool:
        return True

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:
        return isinstance(other, LineProblemFilter)


class ModuleProblemFilter(ProblemFilter):
    """ProblemFilter implementation that filters problems, if they have been
    created by a specified LaTeXBuddy module."""

    def __init__(
        self,
        module_name: str,
        start_line: int,
        end_line: int | None = None,
    ):
        """Initializes a new ModuleProblemFilter with a string representation
        of a module name as its custom parameter.

        :param module_name: name of the module which created a problem object
        :param start_line: beginning of the filter's area
        :param end_line: end of the filter's area
        """

        super().__init__(start_line, end_line)
        self.module_name = module_name

    def custom_match(self, problem: Problem) -> bool:
        return problem.checker == self.module_name

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:
        return isinstance(other, ModuleProblemFilter) \
            and other.module_name == self.module_name


class SeverityProblemFilter(ProblemFilter):
    """ProblemFilter implementation that filters problems, if they have been
    created with a specified ProblemSeverity."""

    def __init__(
        self,
        severity: ProblemSeverity,
        start_line: int,
        end_line: int | None = None,
    ):
        """Initializes a new SeverityProblemFilter with a string representation
        of a ProblemSeverity level as its custom parameter.

        :param severity: ProblemSeverity level of a problem
        :param start_line: beginning of the filter's area
        :param end_line: end of the filter's area
        """

        super().__init__(start_line, end_line)
        self.severity = severity

    def custom_match(self, problem: Problem) -> bool:
        return problem.severity == self.severity

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:
        return isinstance(other, SeverityProblemFilter) \
            and other.severity == self.severity


class WhitelistKeyProblemFilter(ProblemFilter):
    """This filter excludes problems, if they have been created with a
    specified whitelist key.

    :param wl_key: whitelist key of a problem
    :param start_line: beginning of the filter's area
    :param end_line: end of the filter's area
    """

    def __init__(
        self,
        wl_key: str,
        start_line: int,
        end_line: int | None = None,
    ):
        super().__init__(start_line, end_line)
        self.wl_key = wl_key

    def custom_match(self, problem: Problem) -> bool:
        return problem.key == self.wl_key

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:
        return isinstance(other, WhitelistKeyProblemFilter) \
            and other.wl_key == self.wl_key


class Preprocessor:
    """This class represents the LaTeXBuddy in-file preprocessor.

    the Preprocessor is capable of parsing buddy commands disguised as
    LaTeX comments from a TexFile object using regexes and is able to
    filter any given Problem or list of Problems accordingly.
    """

    __RE_COMMAND = re.compile(
        r"%\s?buddy (ignore-next|begin-ignore|end-ignore)( (\S+))*",
    )

    __RE_IGNORE_NEXT_ONE_LINE = re.compile(
        r"%\s?buddy ignore-next(?:(?: 1)? line)?",
    )
    __RE_IGNORE_NEXT_N_LINES = re.compile(
        r"%\s?buddy ignore-next (\d+) lines",
    )

    __RE_BEGIN_IGNORE_ANYTHING = re.compile(
        r"%\s?buddy begin-ignore",
    )
    __RE_BEGIN_IGNORE_MODULES = re.compile(
        r"%\s?buddy begin-ignore (modules?)((?: \S+)+)",
    )
    __RE_BEGIN_IGNORE_SEVERITIES = re.compile(
        r"%\s?buddy begin-ignore (?:severity|severities)((?: \S+)+)",
    )
    __RE_BEGIN_IGNORE_WL_KEYS = re.compile(
        r"%\s?buddy begin-ignore (whitelist-keys?)((?: \S+)+)",
    )

    __RE_END_IGNORE_ANYTHING = re.compile(r"%\s?buddy end-ignore")
    __RE_END_IGNORE_MODULES = re.compile(
        r"%\s?buddy end-ignore (modules?)((?: \S+)+)",
    )
    __RE_END_IGNORE_SEVERITIES = re.compile(
        r"%\s?buddy end-ignore (?:severity|severities)((?: \S+)+)",
    )
    __RE_END_IGNORE_WL_KEYS = re.compile(
        r"%\s?buddy end-ignore (whitelist-keys?)((?: \S+)+)",
    )

    def __init__(self) -> None:
        """Initializes a new Preprocessor instance with an empty list of
        filters."""

        self.filters: list[ProblemFilter] = []

    def regex_parse_preprocessor_comments(self, file: TexFile) -> None:
        """Parses preprocessor statements in a TeX file.

        This method takes a :class:`~latexbuddy.texfile.TexFile`
        object and parses all preprocessor statements contained in it.
        This results in a set of of :class:`~.ProblemFilter` objects,
        which are then added to this instance's list of filters and
        later applied to the problems.

        :param file: TeX file object containing the LaTeX source code
                     to be parsed
        """

        line_num = 0  # lines are 1-based
        for line in file.tex.splitlines():

            line_num += 1  # lines are 1-based

            if not Preprocessor.__RE_COMMAND.fullmatch(line):
                continue

            resulting_filters = self.__regex_parse_cmd_args_to_filter(
                line, line_num,
            )

            for resulting_filter in resulting_filters:
                self.filters.append(resulting_filter)

    def __regex_parse_cmd_args_to_filter(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter]:
        """Parses a preprocessor statement into filters.

        :param line: the LaTeX code line which contains the
                     preprocessor command to be parsed
        :param line_num: line number of the LaTeX code line to be
                         parsed
        :return: a list of zero or more ProblemFilters resulting from
                 the preprocessor command
        """

        matchers: list[Callable[[str, int], list[ProblemFilter] | None]] = [
            self.__regex_match_command_pattern_ignore_next_one_line,
            self.__regex_match_command_pattern_ignore_next_n_lines,
            self.__regex_match_command_pattern_begin_ignore_anything,
            self.__regex_match_command_pattern_begin_ignore_modules,
            self.__regex_match_command_pattern_begin_ignore_severities,
            self.__regex_match_command_pattern_begin_ignore_wl_keys,
            self.__regex_match_command_pattern_end_ignore_anything,
            self.__regex_match_command_pattern_end_ignore_modules,
            self.__regex_match_command_pattern_end_ignore_severities,
            self.__regex_match_command_pattern_end_ignore_wl_keys,
        ]

        for matcher in matchers:

            match = matcher(line, line_num)
            if match is not None:
                return match

        LOG.warning(
            f"Invalid Syntax: Could not parse preprocessing command "
            f"in line {line_num}: \n{line}",
        )
        return []

    def __regex_match_command_pattern_ignore_next_one_line(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Checks, if the provided command matches the regex pattern and
        creates LineProblemFilters beginning and ending at line_num + 1.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: LineProblemFilter as a list, None if regex not matching
        """

        match = Preprocessor.__RE_IGNORE_NEXT_ONE_LINE.fullmatch(line)
        if match is not None:
            LOG.debug(
                f"Created LineProblemFilter "
                f"from line {line_num + 1} to {line_num + 1}",
            )
            return [LineProblemFilter(line_num + 1, line_num + 1)]

        return None

    def __regex_match_command_pattern_ignore_next_n_lines(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Checks, if the provided command matches the regex pattern and
        creates a LineProblemFilter beginning at line_num + 1 and ending at
        line_num + n. The number of lines to ignore (n) is drawn from the
        command.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: LineProblemFilter as a list, None if regex not matching
        """

        match = Preprocessor.__RE_IGNORE_NEXT_N_LINES.fullmatch(line)
        if match is not None:
            n = int(match.group(1))
            LOG.debug(
                f"Created LineProblemFilter "
                f"from line {line_num + 1} to {line_num + n}",
            )
            return [LineProblemFilter(line_num + 1, line_num + n)]

        return None

    def __regex_match_command_pattern_begin_ignore_anything(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Creates a line filter.

        Checks, if the provided command matches the regex pattern and
        creates a ``LineProblemFilter`` beginning at ``line_num + 1``.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: open-ended ``LineProblemFilter`` as a list,
                 ``None`` if regex not matching
        """

        match = Preprocessor.__RE_BEGIN_IGNORE_ANYTHING.fullmatch(line)
        if match is None:
            return None

        open_ended_filter = self.__get_open_ended_filter(
            LineProblemFilter(0),
        )

        if open_ended_filter is None:
            LOG.debug(
                f"Created open-ended LineProblemFilter "
                f"beginning in line {line_num + 1}",
            )
            return [LineProblemFilter(line_num + 1)]

        LOG.info(
            f"Ignored duplicate command 'begin-ignore' "
            f"in line {line_num}",
        )
        return []

    def __regex_match_command_pattern_begin_ignore_modules(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Creates filters with respect to the ignored modules.

        Checks, if the provided command matches the regex pattern and
        creates ModuleProblemFilters corresponding to the provided
        module names beginning at ``line_num + 1``.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: list of open-ended ``ModuleProblemFilter``s to match
                 the provided modules, ``None`` if regex not matching
        """

        match = Preprocessor.__RE_BEGIN_IGNORE_MODULES.fullmatch(line)
        if match is not None:
            modules = match.group(1).strip().split(" ")

            filters: list[ProblemFilter] = []
            for module in modules:

                open_ended_filter = self.__get_open_ended_filter(
                    ModuleProblemFilter(module, 0),
                )

                if open_ended_filter is not None:
                    LOG.info(
                        f"Ignored duplicate command 'begin-ignore' "
                        f"for module '{module}' in line {line_num}",
                    )
                else:
                    LOG.debug(
                        f"Created open-ended ModuleProblemFilter "
                        f"for module '{module}' "
                        f"beginning in line {line_num + 1}",
                    )
                    filters.append(ModuleProblemFilter(module, line_num + 1))

            return filters

        return None

    def __regex_match_command_pattern_begin_ignore_severities(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Checks, if the provided command matches the regex pattern and
        creates SeverityProblemFilters corresponding to the provided severities
        beginning at line_num + 1.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: list of open-ended SeverityProblemFilters
                 to match the provided severities, None if regex not matching
        """

        match = Preprocessor.__RE_BEGIN_IGNORE_SEVERITIES.fullmatch(line)
        if match is not None:
            severities = match.group(1).strip().split(" ")

            filters: list[ProblemFilter] = []
            for severity in severities:

                try:
                    enum_severity = ProblemSeverity[severity.upper()]

                    open_ended_filter = self.__get_open_ended_filter(
                        SeverityProblemFilter(enum_severity, 0),
                    )

                    if open_ended_filter is not None:
                        LOG.info(
                            f"Ignored duplicate command 'begin-ignore' "
                            f"for severity '{severity}' in line {line_num}",
                        )
                    else:
                        LOG.debug(
                            f"Created open-ended ModuleProblemFilter "
                            f"for severity '{str(enum_severity)}' "
                            f"beginning in line {line_num + 1}",
                        )
                        filters.append(
                            SeverityProblemFilter(enum_severity, line_num + 1),
                        )
                except KeyError:
                    LOG.warning(
                        f"Invalid syntax: "
                        f"Unknown ProblemSeverity '{severity}' "
                        f"in line {line_num}",
                    )

            return filters

        return None

    def __regex_match_command_pattern_begin_ignore_wl_keys(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Checks, if the provided command matches the regex pattern and
        creates WhitelistKeyProblemFilters corresponding to the provided
        whitelist keys beginning at line_num + 1.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: list of open-ended WhitelistKeyProblemFilters
                 to match the provided whitelist keys, None if regex
                 not matching
        """

        match = Preprocessor.__RE_BEGIN_IGNORE_WL_KEYS.fullmatch(line)
        if match is not None:
            keys = match.group(1).strip().split(" ")

            filters: list[ProblemFilter] = []
            for key in keys:

                open_ended_filter = self.__get_open_ended_filter(
                    WhitelistKeyProblemFilter(key, 0),
                )

                if open_ended_filter is not None:
                    LOG.info(
                        f"Ignored duplicate command 'begin-ignore' "
                        f"for whitelist-key '{key}' in line {line_num}",
                    )
                else:
                    LOG.debug(
                        f"Created open-ended WhitelistKeyProblemFilter "
                        f"for whitelist-key '{key}' beginning "
                        f"in line {line_num + 1}",
                    )
                    filters.append(
                        WhitelistKeyProblemFilter(key, line_num + 1),
                    )

            return filters

        return None

    def __regex_match_command_pattern_end_ignore_anything(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Checks, if the provided command (line) matches the regex pattern and
        sets the end line for the matching open-ended ProblemFilter.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: empty list, if successful; None otherwise
        """

        match = Preprocessor.__RE_END_IGNORE_ANYTHING.fullmatch(line)
        if match is not None:

            open_ended_filter = self.__get_open_ended_filter(
                LineProblemFilter(0),
            )

            if open_ended_filter is None:
                LOG.info(
                    f"Ignored duplicate command 'end-ignore' "
                    f"in line {line_num}",
                )
            else:
                LOG.debug(
                    f"Ended existing open-ended LineProblemFilter "
                    f"in line {line_num}",
                )
                open_ended_filter.end(line_num)

            return []

        return None

    def __regex_match_command_pattern_end_ignore_modules(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Checks, if the provided command (line) matches the regex pattern and
        sets the end line for the matching open-ended ProblemFilter.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: empty list, if successful; None otherwise
        """

        match = Preprocessor.__RE_END_IGNORE_MODULES.fullmatch(line)
        if match is not None:
            modules = match.group(1).strip().split(" ")

            for module in modules:

                open_ended_filter = self.__get_open_ended_filter(
                    ModuleProblemFilter(module, 0),
                )

                if open_ended_filter is None:
                    LOG.info(
                        f"Ignored duplicate command 'end-ignore' "
                        f"for module '{module}' "
                        f"in line {line_num}",
                    )
                else:
                    LOG.debug(
                        f"Ended existing open-ended ModuleProblemFilter "
                        f"for module '{module}' in line {line_num + 1}",
                    )
                    open_ended_filter.end(line_num)

            return []

        return None

    def __regex_match_command_pattern_end_ignore_severities(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Checks, if the provided command (line) matches the regex pattern and
        sets the end line for the matching open-ended ProblemFilter.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: empty list, if successful; None otherwise
        """

        match = Preprocessor.__RE_END_IGNORE_SEVERITIES.fullmatch(line)
        if match is not None:
            severities = match.group(1).strip().split(" ")

            for severity in severities:

                try:
                    enum_severity = ProblemSeverity[severity.upper()]

                    open_ended_filter = self.__get_open_ended_filter(
                        SeverityProblemFilter(enum_severity, 0),
                    )

                    if open_ended_filter is None:
                        LOG.info(
                            f"Ignored duplicate command 'end-ignore' "
                            f"for severity '{severity}' in line {line_num}",
                        )
                    else:
                        LOG.debug(
                            f"Ended existing open-ended SeverityProblemFilter "
                            f"for severity '{str(enum_severity)}' "
                            f"in line {line_num + 1}",
                        )
                        open_ended_filter.end(line_num)
                except KeyError:
                    LOG.warning(
                        f"Invalid syntax: "
                        f"Unknown ProblemSeverity '{severity}' "
                        f"in line {line_num}",
                    )

            return []

        return None

    def __regex_match_command_pattern_end_ignore_wl_keys(
        self,
        line: str,
        line_num: int,
    ) -> list[ProblemFilter] | None:
        """Checks, if the provided command (line) matches the regex pattern and
        sets the end line for the matching open-ended ProblemFilter.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: empty list, if successful; None otherwise
        """

        match = Preprocessor.__RE_END_IGNORE_WL_KEYS.fullmatch(line)
        if match is not None:
            keys = match.group(1).strip().split(" ")

            for key in keys:

                open_ended_filter = self.__get_open_ended_filter(
                    WhitelistKeyProblemFilter(key, 0),
                )

                if open_ended_filter is None:
                    LOG.info(
                        f"Ignored duplicate command 'end-ignore' "
                        f"for whitelist-key '{key}' in line {line_num}",
                    )
                else:
                    LOG.debug(
                        f"Ended existing open-ended WhitelistKeyProblemFilter "
                        f"for whitelist-key '{key}' in line {line_num + 1}",
                    )
                    open_ended_filter.end(line_num)

            return []

        return None

    def __get_open_ended_filter(
        self,
        reference_filter: ProblemFilter,
    ) -> ProblemFilter | None:
        """Searches for any open-ended (no end set) ProblemFilter matching the
        provided reference ProblemFilter.

        :param reference_filter: reference to find matching open-ended
                                 filter
        :return: matching open-ended filter, if found
        """

        for f in self.filters:
            if f.end_line is not None:
                continue
            if not f.custom_parameters_equal(reference_filter):
                continue
            return f

        return None

    def matches_preprocessor_filter(self, problem: Problem) -> bool:
        """Checks, if the provided Problem matches any filter.

        :param problem: Problem to check
        :return: false if matching; true otherwise
        """
        for f in self.filters:
            if f.match(problem):
                return False
        return True

    def apply_preprocessor_filter(
        self,
        problems: list[Problem],
    ) -> list[Problem]:
        """Applies all parsed ProblemFilters and returns all non- matching
        Problems.

        :param problems: list of Problems to filter
        :return: filtered list of Problems
        """
        return list(filter(self.matches_preprocessor_filter, problems))
